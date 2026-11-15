#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
command -v npx >/dev/null || { echo 'Node.js and npm are required to regenerate diagrams.'; exit 1; }
extra=()
if [[ $# -gt 1 ]]; then
  echo 'Usage: bash docs/diagrams/render.sh [absolute-path-to-puppeteer-config.json]'
  exit 1
fi
if [[ $# -eq 1 ]]; then
  extra=(-p "$1")
fi
for source in [0-9][0-9]-*.mmd; do
  npx --yes --package @mermaid-js/mermaid-cli@11.12.0 mmdc \
    -i "$source" -o "${source%.mmd}.svg" \
    -c mermaid-config.json -b white "${extra[@]}"
done
