import re
import csv
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import time


def extract_metadata(metadata_text):
    if not metadata_text:
        return "", "", ""
    parts = metadata_text.split(" · ")
    level = parts[0] if len(parts) > 0 else ""
    type_ = parts[1] if len(parts) > 1 else ""
    duration = parts[2] if len(parts) > 2 else ""
    return level, type_, duration


def convert_reviews_to_numeric(reviews_text):
    if not reviews_text:
        return 0

    match = re.search(r"(\d+(?:\.\d+)?)(K|M)", reviews_text)
    if match:
        num = float(match.group(1))
        unit = match.group(2)
        if unit == "K":
            return int(num * 1000)
        elif unit == "M":
            return int(num * 1000000)

    match = re.search(r"(\d+)", reviews_text)
    if match:
        return int(match.group(1))
    return 0


def clean_skills(skills_text):
    if skills_text.startswith("Skills you'll gain:"):
        return skills_text[len("Skills you'll gain:") :].strip()
    return skills_text.strip()


def extract_course_info(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    courses = []
    course_cards = soup.select("ul.cds-9.css-5t8l4v.cds-10 li")
    print(f"Found {len(course_cards)} course cards")

    for card in course_cards:
        course = {}

        # Title
        title_elem = card.find("h3", class_="cds-CommonCard-title")
        course["title"] = title_elem.get_text(strip=True) if title_elem else ""

        # Partner
        partner_elem = card.find("p", class_="cds-ProductCard-partnerNames")
        course["partner"] = partner_elem.get_text(strip=True) if partner_elem else ""

        # Rating
        rating_elem = card.find("span", class_="css-4s48ix")
        course["rating"] = rating_elem.get_text(strip=True) if rating_elem else "-"

        # Reviews
        rating_elem = card.find("span", class_="css-4s48ix")
        if rating_elem:
            # Find the next div with css-vac8rf after the rating
            next_elem = rating_elem.find_next("div", class_="css-vac8rf")
            if next_elem and "reviews" in next_elem.get_text().lower():
                course["reviews"] = next_elem.get_text(strip=True)
            else:
                course["reviews"] = ""
        else:
            course["reviews"] = ""

        course["reviews"] = convert_reviews_to_numeric(course["reviews"])

        # Skills
        skills_div = card.find("div", class_="cds-CommonCard-bodyContent")
        if skills_div:
            skills_p = skills_div.find("p", class_="css-vac8rf")
            if skills_p:
                course["skills"] = skills_p.get_text(strip=True).replace(
                    "Skills you'll gain: ", ""
                )
            else:
                course["skills"] = ""
        else:
            course["skills"] = ""

        course["skills"] = clean_skills(course["skills"])

        # Metadata (level, type, duration)
        metadata_div = card.find("div", class_="cds-CommonCard-metadata")
        if metadata_div:
            metadata_p = metadata_div.find("p")
            metadata = metadata_p.get_text(strip=True) if metadata_p else ""
        else:
            metadata = ""

        level, type_, duration = extract_metadata(metadata)
        course["level"] = level
        course["type"] = type_
        course["duration"] = duration

        # URL (from the link)
        link_elem = card.find("a", class_="cds-CommonCard-titleLink")
        if link_elem and "href" in link_elem.attrs:
            href = str(link_elem["href"])
            course["url"] = "https://www.coursera.org" + href
            course["url_sheet"] = '=HYPERLINK("' + course["url"] + '", "url")'
        else:
            course["url"] = ""
            course["url_sheet"] = ""
        # Degree
        degree_elem = card.find("p", class_="css-ls7ln4")
        course["degree"] = (
            "degree"
            if degree_elem and "Build toward a degree" in degree_elem.get_text()
            else "-"
        )

        # AI Skills
        elems = card.find_all("span", class_="css-1ast7yb")
        course["AI skills"] = (
            "AI skills"
            if elems and any("AI skills" in elem.get_text() for elem in elems)
            else "-"
        )

        # New
        course["new"] = (
            "new" if elems and any("New" in elem.get_text() for elem in elems) else "-"
        )
        courses.append(course)

    return courses


def save_to_csv(courses, output_file):
    if not courses:
        print("No courses found.")
        return

    fieldnames = [
        "idx",
        "selected",
        "partner",
        "title",
        "level",
        "type",
        "duration",
        "degree",
        "AI skills",
        "new",
        "rating",
        "reviews",
        "url",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for course in courses:
            course["url"] = course["url_sheet"]
            del course["url_sheet"]
            del course["skills"]
            writer.writerow(course)


def get_html_content(url):
    print(url)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("--window-size=1280,720")
    options.add_argument("--window-size=1080,1920")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "cds-ProductCard-base"))
    )

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    html_content = driver.page_source
    driver.quit()

    return html_content


if __name__ == "__main__":
    selected_courses_file = "selected.json"
    selected_courses = json.load(open(selected_courses_file, "r"))
    selected_courses = [
        (course["partner"], course["title"]) for course in selected_courses
    ]

    url_search = "https://www.coursera.org/search?"
    language = "English"
    plus = "true"
    sort_by = "NEW"

    partners = [
        "IBM",
        "Google",
        "Google Cloud",
        "Microsoft",
        "Amazon Web Services",
        "Meta",
        "Alberta Machine Intelligence Institute",
        "Anthropic",
    ]

    product_type_description = ["Professional Certificates", "Specializations"]

    tags_case = ["RAG", "MCP", "LLM"]

    tags_no_case = [
        "Generative AI",
        "AI Dev",
        "AI Agent",
        "AI Engineer",
        "Agents",
        "Agentic",
        "Prompt",
        "GenAI",
        "LangGraph",
        "LangChain",
        "Hugging Face",
        "OpenAI",
        "Retrieval-Augmented Generation",
    ]

    skip_lang_tags = ["-tr", "-ja", "-jp", "-fr", "-ko", "-br", "-es", "-bhid", "-zeka"]

    partners_query = "&".join([f'partners={e.replace(" ", "%20")}' for e in partners])
    product_type_description_query = "&".join(
        [
            f'productTypeDescription={p.replace(" ", "%20")}'
            for p in product_type_description
        ]
    )

    url_parts = [
        f"language={language}",
        partners_query,
        f"isPartOfCourseraPlus={plus}",
        product_type_description_query,
        f"sortBy={sort_by}",
    ]
    url = url_search + "&".join(url_parts)

    html_content = get_html_content(url)
    courses = extract_course_info(html_content)

    def is_genai_course(course):
        title = course["title"]
        skills = course["skills"]
        text = f"{title} {skills}"
        text_lower = text.lower()

        if any(tag in text for tag in tags_case):
            return True
        if any(tag.lower() in text_lower for tag in tags_no_case):
            return True
        return False

    def is_english_course(course):
        url = course["url"]

        if any(url.endswith(skip_tag) for skip_tag in skip_lang_tags):
            return False
        return True

    genai_courses = []
    course_idx = 1

    for course in courses:
        if is_genai_course(course) and is_english_course(course):
            course["idx"] = course_idx

            if (course["partner"], course["title"]) in selected_courses:
                course["selected"] = "selected"
            else:
                course["selected"] = None

            genai_courses.append(course)
            course_idx += 1

    output_file = "coursera_courses.csv"

    save_to_csv(genai_courses, output_file)

    print(f"Extracted {len(genai_courses)} courses and saved to {output_file}")
