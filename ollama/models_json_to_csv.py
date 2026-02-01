#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


TAG_ORDER = ["cloud", "embedding", "thinking", "tools", "vision"]


def main() -> int:
    here = Path(__file__).resolve().parent
    json_path = here / "models_data.json"
    csv_path = here / "models.csv"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    models = data["models"]

    # Determine tag columns from per-version tags (keep canonical order first)
    tags_found: set[str] = set()
    for m in models:
        for v in m.get("versions", []):
            for t in v.get("tags", []):
                tags_found.add(str(t).lower())

    tag_columns = [t for t in TAG_ORDER if t in tags_found]
    tag_columns.extend(sorted(tags_found - set(tag_columns)))

    fieldnames = [
        "select",
        "provider",
        "model_name",
        "model_version",
        "param_size",
        "size_gb",
        "context",
        *tag_columns,
        "link",
        "description",
    ]

    def _model_sort_key(m: dict) -> tuple:
        provider_key = str(m.get("provider", "") or "").strip().lower()
        name_key = str(m.get("model_name", "") or "").strip().lower()
        return (provider_key, name_key)

    sorted_models = sorted(models, key=_model_sort_key)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for m in sorted_models:
            provider = str(m.get("provider", "") or "").strip()
            model_name = str(m.get("model_name", "") or "").strip()
            description = str(m.get("description", "") or "").strip()

            for v in sorted(
                m.get("versions", []),
                key=lambda v: str(v.get("model_version", "") or "").strip().lower(),
            ):
                url = v.get("version_link", "")
                sheet_link = f'=HYPERLINK("{url}", "link")' if url else ""

                size_gb = v.get("size_gb", None)
                size_gb_str = "" if size_gb is None else str(size_gb)

                input_types = v.get("input", [])

                tags = set(str(t).lower() for t in v.get("tags", []))

                model_version_full = str(v.get("model_version", "") or "").strip()
                param_size = str(v.get("param_size", "") or "").strip().lower()

                if ":" in model_version_full:
                    model_version = model_version_full.split(":", 1)[1].strip()
                else:
                    model_version = ""

                if model_version.strip().lower() == "latest":
                    continue

                cloud_from_version = "cloud" in model_version.lower()
                select_providers = ["Google", "IBM", "Meta", "Microsoft", "NVIDIA", "OpenAI", "Mistral", "Moonshot AI"]

                row = {
                    "select": "select" if provider in select_providers else None,
                    "provider": provider,
                    "model_name": model_name,
                    "model_version": model_version,
                    "param_size": param_size,
                    "size_gb": size_gb_str,
                    "context": v.get("context_display", ""),
                    "vision": "vision" if "Image" in input_types else None,
                    "link": sheet_link,
                    "description": description,
                }

                for t in tag_columns:
                    if t == "vision":
                        continue

                    if t == "cloud":
                        present = cloud_from_version
                    else:
                        present = t in tags

                    row[t] = t if present else None

                w.writerow(row)

    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
