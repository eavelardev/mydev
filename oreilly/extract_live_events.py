#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_API_URL = "https://www.oreilly.com/api/v1/live-events/"
BASE_EVENT_URL = "https://www.oreilly.com/live-events"


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def load_contributors_filter(file_path: str) -> set[str]:
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    names = {normalize_name(line) for line in lines if line.strip()}
    if not names:
        raise ValueError(f"No contributor names found in {file_path}")
    return names


def fetch_page(limit: int, timeout: int = 30) -> dict[str, Any]:
    params = urlencode({"limit": limit})
    url = f"{BASE_API_URL}?{params}"
    print(f"Fetching: {url}")
    with urlopen(url, timeout=timeout) as response:
        return json.load(response)


def extract_description(item: dict[str, Any]) -> str:
    short_description = (item.get("short_description") or "").strip()
    return short_description if short_description else ""

def extract_contributors(item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for contributor in item.get("contributors", []):
        full_name = (contributor.get("full_name") or "").strip()
        names.append(full_name)

    return names


def extract_sessions(item: dict[str, Any]) -> list[dict[str, str]]:
    sessions: list[dict[str, str]] = []
    for session in item.get("sessions", []):
        start_time = session.get("start_time")
        end_time = session.get("end_time")
        if start_time and end_time:
            sessions.append({"start_time": start_time, "end_time": end_time})

    return sessions


def build_event_url(item: dict[str, Any]) -> str:
    slug = item.get("slug")
    series_identifier = item.get("series_identifier")
    product_identifier = item.get("product_identifier")
    if slug and series_identifier and product_identifier:
        return f"{BASE_EVENT_URL}/{slug}/{series_identifier}/{product_identifier}/"
    return ""


def normalize_event(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title", ""),
        "description": extract_description(item),
        "contributors": extract_contributors(item),
        "sessions": extract_sessions(item),
        "url": build_event_url(item),
    }


def matches_contributor_filter(contributors: list[str], allowed_names: set[str]) -> bool:
    return any(normalize_name(name) in allowed_names for name in contributors)


def fetch_events(total_limit: int, allowed_names: set[str]) -> list[dict[str, Any]]:
    if total_limit <= 0:
        return []

    collected: list[dict[str, Any]] = []
    payload = fetch_page(limit=total_limit)
    results = payload.get("results", [])

    for item in results:
        normalized = normalize_event(item)
        if matches_contributor_filter(normalized["contributors"], allowed_names):
            collected.append(normalized)
            if len(collected) >= total_limit:
                break

    return collected[:total_limit]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract O'Reilly live event information into a compact JSON file."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of live events to fetch (default: 300).",
    )
    parser.add_argument(
        "--output",
        default="oreilly_live_events.json",
        help="Output JSON file path (default: oreilly_live_events.json).",
    )
    parser.add_argument(
        "--contributors-file",
        default="contributors.txt",
        help="Path to newline-separated contributor names used for filtering (default: contributors.txt).",
    )
    args = parser.parse_args()

    allowed_names = load_contributors_filter(args.contributors_file)
    events = fetch_events(args.limit, allowed_names)

    with open(args.output, "w", encoding="utf-8") as out_file:
        json.dump(events, out_file, ensure_ascii=False, indent=4)

    print(f"Saved {len(events)} event(s) to {args.output}")


if __name__ == "__main__":
    main()
