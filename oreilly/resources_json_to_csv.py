#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import datetime
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


def to_hyperlink_formula_with_label(url: Any, label: Any) -> str:
    if not url:
        return to_csv_value(label)
    safe_url = str(url).replace('"', '""')
    safe_label = to_csv_value(label).replace('"', '""')
    return f'=HYPERLINK("{safe_url}", "{safe_label}")'


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


def to_hours_minutes_from_seconds(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        total_minutes = int(round(float(value) / 60))
    except (TypeError, ValueError):
        return to_csv_value(value)

    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"


def to_hours_minutes_from_minutes(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        total_minutes = int(round(float(value)))
    except (TypeError, ValueError):
        return to_csv_value(value)

    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"


def to_publisher(value: Any) -> str:
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if item is not None and str(item).strip()]
        return cleaned[0] if cleaned else ""
    return to_csv_value(value)


def to_authors_cell(value: Any) -> str:
    if not isinstance(value, list):
        return ""

    cleaned_names = [
        " ".join(str(name).strip().split()) for name in value if name is not None and str(name).strip()
    ]
    if not cleaned_names:
        return ""

    formulas = [to_author_hyperlink_formula(name) for name in cleaned_names]
    return " | ".join(formulas)


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def to_authors_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = [" ".join(str(name).strip().split()) for name in value if name is not None and str(name).strip()]
    return [name for name in cleaned if name]


def build_author_columns(resources: list[dict[str, Any]], preferred_order: list[str] | None = None) -> list[str]:
    discovered_map: dict[str, str] = {}
    for resource in resources:
        for name in to_authors_list(resource.get("authors")):
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


def build_author_cells(resource_authors: list[str], author_columns: list[str]) -> dict[str, str]:
    event_keys = {normalize_name(name) for name in resource_authors}
    cells: dict[str, str] = {}
    for name in author_columns:
        cells[name] = to_author_hyperlink_formula(name) if normalize_name(name) in event_keys else ""
    return cells


def load_author_order(file_path: str) -> list[str]:
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


def load_selected_ids(file_path: str) -> set[str]:
    try:
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
    except Exception:
        return set()

    ids: set[str] = set()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                val = item.get("id") or item.get("archive_id") or item.get("isbn")
                if val is not None:
                    ids.add(str(val).strip())
            else:
                ids.add(str(item).strip())
    return ids


def extract_edition_from_title(title: Any) -> str:
    if not title:
        return ""
    text = str(title)
    import re

    m = re.search(r"(\d+)(?:st|nd|rd|th)?\s+edition", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    words = {
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
    }
    for word, num in words.items():
        if re.search(rf"\b{word}\b\s+edition", text, flags=re.IGNORECASE):
            return num

    return ""


def extract_has_quiz_from_description(description: Any) -> str:
    if not description:
        return ""
    text = str(description)
    return "quiz" if "with quizzes" in text.lower() else ""


def build_row(resource: dict[str, Any], selected_ids: set[str]) -> dict[str, Any]:
    archive_id = to_csv_value(resource.get("archive_id"))
    web_url = resource.get("web_url")
    full_url = f"https://learning.oreilly.com{web_url}" if web_url else None

    return {
        "id": f"'{archive_id}",
        "select": "select" if archive_id and archive_id in selected_ids else None,
        "publisher": to_publisher(resource.get("publishers")),
        "title": resource.get("title"),
        "edition": extract_edition_from_title(resource.get("title")),
        "url": to_hyperlink_formula_with_label(full_url, "Open"),
        "issued": to_local_time_label(resource.get("issued")),
        "last modified": to_local_time_label(resource.get("last_modified_time")),
        "format": to_csv_value(resource.get("format")),
        "video classification": to_csv_value(resource.get("video_classification")),
        "quiz": extract_has_quiz_from_description(resource.get("description")),
        "time required": to_hours_minutes_from_minutes(resource.get("minutes_required")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert O'Reilly resources JSON to CSV with selected columns."
    )
    parser.add_argument(
        "--input",
        default="oreilly_resources.json",
        help="Input JSON file path (default: oreilly_resources.json).",
    )
    parser.add_argument(
        "--output",
        default="oreilly_resources.csv",
        help="Output CSV file path (default: oreilly_resources.csv).",
    )
    parser.add_argument(
        "--authors-file",
        default="authors.txt",
        help="Optional file with author names (one per line) to define author column order.",
    )
    parser.add_argument(
        "--selected-file",
        default="selected_resources.json",
        help="Optional JSON file listing selected resources (array of objects with 'id').",
    )

    args = parser.parse_args()

    resources = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(resources, list):
        raise ValueError("Input JSON must be a list of resource objects.")

    base_fieldnames = [
        "id",
        "select",
        "publisher",
        "title",
        "edition",
        "url",
        "issued",
        "last modified",
        "format",
        "video classification",
        "quiz",
        "time required",
    ]

    preferred_order = None
    if args.authors_file:
        preferred_order = load_author_order(args.authors_file)

    selected_ids: set[str] = set()
    if args.selected_file:
        selected_ids = load_selected_ids(args.selected_file)

    author_columns = build_author_columns(resources, preferred_order)

    fieldnames = base_fieldnames + author_columns

    rows: list[dict[str, str]] = []
    for resource in resources:
        row = build_row(resource, selected_ids)
        resource_authors = to_authors_list(resource.get("authors"))
        row.update(build_author_cells(resource_authors, author_columns))
        rows.append(row)

    with open(args.output, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} row(s) to {args.output}")


if __name__ == "__main__":
    main()
