#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote


def to_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def to_hyperlink_formula(url: Any) -> str:
    if not url:
        return ""
    safe_url = str(url).replace('"', '""')
    return f'=HYPERLINK("{safe_url}", "Open")'


def to_author_hyperlink_formula(name: str) -> str:
    query = quote(f'author:"{name}"', safe="")
    url = f"https://learning.oreilly.com/search/?q={query}"
    safe_url = url.replace('"', '""')
    safe_name = name.replace('"', '""')
    return f'=HYPERLINK("{safe_url}", "{safe_name}")'


def to_local_time_label(value: Any) -> str:
    if not value:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    try:
        dt_utc = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text

    local_dt = dt_utc.astimezone()
    return f"{local_dt:%Y-%m-%d %H:%M:%S}"


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def load_contributor_order(file_path: str) -> list[str]:
    names = Path(file_path).read_text(encoding="utf-8").splitlines()
    cleaned_names = [" ".join(name.strip().split()) for name in names]
    deduped: dict[str, str] = {}
    for name in cleaned_names:
        if not name:
            continue
        key = normalize_name(name)
        if key not in deduped:
            deduped[key] = name
    return list(deduped.values())


def to_contributors_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = [" ".join(str(item).strip().split()) for item in value if item is not None]
    return [name for name in cleaned if name]


def build_contributor_columns(
    events: list[dict[str, Any]], preferred_order: list[str] | None
) -> list[str]:
    discovered_map: dict[str, str] = {}
    for event in events:
        for name in to_contributors_list(event.get("contributors")):
            key = normalize_name(name)
            if key not in discovered_map:
                discovered_map[key] = name

    if not preferred_order:
        return list(discovered_map.values())

    ordered: list[str] = []
    added: set[str] = set()
    for preferred_name in preferred_order:
        key = normalize_name(preferred_name)
        if key in discovered_map and key not in added:
            ordered.append(preferred_name)
            added.add(key)

    for key, name in discovered_map.items():
        if key not in added:
            ordered.append(name)
    return ordered


def collect_keys(events: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    non_session_keys: list[str] = []
    session_keys: list[str] = []

    for event in events:
        for key in event.keys():
            if key not in {"sessions", "contributors"} and key not in non_session_keys:
                non_session_keys.append(key)

        for session in event.get("sessions") or []:
            for key in session.keys():
                if key not in session_keys:
                    session_keys.append(key)

    return non_session_keys, session_keys


def order_session_keys(session_keys: list[str]) -> list[str]:
    prioritized = [key for key in ["start_time", "end_time"] if key in session_keys]
    remaining = [key for key in session_keys if key not in {"start_time", "end_time"}]
    return prioritized + remaining


def build_base_row(
    event: dict[str, Any],
    non_session_keys: list[str],
    total_sessions: int,
    session_index: int,
) -> dict[str, str]:
    row: dict[str, str] = {}
    for key in non_session_keys:
        value = event.get(key)
        if key == "title" and total_sessions > 1 and value:
            row[key] = f"{value} ({session_index})"
        elif key == "url":
            row[key] = to_hyperlink_formula(value)
        else:
            row[key] = to_csv_value(value)
    return row


def build_contributor_cells(
    event_contributors: list[str], contributor_columns: list[str]
) -> dict[str, str]:
    event_keys = {normalize_name(name) for name in event_contributors}
    cells: dict[str, str] = {}
    for name in contributor_columns:
        cells[name] = (
            to_author_hyperlink_formula(name) if normalize_name(name) in event_keys else ""
        )
    return cells


def build_rows(
    events: list[dict[str, Any]], contributor_columns: list[str]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    non_session_keys, session_keys = collect_keys(events)
    ordered_session_keys = order_session_keys(session_keys)

    for event in events:
        sessions = event.get("sessions") or []
        total_sessions = len(sessions)
        event_contributors = to_contributors_list(event.get("contributors"))
        contributor_cells = build_contributor_cells(event_contributors, contributor_columns)

        for session_index, session in enumerate(sessions, start=1):
            row = {"idx": str(len(rows) + 1)}
            row.update(
                build_base_row(
                    event=event,
                    non_session_keys=non_session_keys,
                    total_sessions=total_sessions,
                    session_index=session_index,
                )
            )
            for key in ordered_session_keys:
                value = session.get(key)
                row[key] = (
                    to_local_time_label(value)
                    if key in {"start_time", "end_time"}
                    else to_csv_value(value)
                )
            row.update(contributor_cells)
            rows.append(row)

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert O'Reilly live events JSON to CSV with one row per session."
    )
    parser.add_argument(
        "--input",
        default="oreilly_live_events.json",
        help="Input JSON file path (default: oreilly_live_events.json).",
    )
    parser.add_argument(
        "--output",
        default="oreilly_live_events.csv",
        help="Output CSV file path (default: oreilly_live_events.csv).",
    )
    parser.add_argument(
        "--contributors-file",
        default=None,
        help="Optional file with contributor names (one per line) to define contributor column order.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    events = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(events, list):
        raise ValueError("Input JSON must be a list of event objects.")

    preferred_order = None
    if args.contributors_file:
        preferred_order = load_contributor_order(args.contributors_file)

    contributor_columns = build_contributor_columns(events, preferred_order)
    rows = build_rows(events, contributor_columns)

    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = []

    with open(args.output, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} row(s) to {args.output}")


if __name__ == "__main__":
    main()
