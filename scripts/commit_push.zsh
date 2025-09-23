#!/usr/bin/env zsh
set -euo pipefail
MSG="${1:-Tribestock: inventory model + endpoints + seeds + hubs/logs ($(date +'%Y-%m-%d %H:%M:%S'))}"
git rev-parse --git-dir >/dev/null 2>&1
git status --short || true
git add -A
if git diff --cached --quiet; then
  echo "No staged changes. Nothing to commit."
  exit 0
fi
git commit -m "$MSG"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTE="$(git remote | head -n1)"
if [ -z "$REMOTE" ]; then
  echo "No git remote configured. Add one, e.g.:"
  echo "  git remote add origin <YOUR_REPO_URL>"
  echo "  git push -u origin $BRANCH"
  exit 1
fi
git push -u "$REMOTE" "$BRANCH"
echo "Pushed '$MSG' to $REMOTE/$BRANCH"
