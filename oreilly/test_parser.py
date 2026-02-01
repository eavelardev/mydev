import pathlib
from scraper.oreilly_scraper import parse_search_html


def test_parse_oreilly_sample():
    sample = pathlib.Path("/home/eavelar/dev/oreilly.html").read_text(encoding="utf-8")
    courses = parse_search_html(sample)
    # basic sanity checks
    assert isinstance(courses, list)
    assert len(courses) >= 1

    # find a known course by title fragment
    titles = [c.title for c in courses]
    assert any("Building AI Apps with Gemini" in t or "GenAI Prompt to Product Showdown" in t for t in titles)

    # check structure of first items include URLs
    first = courses[0]
    assert first.title
    assert first.url, "Expected first course to have a URL"
    assert first.authors and isinstance(first.authors, list)

    # known URL for first course (from sample)
    assert first.url.endswith("/0642572010712/")
    # schedule info
    assert first.schedule_date == "Nov 26"
    assert first.schedule_time == "7am-11am"
    # publisher
    assert first.publisher == "O'Reilly Media, Inc."

    # Check that the known Prompt Engineering course includes a quiz
    prompt_course = None
    for c in courses:
        if c.product_id == "0790145740359" or "Prompt Engineering Deep Dive" in c.title:
            prompt_course = c
            break
    assert prompt_course is not None, "Expected to find the Prompt Engineering Deep Dive course in sample"
    assert getattr(prompt_course, "includes_quiz", False) is True

    # Check duration and month-year for AI Superstream: Large Language Models
    ai_course = None
    for c in courses:
        if "AI Superstream: Large Language Models" in c.title or c.product_id == "0636920889717":
            ai_course = c
            break
    assert ai_course is not None, "Expected to find 'AI Superstream: Large Language Models' in sample"
    # expected fallback parsed from meta: December 2023 and duration 3h 40m
    assert ai_course.schedule_date == "December 2023"
    assert getattr(ai_course, "duration", None) == "3h 40m"
