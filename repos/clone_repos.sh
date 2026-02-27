#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Allow passing the markdown list file as the first CLI argument.
# Usage: clone_repos.sh [path/to/list.md]
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [path/to/list.md]"
  exit 0
fi
LIST_FILE="${1:-$ROOT_DIR/ReAct repos.md}"

if [[ ! -f "$LIST_FILE" ]]; then
  echo "Missing $LIST_FILE" >&2
  exit 1
fi

echo "Cloning repos listed in $LIST_FILE into $ROOT_DIR"

# Parse markdown bullet links like: * [org/**repo**](url) or - [text](url)
while IFS= read -r line; do
  # Skip lines that don't look like markdown link bullets
  if ! printf '%s\n' "$line" | grep -Eq '^\s*[*-]\s*\[.*\]\(.*\)'; then
    continue
  fi

  # Extract the URL inside the last parentheses on the line
  url="$(printf '%s\n' "$line" | sed -n 's/.*(\([^)]*\)).*/\1/p')"

  # Try to extract bolded repo name between **...** first
  repo="$(printf '%s\n' "$line" | sed -n 's/.*\*\*\([^*][^*]*\)\*\*.*/\1/p')"

  # Fallback: use the link text inside [ ... ] if bold not present
  if [[ -z "$repo" ]]; then
    repo="$(printf '%s\n' "$line" | sed -n 's/.*\[\s*\([^]]*\)\s*\].*/\1/p')"
    # If link text contains org/repo, use basename
    repo="$(basename "$repo")"
  fi

  # Trim whitespace from extracted values
  repo="$(printf '%s' "$repo" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  url="$(printf '%s' "$url" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

  if [[ -z "$repo" || -z "$url" ]]; then
    continue
  fi

  target="$ROOT_DIR/$repo"
  if [[ -d "$target/.git" ]]; then
    echo "Skipping $repo (already cloned)"
    continue
  fi
  if [[ -d "$target" ]]; then
    echo "Skipping $repo (target directory exists but is not a git repo)"
    continue
  fi

  echo "Cloning $repo from $url"
  git clone --depth 1 "$url" "$target"
done < "$LIST_FILE"
