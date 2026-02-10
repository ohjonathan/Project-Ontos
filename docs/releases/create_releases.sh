#!/usr/bin/env bash
# Create GitHub releases for all missing tagged versions (v3.0.4 through v3.2.2).
# Requires: gh CLI authenticated with a token that has 'repo' scope.
#
# Usage:
#   gh auth login --scopes repo    # if PAT lacks release permissions
#   bash docs/releases/create_releases.sh
#
set -euo pipefail
REPO="ohjonathan/Project-Ontos"

echo "==> Creating release v3.0.4..."
gh release create v3.0.4 \
  --repo "$REPO" \
  --title "v3.0.4" \
  --latest=false \
  --notes-file docs/releases/v3.0.4.md

echo "==> Creating release v3.0.5..."
gh release create v3.0.5 \
  --repo "$REPO" \
  --title "v3.0.5" \
  --latest=false \
  --notes-file docs/releases/v3.0.5.md

echo "==> Creating release v3.1.0..."
gh release create v3.1.0 \
  --repo "$REPO" \
  --title "v3.1.0" \
  --latest=false \
  --notes-file docs/releases/v3.1.0.md

echo "==> Creating release v3.1.1..."
gh release create v3.1.1 \
  --repo "$REPO" \
  --title "v3.1.1" \
  --latest=false \
  --notes-file docs/releases/v3.1.1.md

echo "==> Creating release v3.2.0..."
gh release create v3.2.0 \
  --repo "$REPO" \
  --title "v3.2.0" \
  --latest=false \
  --notes-file docs/releases/v3.2.0.md

echo "==> Creating release v3.2.1..."
gh release create v3.2.1 \
  --repo "$REPO" \
  --title "v3.2.1" \
  --latest=false \
  --notes-file docs/releases/v3.2.1.md

echo "==> Creating release v3.2.2 (Latest)..."
gh release create v3.2.2 \
  --repo "$REPO" \
  --title "v3.2.2" \
  --latest=true \
  --notes-file docs/releases/v3.2.2.md

echo "✅ All 7 releases created successfully."
