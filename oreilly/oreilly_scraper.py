from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import re
from datetime import datetime
import requests
import csv
import argparse
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

@dataclass
class Course:
    publisher: Optional[str] = None
    title: str = ""
    edition: Optional[str] = None
    format: Optional[str] = None
    quiz: bool = False
    release: Optional[str] = None
    duration: Optional[str] = None
    schedule_date: Optional[str] = None
    # split schedule time into start and end (e.g. '7am-11am' -> start_time='7am', end_time='11am')
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    url: str = ""
    authors: List[str] = None
    product_id: Optional[str] = None
    cover: Optional[str] = None
    description: str = ""


def parse_search_html(html: str) -> List[Course]:
    """Parse O'Reilly Learning search HTML and return list of Course objects.

    This parser is built against the sample `oreilly.html` provided.
    It extracts title, link, authors, description, format label, cover image URL and product id.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Each search result is an article with data-testid starting with 'search-card-'
    for article in soup.find_all("article", attrs={"data-testid": True}):
        data_testid = article.get("data-testid", "")
        if not data_testid.startswith("search-card-"):
            continue

        # title and url — find the title container, then its inner anchor
        title_container = article.select_one("[data-testid^=title-link-]")
        title = ""
        url = ""
        if title_container:
            a = title_container.find("a")
            if a:
                title = a.get_text(strip=True)
                url = a.get("href", "")
            else:
                title = title_container.get_text(strip=True)
        else:
            # fallback: any h3 > a
            a = article.select_one("h3 a")
            if a:
                title = a.get_text(strip=True)
                url = a.get("href", "")

        # extract edition from title (e.g., '2nd Edition', 'Second Edition', '(3rd Edition)')
        edition = None
        if title:
            # parenthetical edition like '(3rd Edition)'
            m = re.search(r"\(([^)]*?(?:Edition|Ed\.|Ed)\b[^)]*)\)", title, re.IGNORECASE)
            if m:
                edition = m.group(1).strip()
                title = re.sub(re.escape(m.group(0)), "", title).strip()
            else:
                # ordinal numeric edition e.g. '2nd Edition'
                m2 = re.search(r"\b(\d+(?:st|nd|rd|th)\s+Edition)\b", title, re.IGNORECASE)
                if not m2:
                    # word ordinals e.g. 'Second Edition'
                    m2 = re.search(r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)\s+Edition\b", title, re.IGNORECASE)
                if m2:
                    edition = m2.group(1).strip()
                    title = re.sub(re.escape(m2.group(0)), "", title).strip()
            # clean up trailing separators (commas, dashes, colons, pipes) left after removal
            title = re.sub(r"[\-,:|\u2014\u2013]\s*$", "", title).strip()

        # normalize edition to just the numeric value as a string, e.g. '2' for '2nd Edition' or 'Second Edition'
        def _edition_to_number(ed: Optional[str]) -> Optional[str]:
            if not ed:
                return None
            s = ed.strip()
            # try to find a number
            m = re.search(r"(\d+)", s)
            if m:
                return str(int(m.group(1)))
            # map common word ordinals to numbers
            word_map = {
                "first": "1",
                "second": "2",
                "third": "3",
                "fourth": "4",
                "fifth": "5",
                "sixth": "6",
                "seventh": "7",
                "eighth": "8",
                "ninth": "9",
                "tenth": "10",
                "eleventh": "11",
                "twelfth": "12",
                "thirteenth": "13",
                "fourteenth": "14",
            }
            key = re.sub(r"[^a-z]", "", s.lower())
            return word_map.get(key)

        if edition:
            edition = _edition_to_number(edition)

        # authors - look for data-testid like 'search-card-authors-...'
        authors_container = article.select_one("[data-testid^=search-card-authors-]")
        authors = []
        if authors_container:
            for a in authors_container.find_all("a"):
                text = a.get_text(strip=True)
                if text:
                    authors.append(text)

        # description
        desc = ""
        desc_tag = article.select_one("[data-testid^=search-card-description-] .orm-ff-Description-Description")
        if not desc_tag:
            desc_tag = article.select_one("[data-testid^=search-card-description-]")
        if desc_tag:
            desc = desc_tag.get_text(separator=" ", strip=True)

        # format label
        format_label = None
        format_tag = article.select_one("[data-testid^=search-card-content-level-] [data-testid^=format-label-]")
        if format_tag:
            # text may include 'Format:' in an srOnly span; strip that prefix
            raw = format_tag.get_text(" ", strip=True)
            # remove leading 'Format:' (case-sensitive as seen in sample)
            format_label = re.sub(r"^\s*Format:\s*", "", raw)

        # cover image
        cover = None
        cover_tag = article.select_one("[data-testid^=search-card-cover-image-] img")
        if cover_tag and cover_tag.has_attr("src"):
            cover = cover_tag["src"]

        # product id from data-product-id in add to playlist button
        product_id = None
        add_btn = article.select_one("button[data-product-id]")
        if add_btn and add_btn.has_attr("data-product-id"):
            product_id = add_btn["data-product-id"]

        # schedule: look for upcoming-events list
        schedule_date = None
        # raw schedule time string (e.g. '7am-11am') — we'll split into start/end below
        raw_schedule_time = None
        upcoming = article.select_one("[data-testid^=upcoming-events-]")
        if upcoming:
            # first list item contains something like 'Nov 26 • 7am-11am'
            li = upcoming.find("li")
            if li:
                txt = li.get_text(" ", strip=True)
                # split on bullet/dot '•' if present
                if "•" in txt:
                    parts = [p.strip() for p in txt.split("•", 1)]
                    schedule_date = parts[0]
                    raw_schedule_time = parts[1] if len(parts) > 1 else None
                    # normalize 'Noon' to '12pm' (case-insensitive), e.g. '7am-Noon' -> '7am-12pm'
                    if raw_schedule_time:
                        raw_schedule_time = re.sub(r"\bNoon\b", "12pm", raw_schedule_time, flags=re.IGNORECASE)
                else:
                    # attempt to parse words for month/day/time
                    schedule_date = txt
            else:
                txt = upcoming.get_text(" ", strip=True)

                # skip if the series explicitly has no scheduled events
                if txt.strip() == "There are currently no scheduled events for this series.":
                    # nothing scheduled — leave schedule_date/raw_schedule_time as None
                    pass

        # If schedule_date exists but lacks a year, append a year based on current date
        if schedule_date and not re.search(r"\b\d{4}\b", schedule_date):
            # find month token (full or short)
            mmon = re.search(r"\b(January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|September|Sept|Sep|October|Oct|November|Nov|December|Dec)\b", schedule_date, re.IGNORECASE)
            if mmon:
                mon = mmon.group(1)
                mon_key = mon[:3].lower()
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                }
                month_num = month_map.get(mon_key)
                if month_num:
                    now = datetime.now()
                    cur_month = now.month
                    year = now.year if month_num >= cur_month else now.year + 1
                    schedule_date = schedule_date.strip()
                    schedule_date = f"{schedule_date}, {year}"

        # publisher: look for a link under meta-content that points to /publisher/
        publisher = None
        meta = article.select_one("[data-testid^=search-card-meta-content-]")
        if meta:
            # find link with '/publisher/' in href
            a = meta.find(lambda tag: tag.name == 'a' and tag.has_attr('href') and '/publisher/' in tag['href'])
            if a:
                pub_text = a.get_text(strip=True)
                # normalize known publisher display name
                if pub_text == "O'Reilly Media, Inc.":
                    publisher = "O'Reilly"
                else:
                    publisher = pub_text

        # quiz: presence of an element with data-testid like 'includes-quizzes-<id>'
        quiz = bool(article.select_one("[data-testid^=includes-quizzes-]"))

        # If no upcoming-events entry, try to extract month-year and duration from meta text
        duration = None
        release = None
        if not schedule_date and meta:
            meta_text = meta.get_text(" ", strip=True)
            # month-year, e.g. 'December 2023' or 'July 2024'
            m = re.search(r"\b([A-Z][a-z]+ \d{4})\b", meta_text)
            if m:
                full = m.group(1)
                m2 = re.match(r"([A-Za-z]+) (\d{4})", full)
                if m2:
                    mon_name = m2.group(1)
                    y = m2.group(2)
                    abbr_map = {
                        'january': 'Jan', 'february': 'Feb', 'march': 'Mar', 'april': 'Apr', 'may': 'May', 'june': 'Jun',
                        'july': 'Jul', 'august': 'Aug', 'september': 'Sep', 'october': 'Oct', 'november': 'Nov', 'december': 'Dec'
                    }
                    release = f"{abbr_map.get(mon_name.lower(), mon_name[:3])} {y}"
            # duration like '3h 40m' or '1h' or '45m'
            m2 = re.search(r"\b(\d+h(?:\s*\d+m)?|\d+m)\b", meta_text)
            if m2:
                duration = m2.group(1)

        # If schedule_date contains multiple day numbers (e.g. 'Nov 19 & 20, 2025'),
        # create a separate Course entry for each day and add the day to the title.
        if schedule_date:
            # find 4-digit year if present
            yr_m = re.search(r"\b(\d{4})\b", schedule_date)
            year_str = yr_m.group(1) if yr_m else None
            # collect all 1-2 digit numbers (days) in the schedule_date
            nums = re.findall(r"\b(\d{1,2})\b", schedule_date)
            # filter out the year if it was captured as a number
            day_nums = [int(n) for n in nums if not (year_str and n == year_str)]
            if len(day_nums) > 1:
                # find the month token (e.g., 'Nov' or 'November')
                mmon = re.search(r"\b(January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|September|Sept|Sep|October|Oct|November|Nov|December|Dec)\b", schedule_date, re.IGNORECASE)
                mon = mmon.group(1) if mmon else ""
                for num_day, d in enumerate(day_nums):
                    sd = f"{mon} {d}"
                    if year_str:
                        sd = f"{sd}, {year_str}"
                    title_with_day = f"{title} (Day {num_day+1})" if title else title
                    # split raw_schedule_time into start/end
                    start_time, end_time = _split_time_range(raw_schedule_time) if 'raw_schedule_time' in locals() and raw_schedule_time else (None, None)
                    results.append(Course(title=title_with_day, url=url, authors=authors or [], description=desc, format=format_label, cover=cover, product_id=product_id, schedule_date=sd, start_time=start_time, end_time=end_time, publisher=publisher, quiz=quiz, duration=duration, release=release, edition=edition))
            else:
                # split raw_schedule_time into start/end
                start_time, end_time = _split_time_range(raw_schedule_time) if raw_schedule_time else (None, None)
                results.append(Course(title=title, url=url, authors=authors or [], description=desc, format=format_label, cover=cover, product_id=product_id, schedule_date=schedule_date, start_time=start_time, end_time=end_time, publisher=publisher, quiz=quiz, duration=duration, release=release, edition=edition))
        else:
            # no schedule_date; still attach any parsed start/end times
            start_time, end_time = _split_time_range(raw_schedule_time) if raw_schedule_time else (None, None)
            results.append(Course(title=title, url=url, authors=authors or [], description=desc, format=format_label, cover=cover, product_id=product_id, schedule_date=schedule_date, start_time=start_time, end_time=end_time, publisher=publisher, quiz=quiz, duration=duration, release=release, edition=edition))

    return results


def _split_time_range(s: Optional[str]):
    """Split a time range string into (start, end).

    Accepts formats like '7am-11am', '7:30am - 11:15am', '9am to 12pm'.
    Returns (start, end) where either may be None if missing.
    """
    if not s:
        return (None, None)
    s = s.strip()
    # common separators: hyphen, en-dash, em-dash, 'to'
    parts = re.split(r"\s*(?:-|–|—|−|to)\s*", s, flags=re.IGNORECASE)
    if len(parts) == 1:
        return (parts[0].strip(), None)
    start = parts[0].strip() if parts[0].strip() else None
    end = parts[1].strip() if parts[1].strip() else None
    return (start, end)


def fetch_search(url: str, session: Optional[requests.Session] = None) -> List[Course]:
    """Fetch the search URL and parse results. Returns list of Course objects.

    Note: For heavy scraping or behind-auth pages, provide a logged-in session.
    """
    # Try to use Selenium to fetch the page (renders JavaScript). If Selenium
    # isn't available or fails, fall back to requests.
    try:
        options = Options()
        # run headless for automated runs
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)

            try:
                WebDriverWait(driver, 10).until(lambda drv: drv.find_element(By.CSS_SELECTOR, "div[data-testid^=streamlined-search-cards]"))
            except Exception:
                # if the wait fails, continue and capture what we have
                pass
            html = driver.page_source
            # persist fetched HTML for debugging
            try:
                with open("fetched_search.html", "w", encoding="utf-8") as wf:
                    wf.write(html)
            except Exception:
                pass
        finally:
            try:
                driver.quit()
            except Exception:
                pass

        return parse_search_html(html)
    except Exception:
        # fallback to requests if selenium isn't available or fails
        s = session or requests.Session()
        r = s.get(url)
        r.raise_for_status()
        try:
            if not r.encoding:
                r.encoding = r.apparent_encoding
            content_type = r.headers.get("Content-Type", "")
            if "html" in content_type.lower():
                html_to_save = r.text
            else:
                try:
                    j = r.json()
                    html_to_save = j.get("html") or j.get("content") or r.text
                except ValueError:
                    html_to_save = r.text
            try:
                with open("fetched_search.html", "w", encoding="utf-8") as wf:
                    wf.write(html_to_save)
            except Exception:
                pass
        except Exception:
            pass
        return parse_search_html(r.text)


def courses_to_dicts(courses: List[Course]) -> List[Dict]:
    return [asdict(c) for c in courses]


def dump_courses_csv(courses: List[Course], outfile: Optional[str] = None) -> None:
    """Write courses to CSV. Authors are joined with ", ".

    If outfile is None, prints CSV to stdout.
    """
    fieldnames = [
        "publisher",
        "title",
        "edition",
        "format",
        "quiz",
        "release",
        "duration",
        "schedule_date",
        "start_time",
        "end_time",
        "url",
        "authors",
        # "product_id",
        # "cover",
        # "description",
    ]

    def row_for(c: Course) -> Dict[str, str]:
        return {
            "publisher": c.publisher or "",
            "title": c.title or "",
            "edition": c.edition or "",
            "format": c.format or "",
            "quiz": "yes" if bool(c.quiz) else "",
            "release": c.release or "",
            "duration": c.duration or "",
            "schedule_date": c.schedule_date or "",
            "start_time": c.start_time or "",
            "end_time": c.end_time or "",
            "url": f'=HYPERLINK("{c.url}", "{c.publisher}")' or "",
            "authors": ", ".join(c.authors) if c.authors else "",
            # "product_id": c.product_id or "",
            # "cover": c.cover or "",
            # "description": c.description or "",
        }

    fp = open(outfile, "w", encoding="utf-8", newline="") if outfile else sys.stdout
    try:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for c in courses:
            writer.writerow(row_for(c))
    finally:
        if outfile:
            fp.close()


def dump_courses_json(courses: List[Course], outfile: Optional[str] = None) -> None:
    j = json.dumps([asdict(c) for c in courses], ensure_ascii=False, indent=2)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(j)
    else:
        print(j)


def main(argv=None):
    p = argparse.ArgumentParser(description="Parse O'Reilly Learning search HTML and output results")
    p.add_argument("source", help="Path to local HTML file or a URL starting with http(s)://")
    p.add_argument("--format", choices=["text", "json", "csv"], default="text", help="Output format")
    p.add_argument("--outfile", help="Write output to file (for json format)")
    args = p.parse_args(argv)

    src = args.source
    if src.startswith("http://") or src.startswith("https://"):
        print(f"Fetching and parsing from URL")
        courses = fetch_search(src)
    else:
        with open(src, "r", encoding="utf-8") as f:
            courses = parse_search_html(f.read())

    if args.format == "json":
        dump_courses_json(courses, outfile=args.outfile)
    elif args.format == "csv":
        dump_courses_csv(courses, outfile=args.outfile)
    else:
        for c in courses:
            print(c)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)
