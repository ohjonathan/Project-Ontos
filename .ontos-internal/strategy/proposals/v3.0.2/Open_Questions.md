# v3.0.2: Open Questions & Next Steps

**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-14
**Status:** Planning

---

## Deferred from v3.0.1

### Q1: PyPI Publishing

**Question:** Do you have PyPI credentials configured for this project?

**Context:**
- v3.0.1 is merged but not published to PyPI
- Users cannot `pip install ontos` until published
- Requires PyPI account with upload permissions

**Options:**
1. Use existing PyPI credentials (if configured)
2. Create new PyPI account for project
3. Use GitHub Actions for automated publishing
4. Keep as source-only distribution for now

**Suggested Next Step:** Decide on publishing strategy before v3.0.2

---

### Q2: Release Announcements

**Question:** What channels should be used for release announcements?

**Context:**
- v3.0.1 tag exists but no GitHub Release created
- No visibility into project communication channels

**Options:**
1. GitHub Releases only (minimal)
2. GitHub Releases + README badge
3. GitHub Releases + external channels (Discord/Slack/Twitter)
4. No public announcements (internal project)

**Suggested Next Step:** Create GitHub Release for v3.0.1, decide on ongoing announcement strategy

---

## Open Research Questions

### Q3: Architecture Violation

**Issue:** `ontos/core/config.py:229` imports from `ontos.io.git`

**Question:** Should this be fixed in v3.0.2 or tracked for later?

**Context:**
- Violates core/ → io/ constraint
- Pre-existing, not introduced by Phase 5
- Requires refactoring to inject dependency

**Suggested Next Step:** Assess effort and decide priority

---

### Q4: Test Count Reduction

**Observation:** Tests dropped from 411 to 395 between reviews

**Question:** Is this expected? Were tests removed intentionally?

**Suggested Next Step:** Audit test changes to confirm intentional

---

### Q5: Golden Master Framework

**Question:** Should golden tests be expanded for v3.0.2?

**Context:**
- Currently only 2 golden tests
- Framework exists but underutilized
- Could catch output regressions

**Suggested Next Step:** Define golden test coverage goals

---

## Suggested v3.0.2 Scope

| Priority | Item | Type |
|----------|------|------|
| Must | PyPI publishing setup | Infrastructure |
| Must | GitHub Release for v3.0.1 | Release |
| Should | Fix architecture violation | Tech debt |
| Should | Expand golden test coverage | Testing |
| Could | Automated release workflow | CI/CD |

---

## Next Steps

1. **Immediate:** Create GitHub Release for v3.0.1
2. **This week:** Decide PyPI publishing strategy
3. **v3.0.2 planning:** Address open questions above

---

**Document signed by:**
- **Role:** Chief Architect
- **Model:** Claude Opus 4.5
- **Date:** 2026-01-14
