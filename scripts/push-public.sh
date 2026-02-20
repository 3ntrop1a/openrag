#!/bin/bash
# push-public.sh
# Syncs the public openrag repo from the private one.
# Excludes: docs/, docs_wte/, guide_openrag.txt
#
# Usage: bash scripts/push-public.sh
#    or: make push-public

set -e

PUBLIC_REMOTE="public"
TEMP_BRANCH="public-sync-$$"

# Ensure we are on main and working tree is clean
CURRENT=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT" != "main" ]]; then
  echo "❌ Must be on main branch (currently on $CURRENT)"
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "❌ Uncommitted changes detected — commit or stash first"
  exit 1
fi

# Check public remote exists
if ! git remote get-url "$PUBLIC_REMOTE" &>/dev/null; then
  echo "❌ Remote '$PUBLIC_REMOTE' not configured."
  echo "   Add it with:"
  echo "   git remote add public https://github.com/3ntrop1a/openrag.git"
  exit 1
fi

echo "🔀 Creating temporary branch $TEMP_BRANCH..."
git checkout -b "$TEMP_BRANCH"

echo "🗑️  Removing private-only files..."
git rm -rf --cached docs/ docs_wte/ guide_openrag.txt 2>/dev/null || true

# Only commit if there's something to commit
if ! git diff --cached --quiet; then
  git commit -m "chore: strip private files for public sync"
fi

echo "🚀 Pushing to '$PUBLIC_REMOTE' (main)..."
git push "$PUBLIC_REMOTE" "$TEMP_BRANCH:main" --force

echo "🧹 Cleaning up..."
git checkout main
git branch -D "$TEMP_BRANCH"

echo ""
echo "✅ Public repo synced successfully!"
echo "   https://github.com/3ntrop1a/openrag"
