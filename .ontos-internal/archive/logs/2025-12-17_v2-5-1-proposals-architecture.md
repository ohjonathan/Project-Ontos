---
id: log_20251217_v2_5_1_proposals_architecture
type: log
status: active
event_type: decision
concepts: [architecture, ontology, proposals, workflow]
impacts: [v2_strategy, ontos_manual]
---

# Session Log: V2.5.1 Proposals Architecture

Date: 2025-12-17 12:45 KST
Source: Claude Opus 4.5
Event Type: decision

## 1. Goal

Design the architectural foundation for `/strategy/proposals/` - a staging area for draft strategy documents within the Ontos dual ontology framework.

## 2. Key Decisions

### Proposals as Space (Not Time)

**Question:** Where do planning documents fit in the dual ontology?
- **Time (History):** Logs - what happened
- **Space (Truth):** Strategy, atoms - what is true

**Decision:** Proposals are **Space with `status: draft`** - potential truth, not yet approved.

Rationale: Planning documents aren't about what happened (that's logs). They're about what *could become* truth. The `status` field already supports this - we're activating an underused part of the ontology.

### Directory Structure

**Decision:** `/strategy/proposals/` nested under strategy (not parallel `/planning/`)

```
.ontos-internal/
├── strategy/
│   ├── v2_strategy.md           # status: active (Truth)
│   ├── decision_history.md      # status: active (Truth)
│   └── proposals/               # status: draft (Potential)
│       └── *.md
```

Rationale: Proposals are pre-strategy, not a separate ontological category. Keeps dual ontology clean.

### Proposal Lifecycle

```
draft → approved (status: active) OR rejected (status: rejected)
```

**New status value:** `rejected` - considered but never became truth.

### Recording Rejections

**Decision:** Rejected proposals are recorded in `decision_history.md` alongside approvals.

| Date | Slug | Decision | Outcome | Archive Path |
|------|------|----------|---------|--------------|
| 2025-12-10 | auth-flow | Chose OAuth2 | ✅ APPROVED | archive/logs/... |
| 2025-12-17 | redis-cache | Redis caching | ❌ REJECTED | archive/proposals/... |

Rationale:
- Prevents re-analyzing rejected ideas without context
- Complete institutional memory (what we considered AND why we chose/rejected)
- Mirrors how human organizations record decisions

### Status Field Evolution

| Status | Meaning | Temporal State |
|--------|---------|----------------|
| `draft` | Work in progress | Potential future |
| `active` | Approved, current truth | Present |
| `deprecated` | Was true, no longer | Past truth |
| `rejected` | Considered but not approved | Never became truth |

## 3. Alternatives Considered

### Parallel `/planning/` Directory
- Would create implicit third ontological category
- Rejected: Breaks clean dual ontology, adds complexity

### Separate `rejection_history.md`
- Clear separation of approvals and rejections
- Rejected: Two files to maintain, might be forgotten

### Planning as Time (Extended Exploration Logs)
- Treat proposals as multi-session exploration logs
- Rejected: Planning isn't about what happened, it's about potential futures

## 4. Impact Analysis

### v2.5.1 (Current)
- ✅ Create `/strategy/proposals/` directory
- ✅ Add proposal docs with proper frontmatter
- Document in Manual
- Add `proposal` to Common_Concepts.md

### v2.5.2 (Follow-up)
- Context map: show `[draft]` indicator
- Lint: stale proposal warning (>60 days)
- Validation: skip orphan check for drafts

### v2.6 (Feature Release)
- Context map: optional PROPOSALS section
- `ontos_end_session.py --proposal` flag
- `ontos_reject_proposal.py` tooling
- `status: rejected` with metadata
- S3 archive integration (separate feature)

## 5. Breaking Changes

**None.** This is purely additive:
- Existing docs work unchanged
- Existing workflows work unchanged
- Proposals are opt-in
- `status: draft` already exists in schema

## 6. Critical Finding: Dual-Mode Gap

During this session, we discovered a critical issue: **v2.x features have been developed and tested primarily in contributor mode, with significant gaps in user mode.**

### Issues Found
- `ontos_init.py` doesn't create complete directory structure for users
- Path helpers have inconsistent structure (nested vs flat)
- Missing starter files (decision_history.md, Common_Concepts.md)
- Features silently fail in user mode

### Root Cause
Dogfooding bias - we develop Ontos using Ontos (contributor mode), so user mode is never tested.

### Resolution
Created comprehensive remediation plan: `v2.5.2_dual_mode_remediation.md`

## 7. Next Steps

- Review remediation plan with LLM colleagues (Claude, Codex, Gemini)
- Implement v2.5.2 fixes before v2.6 features
- Add user-mode testing to CI pipeline
- Review v2.6 proposals after v2.5.2 is stable

---
## Raw Session History
```text
Architectural discussion between Jonathan and Claude Opus 4.5.
Key insight #1: "We're not changing the ontology - we're activating an underused part of it."
Key insight #2: "v2.x has been developed in contributor mode only - user mode has critical gaps."
```
