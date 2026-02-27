#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


TAG_ORDER = ["cloud", "embedding", "vision", "tools", "thinking"]

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
                tags_found.add(str(t))

    tag_columns = [t for t in TAG_ORDER if t in tags_found]
    tag_columns.extend(sorted(tags_found - set(tag_columns)))

    fieldnames = [
        "idx",
        "select",
        "provider",
        "model_name",
        "model_version",
        "version_aliases",
        "latest",
        "q4",
        "q8",
        "f16",
        "q4,8,?",
        "param_size",
        "size_gb",
        "context",
        *tag_columns,
        "hybrid",
        "any",
        "RAG",
        "link",
        "date",
        "description",
    ]

    skip_models = [
        "deepseek-coder",
        "deepseek-v2",
        "deepseek-v2.5",
        "falcon",
        "falcon2",
        "gemma",
        "gemma2",
        "qwen",
        "qwen2",
        "qwen2-math",
        "qwen2.5",
        "qwen2.5-coder",
        "qwen2.5vl",
        "qwen3",
        "qwen3-vl",
        "qwen3-coder-next",
        "qwen3-next",
        "starcoder",
        "olmo-3",
        "olmo2",
        "deepseek-v3",
        "smollm",
        "granite3-dense",
        "llama2",
        "llama3",
        "llama3.1",
        "phi",
        "phi3",
        "devstral",
        "mistral-small",
        "mistral-small3.1",
        "wizardlm",
        "glm4"
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        model_idx = 1

        for m in models:
            model_name = m["model_name"]

            if model_name in skip_models:
                continue

            provider = m["provider"]
            description = m["description"]

            model_has_think_and_instruct = (
                any("thinking" in {t for t in v["tags"]} for v in m["versions"])
                and any("instruct" in {t for t in v["tags"]} for v in m["versions"])
            )

            model_has_think_or_instruct = (
                any("thinking" in {t for t in v["tags"]} for v in m["versions"])
                or any("instruct" in {t for t in v["tags"]} for v in m["versions"])
            )

            versions = sorted(
                m["versions"],
                key=lambda v: v["model_version"],
            )

            grouped: dict[str, list[dict]] = {}
            for v in versions:
                model_version_full = v["model_version"]
                hash_value = v["hash"]
                group_key = hash_value or f"nohash:{model_version_full}"
                grouped.setdefault(group_key, []).append(v)

            for group_versions in grouped.values():
                versions = [v["model_version"] for v in group_versions]
                all_versions_str = ", ".join(versions)
                versions_sorted = sorted(versions, key=lambda n: (len(n), n))
                version = versions_sorted[0] if versions_sorted else ""
                aliases = [n for n in versions_sorted[1:] if n]

                chosen = next((v for v in group_versions if v["model_version"] == version), group_versions[0])

                url = chosen.get("version_link", "")
                sheet_link = f'=HYPERLINK("{url}", "link")' if url else ""

                size_gb = chosen.get("size_gb", None)
                size_gb = None if size_gb is None else round(size_gb, 2)

                tags = set(t for t in chosen.get("tags", []))

                param_size = str(chosen.get("param_size", "") or "")

                select_providers = ["Google", "IBM", "Meta", "Microsoft", "NVIDIA", "OpenAI", "Mistral", "Moonshot AI", "Zhipu AI", "DeepSeek"]

                q4 = "q4" if "q4" in all_versions_str else None
                q8 = "q8" if "q8" in all_versions_str else None
                f16 = "f16" if "fp16" in all_versions_str or "bf16" in all_versions_str else None
                qx = "qx" if re.search(r"q\d", all_versions_str) else None

                row = {
                    "idx": model_idx,
                    "select": "select" if provider in select_providers or model_name.startswith("qwen3") else None,
                    "provider": provider,
                    "model_name": model_name,
                    "model_version": version,
                    "version_aliases": ", ".join(aliases),
                    "latest": "latest" if version == "latest" or "latest" in aliases else None,
                    "q4": q4,
                    "q8": q8,
                    "f16": f16,
                    "q4,8,?": "q4,8,?" if q4 or q8 or (not f16 and not qx) else None,
                    "param_size": param_size,
                    "size_gb": size_gb,
                    "context": chosen.get("context_display", ""),
                    "hybrid": "hybrid" if model_has_think_and_instruct else None,
                    "any": "any" if model_has_think_or_instruct else None,
                    "RAG": "RAG" if "RAG" in description else None,
                    "link": sheet_link,
                    "date": chosen.get("updated", ""),
                    "description": description,
                }

                for t in tag_columns:
                    row[t] = t if t in tags else None

                w.writerow(row)
                model_idx += 1

    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
