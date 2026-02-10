---
id: agent_instruction_template_parity
type: strategy
status: complete
depends_on: []
---

# Proposal: Agent Instruction Template Parity

**Date:** 2026-02-10
**Author:** Antigravity (Gemini 2.5 Pro)
**Target Version:** v3.2.3

---

## Problem

Claude CLI does not automatically execute the Ontos activation ritual at session start, even though `CLAUDE.md` is present in the repository root and correctly placed. However, **Codex consistently does** — every session, it runs map regeneration + context load before touching the user's task.

The symptom: Claude CLI skips straight to the user's request, never runs `ontos map`, never reads the context map, and reports "my MEMORY.md is empty" — confusing its own persistence file with the project's instruction file.

## Root Cause

The problem is not in the tooling (Claude CLI reads `CLAUDE.md` correctly) — it's in **what the template says**.

Ontos currently maintains **two divergent templates** with dramatically different activation language:

### `AGENTS_TEMPLATE` (works — Codex follows it)

```markdown
## What is Activation?
Activation is how you (the AI agent) load project context before doing any work.
It is **mandatory**. Do not ask "why" or request clarification—just execute the steps below.
```

Also includes: trigger phrases, re-activation triggers, post-compaction recovery, staleness warnings.

### `CLAUDE_MD_TEMPLATE` (fails — Claude CLI ignores it)

```markdown
## Ontos Activation

This project uses **Ontos** for documentation management.

At the start of every session:
1. Run `ontos map` to generate the context map
2. Read `Ontos_Context_Map.md` to understand the project documentation structure
```

No mandatory language. No trigger phrases. No re-activation logic. No "do not skip" directive.

### The Gap

| Feature | `AGENTS_TEMPLATE` | `CLAUDE_MD_TEMPLATE` |
|---------|-------------------|---------------------|
| "Mandatory" directive | ✅ | ❌ |
| "Do not ask why" language | ✅ | ❌ |
| Trigger phrases | ✅ | ❌ |
| Re-activation triggers | ✅ | ❌ |
| Post-compaction recovery | ✅ | ❌ |
| Project stats (doc count, branch) | ✅ | ❌ |
| Quick reference table | ✅ | ❌ |
| Core invariants | ✅ | ❌ |
| Staleness warning | ✅ | ❌ |
| USER CUSTOM section | ✅ | ❌ |

The `CLAUDE_MD_TEMPLATE` was written as a minimal stub. It was never upgraded to match the activation resilience patterns that were developed for v3.2 `AGENTS.md`.

## Why It Matters

The whole point of v3.2's "activation resilience" theme was to make Ontos activation stick across sessions and agents. If `ontos export claude` produces a weak instruction file, 50% of the multi-agent story is broken. Every user who uses Claude CLI alongside other tools will hit this — and the fix is to update individual repos' `CLAUDE.md` files by hand, which defeats the purpose of having a generator.

## Proposed Solution

### Option A: Unified Core Template (Recommended)

Extract a **shared activation protocol block** and have both `AGENTS_TEMPLATE` and `CLAUDE_MD_TEMPLATE` compose from it. This ensures parity by construction — any improvement to activation resilience automatically flows to all generated instruction files.

```
ACTIVATION_PROTOCOL (shared)
    ├── AGENTS_TEMPLATE  = AGENTS.md header + ACTIVATION_PROTOCOL + agents-specific sections
    ├── CLAUDE_TEMPLATE   = CLAUDE.md header + ACTIVATION_PROTOCOL + claude-specific sections
    └── CURSOR_TEMPLATE   = derived via transform_to_cursorrules()
```

**Files to modify:**
- `ontos/commands/agents.py` — Extract shared protocol block from `AGENTS_TEMPLATE`
- `ontos/commands/claude_template.py` — Rewrite to compose from shared protocol
- `tests/test_cli.py` or new test file — Verify both templates contain mandatory activation language

**Shared protocol block would include:**
- Trigger phrases
- "What is Activation?" with mandatory language
- Activation steps (5-step sequence)
- Re-activation triggers
- Post-compaction recovery
- Session end protocol
- Quick reference table
- Core invariants
- Staleness warning
- USER CUSTOM section preservation

**Tool-specific sections:**
- `AGENTS.md`: Current Project State table (auto-synced stats)
- `CLAUDE.md`: Any Claude-specific affordances (e.g., `MEMORY.md` guidance)

### Option B: Copy-Paste Parity (Simpler, Less Maintainable)

Simply copy the full `AGENTS_TEMPLATE` content into `CLAUDE_MD_TEMPLATE`, changing only the header from `# AGENTS.md` to `# CLAUDE.md`. Quick fix, but creates two templates that can drift again.

### Recommendation

**Option A.** The whole lesson here is that two templates drifted because they weren't structurally linked. The fix should make drift impossible, not just unlikely.

## Verification Plan

1. Run `ontos agents --force` and `ontos export claude --force` in the Ontos-dev repo
2. Diff the activation sections — they should be identical
3. Add a test that asserts both generated files contain the string `"It is **mandatory**"`
4. Manual test: start a fresh Claude CLI session in a repo with the new `CLAUDE.md` and verify it runs activation unprompted

## Open Questions

1. **Should `.cursorrules` also be re-derived from the shared protocol?** Currently it's transformed from `AGENTS.md` content via `transform_to_cursorrules()`. If we extract a shared protocol, the transform should operate on that instead.
2. **Should we add a `ontos export` subcommand that generates all instruction files at once?** (e.g., `ontos export --all` → writes `AGENTS.md`, `CLAUDE.md`, `.cursorrules`)
3. **Naming: should we rename `export claude` to `agents --format claude`?** The current CLI surface has both `ontos agents` and `ontos export claude` doing similar things through different code paths. Consolidation may be warranted.
