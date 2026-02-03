#!/usr/bin/env python3
"""Fetch model URLs from https://ollama.com/search.

Usage:
  python get_model_urls.py
"""

from __future__ import annotations

import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

SEARCH_URL = "https://ollama.com/search"
PAGE_PARAM = "?page={}"
MODEL_PATH_PREFIX = "/library/"


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = None
        for key, value in attrs:
            if key.lower() == "href":
                href = value
                break
        if href:
            self.links.append(href)


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ModelURLFetcher/1.0)"
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_model_urls(html: str, base_url: str) -> list[str]:
    parser = LinkCollector()
    parser.feed(html)

    model_urls: set[str] = set()
    for href in parser.links:
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.path.startswith(MODEL_PATH_PREFIX):
            model_urls.add(full_url)

    return sorted(model_urls)


def get_model_urls() -> list[str]:
    all_urls: set[str] = set()
    page = 1

    while True:
        page_url = f"{SEARCH_URL}{PAGE_PARAM.format(page)}"
        try:
            html = fetch_html(page_url)
        except Exception as exc:
            print(f"Error fetching {page_url}: {exc}", file=sys.stderr)
            break

        page_urls = extract_model_urls(html, page_url)
        if not page_urls:
            break

        before_count = len(all_urls)
        all_urls.update(page_urls)
        if len(all_urls) == before_count:
            break

        page += 1

    return sorted(all_urls)

if __name__ == "__main__":
    all_urls = get_model_urls()

    print(f"Total models found: {len(all_urls)}")
