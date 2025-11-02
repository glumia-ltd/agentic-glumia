#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/protect_main.sh <owner_or_org> <repo_name>
# Requires: gh CLI authenticated with write:repo permissions (classic PAT) or appropriate fine-grained token.

OWNER="${1:-YOUR_GH_USER_OR_ORG}"
REPO="${2:-ai-project-agent-starter}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install: https://cli.github.com/"
  exit 1
fi

# Optional: list recent check names to help you configure required checks
echo "Recent check names (use these for required checks if needed):"
gh api "repos/$OWNER/$REPO/commits/$(git rev-parse HEAD)/check-runs" -H "Accept: application/vnd.github+json" | jq -r '.check_runs[].name' || true

echo
echo "Applying branch protection on 'main' (require PR + review; you can add required checks in the UI)."
gh api -X PUT "repos/$OWNER/$REPO/branches/main/protection"   -H "Accept: application/vnd.github+json"   -F required_pull_request_reviews.dismiss_stale_reviews=true   -F required_pull_request_reviews.required_approving_review_count=1   -F enforce_admins=true   -F restrictions=   -F required_status_checks.strict=false   -F required_status_checks.contexts[]=

echo "Branch protection set. In GitHub > Settings > Branches > Rules, add specific 'Status checks that are required' like 'CI / test (3.10)' and 'CI / test (3.11)' after the first run."
