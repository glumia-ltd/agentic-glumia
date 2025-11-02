#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/bootstrap_repo.sh <owner_or_org> [repo_name] [visibility]
# Example: ./scripts/bootstrap_repo.sh your-gh-username ai-project-agent-starter private

OWNER="${1:-YOUR_GH_USER_OR_ORG}"
REPO="${2:-ai-project-agent-starter}"
VISIBILITY="${3:-private}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install: https://cli.github.com/"
  echo "Then run: gh auth login"
  exit 1
fi

# Ensure git is initialized
if [ ! -d .git ]; then
  git init
  git add .
  git commit -m "feat: initial commit (agent starter)"
fi

# Create remote repo if it doesn't exist; otherwise just push.
if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "Repo exists: $OWNER/$REPO"
  git remote remove origin >/dev/null 2>&1 || true
  gh repo set-default "$OWNER/$REPO" || true
  git remote add origin "https://github.com/$OWNER/$REPO.git"
else
  gh repo create "$OWNER/$REPO" --source . --remote origin --"$VISIBILITY" -y
fi

# Push main
git checkout -B main
git push -u origin main

echo "Repository ready: https://github.com/$OWNER/$REPO"
