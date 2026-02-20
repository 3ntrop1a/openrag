#!/bin/bash
# push-public.sh — syncs public openrag repo, stripping docs/, docs_wte/, guide_openrag.txt
# Usage: bash scripts/push-public.sh  OR  make push-public

set -e

PUBLIC_REMOTE="public"
TEMP_BRANCH="public-sync-$$"

# Cleanup: delete private files from disk so git checkout main can restore them
cleanup() {
  rm -rf docs/ docs_wte/ guide_openrag.txt 2>/dev/null || true
  git checkout -f main 2>/dev/null || true
  git branch -D "$TEMP_BRANCH" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

CURRENT=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT" != "main" ]]; then
  echo "Must be on main branch (currently on $CURRENT)"; exit 1
fi
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Uncommitted changes detected — commit or stash first"; exit 1
fi
if ! git remote get-url "$PUBLIC_REMOTE" &>/dev/null; then
  echo "Remote '$PUBLIC_REMOTE' not found. Add it:"; echo "  git remote add public https://github.com/3ntrop1a/openrag.git"; exit 1
fi

echo "Creating temp branch $TEMP_BRANCH..."
git checkout -b "$TEMP_BRANCH"

echo "Removing private-only files from index..."
git rm -rf --cached docs/ docs_wte/ guide_openrag.txt 2>/dev/null || true

if ! git diff --cached --quiet; then
  git commit -m "chore: strip private files for public sync"
fi

echo "Pushing to $PUBLIC_REMOTE/main..."
git push "$PUBLIC_REMOTE" "$TEMP_BRANCH:main" --force

echo ""
echo "Public repo synced: https://github.com/3ntrop1a/openrag"
# trap fires on exit: removes private files from disk, restores main
