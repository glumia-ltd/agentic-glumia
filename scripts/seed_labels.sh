#!/usr/bin/env bash
set -euo pipefail
OWNER="${GITHUB_OWNER:-}"
REPO="${GITHUB_REPO:-}"
if [ -z "${OWNER}" ] || [ -z "${REPO}" ]; then
  echo "Set GITHUB_OWNER and GITHUB_REPO env vars."
  exit 1
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI required. Install: https://cli.github.com/"
  exit 1
fi
if [ -f labels.json ]; then
  mapfile -t KEYS < <(jq -r 'keys[]' labels.json)
  for k in "${KEYS[@]}"; do
    color=$(jq -r --arg k "$k" '.[$k].color' labels.json)
    desc=$(jq -r --arg k "$k" '.[$k].description' labels.json)
    gh label edit "$k" --color "$color" --description "$desc" --repo "$OWNER/$REPO" 2>/dev/null ||       gh label create "$k" --color "$color" --description "$desc" --repo "$OWNER/$REPO"
    echo "✔ $k"
  done
else
  declare -A COLORS=( ["area/agent"]="1f77b4" )
  for k in "${!COLORS[@]}"; do
    gh label edit "$k" --color "${COLORS[$k]}" --repo "$OWNER/$REPO" 2>/dev/null ||       gh label create "$k" --color "${COLORS[$k]}" --repo "$OWNER/$REPO"
    echo "✔ $k"
  done
fi
echo "Done."
