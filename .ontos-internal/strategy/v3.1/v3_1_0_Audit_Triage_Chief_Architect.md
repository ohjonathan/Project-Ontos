---
id: v3_1_0_audit_triage_chief_architect
type: review
status: complete
depends_on: [v3_1_0_implementation_spec, v3_1_0_research_review_chief_architect]
concepts: [chief-architect-review, audit-triage, v3.1.0]
---

# v3.1.0 Audit Triage — Chief Architect

**Auditors:** Claude (Technical), Codex (Adversarial), Gemini (Strategic)
**Reviewer:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-21
**Status:** Complete

---

## Part 1: Issue Extraction

Deduplicated issues from all three audit reports:

| ID | Issue | Flagged By | Category | Research Relevance |
|----|-------|------------|----------|-------------------|
| AUD-01 | Legacy wrapper architecture (`_cmd_wrapper` + subprocess) | Claude, Codex | Architecture | N/A |
| AUD-02 | Wrapper commands don't honor `.ontos.toml` | Claude, Codex | Config | N/A |
| AUD-03 | `scaffold` command is broken (rejects positional args) | Claude, Codex | CLI | N/A |
| AUD-04 | `verify`, `query`, `consolidate` limited functionality | Claude, Codex | CLI | N/A |
| AUD-05 | MCP placeholder module is confusing | Claude, Codex | API/UX | §4.2 Navigator pattern |
| AUD-06 | Schema version mismatch (2.2 vs 3.0 definitions) | Claude | Schema | §5 Metadata staleness |
| AUD-07 | "Magic defaults" / implicit config resolution unclear | Claude | UX | N/A |
| AUD-08 | AGENTS.md activation flow is fragile | Claude | Integration | §2.1 Sidecar pattern |
| AUD-09 | Tests not included in published package | Claude, Codex | Quality | N/A |
| AUD-10 | Namespace collision with Databricks "ontos" | Gemini | Branding | N/A |
| AUD-11 | Rapid patch train (3.0.1→3.0.5 in 5 days) = stability concern | Codex | Release | N/A |
| AUD-12 | Frontmatter parsing edge cases (BOM, whitespace, `--`) | Codex | Parsing | §5.1.2 Schema validation |
| AUD-13 | Docs may not match installed version | Codex | Documentation | N/A |
| AUD-14 | SessionContext has mixed responsibilities | Claude | Architecture | N/A |
| AUD-15 | Incomplete type hints on public API | Claude | Code Quality | N/A |
| AUD-16 | No `--dry-run` on many commands | Claude | UX | N/A |

---

## Part 2: v3.1.0 Mapping

| Audit ID | v3.1.0 Item | Status | Notes |
|----------|-------------|--------|-------|
| AUD-01 | CMD-1 through CMD-7 | ✅ **Addressed** | Track B eliminates wrappers entirely |
| AUD-02 | CMD-1 through CMD-7 | ✅ **Addressed** | Native commands honor `.ontos.toml` |
| AUD-03 | CMD-1: scaffold | ✅ **Addressed** | Native implementation accepts positional args |
| AUD-04 | CMD-2/3/4: verify/query/consolidate | ✅ **Addressed** | Full native implementations |
| AUD-05 | — | ❌ Not in scope | MCP is v4.0 scope |
| AUD-06 | — | ❌ Not in scope | Schema alignment is separate concern |
| AUD-07 | — | ⚠️ Partial | `--verbose` could show resolved paths |
| AUD-08 | — | ❌ Not in scope | MCP server (v4.0) replaces manual activation |
| AUD-09 | — | ❌ Not in scope | Packaging concern, not feature scope |
| AUD-10 | — | ❌ Not in scope | Branding is non-technical |
| AUD-11 | — | ✅ **Addressed** | v3.1 is a feature release, not patch train |
| AUD-12 | ERR-1 | ⚠️ Partial | Better YAML errors, but not all edge cases |
| AUD-13 | — | ❌ Not in scope | Versioned docs is infrastructure |
| AUD-14 | — | ❌ Not in scope | Internal refactor, not user-facing |
| AUD-15 | — | ❌ Not in scope | Code quality, not feature scope |
| AUD-16 | CMD-1/4: scaffold/consolidate | ⚠️ Partial | `--dry-run` included for scaffold/consolidate |

---

## Part 3: Decision Matrix

Issues NOT fully addressed in v3.1.0:

| Audit ID | Decision | Target | Reasoning |
|----------|----------|--------|-----------|
| AUD-05 | **Defer** | v4.0 | MCP is explicitly v4.0 scope. Research §4.2 supports Navigator pattern but requires infrastructure first. Placeholder warning (v3.0.5) mitigates confusion. |
| AUD-06 | **Defer** | v3.2 | Schema 3.0 fields (`implements`, `tests`, `deprecates`) can be added in v3.2 without breaking changes. Low impact currently. |
| AUD-07 | **Accept** | v3.1 | Add `ontos doctor -v` verbose output showing resolved paths. Low effort, immediate value. |
| AUD-08 | **Defer** | v4.0 | Manual activation works. MCP server (v4.0) provides programmatic alternative. Research §2.1 confirms sidecar pattern is correct direction. |
| AUD-09 | **Defer** | v3.2 | Tests in sdist vs separate package is packaging decision. Document "run tests from repo" for now. |
| AUD-10 | **Reject** | — | Namespace claimed. README disclaimer exists. SEO is ongoing work, not a code fix. |
| AUD-12 | **Accept Risk** | v3.2 | ERR-1 improves most cases. Edge cases (BOM, `--` in content) documented as known limitations for v3.1. Full robustness in v3.2. |
| AUD-13 | **Defer** | v3.2 | Versioned docs requires ReadTheDocs or similar infrastructure. Not blocking. |
| AUD-14 | **Defer** | v3.2 | SessionContext refactor is internal. No user impact. Defer to post-v3.1. |
| AUD-15 | **Defer** | v3.2 | Type hints improvement is gradual. Not blocking adoption. |
| AUD-16 | **Partial** | v3.1 | `--dry-run` added to scaffold/consolidate. Other commands can get it in v3.2. |

---

## Part 4: Spec Amendments

### Additions

| New Item | Source | Priority | Rationale |
|----------|--------|----------|-----------|
| `ontos doctor -v` | AUD-07 | P1 | Show resolved paths (repo_root, config_path, docs_dir) in verbose mode. Low effort, addresses "magic defaults" concern. |

### Modifications

| Existing Item | Change | Source |
|---------------|--------|--------|
| CMD-1: scaffold | Ensure `--dry-run` flag is included | AUD-16, already in spec |
| CMD-4: consolidate | Ensure `--dry-run` flag is included | AUD-16, already in spec |
| ERR-1: YAML errors | Document known edge cases (BOM, `--` in content) as limitations | AUD-12 |

### No Changes Needed

- Track B (CMD-1 through CMD-7) already addresses AUD-01, AUD-02, AUD-03, AUD-04
- ERR-1 already addresses most of AUD-12
- v3.1 release cadence addresses AUD-11 stability concerns

---

## Part 5: Reviewer Consensus Analysis

### Strong Agreement (2+ reviewers)

| Topic | Reviewers | My Response |
|-------|-----------|---------------|
| **Legacy wrapper debt** | All 3 | ✅ **Addressed.** Track B eliminates this entirely. |
| **MCP placeholder confusion** | Claude, Codex | ⚠️ **Acknowledged.** v3.0.5 added FutureWarning. Full implementation is v4.0. |
| **Config fragmentation** | Claude, Codex | ✅ **Addressed.** Native commands honor `.ontos.toml`. |
| **`scaffold` broken** | Claude, Codex | ✅ **Addressed.** CMD-1 native implementation. |
| **Tests not in package** | Claude, Codex | **Deferred.** Document "run from repo" for now. v3.2 for sdist cleanup. |

### Single Reviewer Items

| Topic | Reviewer | My Response |
|-------|----------|---------------|
| **SessionContext refactor** | Claude | **Deferred.** Valid but internal. No user impact. |
| **Namespace collision** | Gemini | **Rejected.** Not a code issue. SEO/branding is ongoing. |
| **Version inflation** | Gemini | **Context provided.** v3 is real (package restructure from v2). |

### Conflicts with Research

| Audit Finding | Research Finding | Resolution |
|---------------|-----------------|------------|
| "AGENTS.md activation is fragile" (AUD-08) | §2.1 Sidecar pattern recommends metadata-first retrieval | **Research supports MCP direction.** Manual activation is bridge to v4.0 MCP server. No conflict. |
| "Frontmatter parsing edge cases" (AUD-12) | §5.1.2 Schema validation is critical | **Research amplifies priority.** ERR-1 in v3.1, full robustness in v3.2. |

---

## Part 6: Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| AUD-05 | MCP deferral allows competitors to ship first | Medium | Medium | FutureWarning communicates intent. CLI remains differentiator. v4.0 target is public. |
| AUD-08 | Manual activation loses to zero-config competitors | Medium | Medium | Ontos targets "opinionated curation" users who accept friction. MCP v4.0 provides alternative. |
| AUD-09 | Contributors can't easily run tests | Low | Low | Document "clone repo, run pytest" workflow. |
| AUD-12 | Frontmatter parsing breaks on edge cases | Low | Medium | ERR-1 catches most errors. Document limitations. Comprehensive fix in v3.2. |
| AUD-14 | SessionContext grows more complex over time | Low | Low | Internal tech debt. Schedule refactor for v3.2. |

---

## Part 7: Verdict

**Audit Status: SUBSTANTIALLY ADDRESSED**

### Coverage Summary

| Category | Addressed | Deferred | Rejected |
|----------|-----------|----------|----------|
| **Critical (P0)** | 4 | 0 | 0 |
| **Important (P1)** | 2 | 7 | 1 |
| **Minor (P2)** | 0 | 4 | 0 |

### Key Findings

1. **All 3 reviewers** agree legacy wrapper debt is the top issue → **Fully addressed** by Track B
2. **MCP concerns** from 2 reviewers → **Appropriately deferred** to v4.0 with FutureWarning
3. **Research validates** our architectural choices (frontmatter, dependency graphs, sidecar pattern)
4. **No spec amendments required** except minor additions (`doctor -v`)

### Final Recommendation

**Proceed with v3.1.0 Implementation Spec v1.0.**

Minor amendment: Add `ontos doctor -v` verbose output (AUD-07).

All critical audit findings (AUD-01 through AUD-04) are addressed by Track B native command migration.

---

## Part 8: Deferred Items Backlog

### v3.2 Candidates

| ID | Item | Source | Effort |
|----|------|--------|--------|
| AUD-06 | Schema 3.0 field implementation | Claude audit | Medium |
| AUD-09 | Tests in sdist or separate package | Claude, Codex | Low |
| AUD-12 | Full frontmatter parsing robustness | Codex audit | Medium |
| AUD-13 | Versioned documentation (ReadTheDocs) | Codex audit | Medium |
| AUD-14 | SessionContext refactor | Claude audit | Medium |
| AUD-15 | Complete type hints | Claude audit | Low |
| AUD-16 | `--dry-run` on remaining commands | Claude audit | Low |
| RES-01 | `intent` field in schema | Research review | Low |
| RES-02 | `--format xml` flag | Research review | Medium |
| RES-03 | Hash verification for staleness | Research review | Medium |

### v4.0 Candidates

| ID | Item | Source | Effort |
|----|------|--------|--------|
| AUD-05 | MCP server implementation | Claude, Codex | High |
| AUD-08 | Programmatic activation (replaces AGENTS.md) | Claude audit | High |
| RES-04 | Navigator pattern (cheap model filter) | Research review | High |
| RES-05 | Automated metadata refresh GitHub Action | Research review | Medium |

---

*Chief Architect Audit Triage — v3.1.0*
*Claude Opus 4.5 — 2026-01-21*
