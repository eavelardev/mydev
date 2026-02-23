import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_API_URL = "https://learning.oreilly.com/api/v2/search/"


def load_contributors_filter(file_path: str) -> list[str]:
    names = Path(file_path).read_text(encoding="utf-8").splitlines()

    if not names:
        raise ValueError(f"No contributor names found in {file_path}")
    return names


def fetch_resources(
    limit: int,
    allowed_names: list[str],
    formats: list[str],
    sort: str = "publication_date",
    order: str = "desc",
) -> list[dict]:
    params = {
        "query": " OR ".join(f'author:"{name}"' for name in allowed_names),
        "formats": formats,
        "issued_before": date.today().isoformat(),
        "sort": sort,
        "order": order,
        "limit": limit,
    }
    url = f"{BASE_API_URL}?{urlencode(params, doseq=True)}"
    print(f"Fetching: \n{url}")

    # resources = []
    with urlopen(url, timeout=30) as response:
        data = json.load(response)

    resources = data.get("results", [])

    return resources

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract O'Reilly resource information into a compact JSON file."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum number of resources to fetch (default: 200).",
    )
    parser.add_argument(
        "--output",
        default="oreilly_resources.json",
        help="Output JSON file path (default: oreilly_resources.json).",
    )
    parser.add_argument(
        "--contributors-file",
        default="contributors.txt",
        help="Path to newline-separated contributor names used for filtering (default: contributors.txt).",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["book", "article", "video"],
        help="List of formats to include (default: book article video).",
    )
    parser.add_argument(
        "--sort",
        default="publication_date",
        help="Sort field (default: publication_date).",
    )
    parser.add_argument(
        "--order",
        default="desc",
        help="Sort order (default: desc).",
    )
    args = parser.parse_args()

    allowed_names = load_contributors_filter(args.contributors_file)
    resources = fetch_resources(
        args.limit,
        allowed_names,
        args.formats,
        sort=args.sort,
        order=args.order,
    )

    with open(args.output, "w", encoding="utf-8") as out_file:
        json.dump(resources, out_file, ensure_ascii=False, indent=4)

    print(f"Saved {len(resources)} resource(s) to {args.output}")


if __name__ == "__main__":
    main()