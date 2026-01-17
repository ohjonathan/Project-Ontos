---
id: installation_ux_proposal_review
type: strategy
status: draft
depends_on: [installation_ux_proposal, philosophy, mission]
concepts: [ux, installation, dx, onboarding, packaging, security]
---

# Review: Installation UX Proposal — Author: Codex (GPT-5)

**Author:** Codex (GPT-5)

## 1) Rationale Test
- Scope assumes “10+ commands” but lacks real user personas, failure data, or severity metrics; the target experience may be mis-calibrated for greenfield users vs. contributors vs. enterprise/constrained envs.
- Trust story is missing: `curl | bash` and `pipx install` are proposed without checksums/signatures, provenance, or pinning; uninstall/rollback for partial or malicious installs is not covered.
- Platform gaps: plan leans on `install.sh` (bash + git) without Windows/WSL or Python-version constraints; no proxy/offline path, so “universal” claim is weak.
- Migration/conflict handling is conceptual only: no default behaviors for existing `docs/`, hook collisions, or schema/version mismatches; rollback and idempotency are unspecified.
- Upgrade path is absent: how existing `ontos_init.py` installs transition to CLI; mixed-version detection/refusal and config migration are undefined.
- Operational robustness is thin: no acceptance tests for re-runs, partial failure handling, or corporate network constraints; success metrics lack measurement hooks.

## 2) What I Would Do Differently
- Ship a cross-platform Python bootstrap first (Phase 0) instead of `curl | bash` as primary: `python -m ontos.install --mode=prompted --yes` that downloads a versioned, checksummed archive and works on Windows/macOS/Linux.
- Define an install manifest (YAML) listing files, destinations, and merge policy; installer consumes the manifest, enabling plan output, backups, and rollback; no hard-coded copy logic.
- Make idempotency first-class: dry-run/plan, explicit overwrite/backup flags, atomic writes (tmp + move), and clean rollback on error; re-running install should be safe.
- Treat provenance as a requirement: publish signed checksums (and optionally GPG signatures) for release archives and scripts; document the trust model prominently.
- Split contributor vs. user flows: detect running inside Ontos repo; downstream users consume packaged artifacts, not git clones; contributors get a short-circuit path.
- Prioritize a minimal win: one-command installer + corrected uninstall docs before widening the CLI surface.

## 3) Additional Improvements Within Current Structure
- Acceptance tests: add matrix for Windows/WSL/macOS/Linux, proxy/offline, existing `docs/`, existing hooks, re-run install/uninstall; fail CI on regressions.
- Conflict policy: specify defaults (e.g., backup to `.ontos-backup/YYYYMMDD/`, refuse overwrite without `--force`, always show plan) and include rollback steps for partial installs.
- Upgrade semantics: `ontos update` should compare installed vs. desired version, migrate config, and hard-fail on incompatible mixes with clear remediation.
- Security: bundle checksums for `install.sh`/archives, add `--verify-only` mode, pin versions in bootstrap, and avoid network fetches without verification.
- Single source of truth: declare canonical `Common_Concepts.md`/agent instructions; installer copies only from canonical location and validates that stubs/duplicates are removed.
- UX polish: improve `--help` with real examples and flow cues; post-install summary (mode chosen, hooks installed, context map generated, how to uninstall); add preview of file system changes before writing.

## Closing
The proposal’s direction (1–2 command install, unified CLI) is solid, but it needs a stronger security/provenance story, cross-platform plan, explicit conflict/upgrade semantics, and testable idempotency to be production-safe.
