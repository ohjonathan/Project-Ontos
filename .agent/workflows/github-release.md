---
description: how to create GitHub releases for Project Ontos
---

# GitHub Release Workflow

## Prerequisites

The `gh` CLI must be authenticated with a token that has **Contents: Read and write** permission.
The current PAT is a fine-grained PAT stored in the macOS keyring.

If `gh release create` returns HTTP 403, the PAT needs updating:
1. Go to https://github.com/settings/tokens → find the active fine-grained PAT
2. Edit it → under **Repository permissions**, set **Contents** to **Read and write**
3. Save → the keyring token updates automatically

> **Note**: `.zshrc` exports `GITHUB_TOKEN="$(gh auth token)"` which means
> any new shell inherits the keyring token. If the env var is stale, run
> `export GITHUB_TOKEN="$(gh auth token)"` to refresh it.

## Creating a Release

// turbo-all

1. Ensure release notes exist in `docs/releases/vX.Y.Z.md`

2. Create the release (not latest):
```bash
gh release create vX.Y.Z --repo ohjonathan/Project-Ontos --title "vX.Y.Z" --latest=false --notes-file docs/releases/vX.Y.Z.md
```

3. If this IS the latest release, use `--latest=true` instead.

## Batch Creating Releases

A batch script exists at `docs/releases/create_releases.sh`.
Edit it to include only the releases you need, then run:
```bash
bash docs/releases/create_releases.sh
```

## Writing Release Notes

Source release details from:
- `CHANGELOG.md` — high-level feature summaries
- `Ontos_CHANGELOG.md` — detailed technical changelog
- `git log --oneline vPREV..vCURR` — commit-level detail
- `docs/releases/` — any existing release note drafts
- PR descriptions via `gh pr view <number>`

Format: Use GitHub markdown with sections for Highlights, Features, Bug Fixes, Documentation, Testing, and a Full Changelog comparison link.
