---
id: pr66_review_consolidation
type: atom
status: complete
depends_on: [agent_instruction_template_parity]
---

# Consolidated Review: PR #66 — Agent Instruction Template Parity (v3.2.3)

## Overview

This PR extracts a shared activation protocol from the monolithic `AGENTS_TEMPLATE` into a new module `ontos/commands/instruction_protocol.py`, then composes both `AGENTS.md` and `CLAUDE.md` templates from the same building blocks. The goal is parity by construction: any improvement to activation resilience automatically flows to all generated instruction files.

**Scope:** Patch release (v3.2.3) — no new CLI commands, no API changes.

**Changeset:** 6 files changed, 275 insertions, 114 deletions.

```
 ontos/commands/agents.py               | 128 +++++++++------------------------
 ontos/commands/claude_template.py      |  49 +++++++++----
 ontos/commands/export.py               |  11 ++-
 ontos/commands/export_claude.py        |  14 +++-
 ontos/commands/instruction_protocol.py | 126 +++++++++++++++++++++++++++++++++
 tests/commands/test_export_phase4.py   |  61 +++++++++++++++-
```

**Architecture verdict:** The extraction itself is clean. `instruction_protocol.py` is a leaf module with no internal dependencies beyond `dataclasses`, `re`, and `typing`. `InstructionProtocolConfig` is a frozen dataclass — good immutability hygiene. Both `agents.py` and `claude_template.py` compose from it without circular imports. The proposal's "Option A: Unified Core Template" is faithfully implemented.

---

## Verdict: BLOCK — 3 blocking issues must be fixed before merge

---

## Blocking Issues

### B-1: Regex backreference injection in `preserve_user_custom_section` [Critical]

**File:** `ontos/commands/instruction_protocol.py:121-126`

```python
return re.sub(
    r"(<!-- USER CUSTOM -->).*?(<!-- /USER CUSTOM -->)",
    f"\\1\n{custom_content}\n\\2",
    content,
    flags=re.DOTALL,
)
```

**Problem:** `custom_content` is user-authored text extracted from an existing file. It is interpolated directly into a `re.sub` replacement string. Python's `re.sub` interprets `\1`, `\2`, `\g<name>` etc. in the replacement as backreferences.

**Impact:**
- A user who writes `\1` or `\2` anywhere in their custom section gets **silent data corruption** — Python substitutes the matched group content instead of the literal text.
- A user who writes `\g<99>` triggers an `re.error` exception — the command crashes.
- This is particularly insidious because users have no reason to expect their markdown notes are being regex-processed.

**Reproduction:** Add `See \1 for details` to the USER CUSTOM block of an existing `CLAUDE.md`, then run `ontos export claude --force`. The output will contain `See <!-- USER CUSTOM --> for details` instead of the literal `\1`.

**Note:** This bug is **pre-existing** — the same `re.sub` pattern was in the old `agents.py`. However, this PR promotes it from a single code path to a shared utility used by both `AGENTS.md` and `CLAUDE.md` generation. The blast radius doubles. It must be fixed before it graduates.

**Fix:** Replace the string-interpolation replacement with a lambda:
```python
return re.sub(
    r"(<!-- USER CUSTOM -->).*?(<!-- /USER CUSTOM -->)",
    lambda m: m.group(1) + "\n" + custom_content + "\n" + m.group(2),
    content,
    flags=re.DOTALL,
)
```

---

### B-2: Section order regression in AGENTS.md [Major]

**Files:** `ontos/commands/agents.py:41-56` (`AGENTS_HEADER_TEMPLATE`) and `agents.py:232` (composition)

**Old section order (pre-PR):**
```
# AGENTS.md
  (intro)
## Trigger Phrases
## Current Project State
## What is Activation?
  ...
```

**New section order (this PR):**
```
# AGENTS.md
  (intro)
## Current Project State      ← moved up (inside AGENTS_HEADER_TEMPLATE)
## Trigger Phrases             ← moved down (starts ACTIVATION_PROTOCOL_HEAD_TEMPLATE)
## What is Activation?
  ...
```

**Cause:** `AGENTS_HEADER_TEMPLATE` (lines 41-56) includes `## Current Project State` as its final section. `ACTIVATION_PROTOCOL_HEAD_TEMPLATE` (line 20) starts with `## Trigger Phrases`. The join at line 232:

```python
content = "\n\n".join([header, activation_head, project_stats, activation_tail])
```

produces `Current Project State → Trigger Phrases`, swapping the original order.

**Why it matters for a patch release:** Any tooling or scripts that parse AGENTS.md by section order (including Cursor's `.cursorrules` transform at `agents.py:237-297`, which iterates line-by-line) may behave differently. The backward-compatibility bar for a patch release is: no visible output changes unless intentional. This one is unintentional.

**Fix options:**
1. Move `## Current Project State` out of `AGENTS_HEADER_TEMPLATE` into its own constant, and reorder the `join` to: `[header, activation_head_trigger_only, current_project_state, activation_head_rest, ...]`
2. Simpler: start the shared protocol at `## What is Activation?` (not `## Trigger Phrases`), and keep `## Trigger Phrases` as a separate composable block placed after `## Current Project State` in the AGENTS join. The CLAUDE join would place Trigger Phrases right after the CLAUDE header.

Recommendation: option (2) because it keeps the shared protocol boundaries clean — the shared block starts at the first section that is genuinely identical across both templates.

---

### B-3: Parity test only checks marker presence, not content equivalence [Major]

**File:** `tests/commands/test_export_phase4.py:188-208`

```python
shared_markers = [
    "## Trigger Phrases",
    "## What is Activation?",
    "## Ontos Activation",
    "## Re-Activation Trigger",
    "## After Context Compaction (/compact)",
    "## Session End",
    "## Quick Reference",
    "## Core Invariants",
    "# USER CUSTOM",
    "## Staleness",
    "It is **mandatory**.",
]
for marker in shared_markers:
    assert marker in agents_content
    assert marker in CLAUDE_MD_TEMPLATE
```

**Problem:** This test checks that 11 strings exist in both templates. It would pass if:
- One template had 5 activation steps and the other had 3
- The activation step text differed between templates (e.g., one says `ontos map`, the other says `ontos update`)
- The "mandatory" language was present but embedded in different surrounding text

This defeats the core value proposition of the PR: parity **by construction**. The test should verify that parity actually holds, not just that both files mention the same headings.

**Fix:** Extract the shared protocol content from both rendered templates (text between the first shared heading and the last shared heading) and assert equality:

```python
def extract_shared_protocol(content, start="## Trigger Phrases", end="## Staleness"):
    """Extract text from start marker through end of end section."""
    start_idx = content.index(start)
    end_idx = content.index(end)
    # Include everything from end marker to next ## or EOF
    rest = content[end_idx:]
    next_section = rest.find("\n## ", 1)
    if next_section == -1:
        return content[start_idx:]
    return content[start_idx:end_idx + next_section]

agents_shared = extract_shared_protocol(agents_content)
claude_shared = extract_shared_protocol(CLAUDE_MD_TEMPLATE)
assert agents_shared == claude_shared
```

This ensures that if anyone changes a word in the shared protocol, both templates reflect it — or the test fails.

---

## Should-Fix Issues (non-blocking, strongly recommended)

### S-1: Em-dash replaced with semicolon in two places

**File:** `ontos/commands/instruction_protocol.py:32,35`

**Old text (in original `AGENTS_TEMPLATE`):**
```
...request clarification—just execute the steps below.
...Do not ask—try both.
```

**New text:**
```
...request clarification; just execute the steps below.
...Do not ask; try both.
```

The em-dash (`—`, U+2014) was replaced with a semicolon (`;`). This is a visible text change in generated output. For a patch release, either restore the em-dashes or note the change explicitly in the release notes/commit message. The em-dashes carry a stronger imperative tone consistent with the "do not ask" activation language.

### S-2: Missing trailing newline in composed output

**File:** `ontos/commands/agents.py:232`

```python
content = "\n\n".join([header, activation_head, project_stats, activation_tail])
```

The old `AGENTS_TEMPLATE` ended with `\n`. The new composition via `"\n\n".join()` does not append a trailing newline. Most text editors and `git diff` treat this as a meaningful difference (the "No newline at end of file" warning). Add `+ "\n"` to the join result.

### S-3: No unit tests for `instruction_protocol.py`

There is no `tests/commands/test_instruction_protocol.py`. The three public functions — `render_activation_protocol_head`, `render_activation_protocol_tail`, and `preserve_user_custom_section` — are only exercised through integration tests in `test_export_phase4.py`.

This matters especially for B-1: after the regex fix lands, there should be dedicated tests for `preserve_user_custom_section` covering:
- Normal content preservation
- Content containing regex metacharacters (`\1`, `\g<3>`, `\n`, `$`)
- Empty custom section (returns original)
- Missing markers in existing content (returns original)
- Nested `<!-- USER CUSTOM -->` markers (see M-5)

### S-4: `"What is Ontos?"` section dropped from CLAUDE.md

The old `CLAUDE_MD_TEMPLATE` (pre-PR) included a `## What is Ontos?` section explaining the tool. The new `claude_template.py` does not include it — it was silently dropped. If intentional, note it in the commit message. If not, restore it as a CLAUDE-specific section after the shared protocol.

---

## Minor Issues (consider but not required for merge)

### M-1: Unused `CLAUDE_MD_TEMPLATE` import in `export_claude.py`

**File:** `ontos/commands/export_claude.py:11-12`

```python
from ontos.commands.claude_template import (
    CLAUDE_MD_TEMPLATE,
    generate_claude_content,
)
```

`CLAUDE_MD_TEMPLATE` is imported but never referenced in `export_claude_command`. Only `generate_claude_content` is used (line 68). Remove the unused import.

### M-2: Missing blank line between `find_repo_root` and `gather_stats` (PEP 8)

**File:** `ontos/commands/agents.py:99-102`

```python
    # No repo found - return None instead of cwd to prevent arbitrary writes
    return None

def gather_stats(repo_root: Path) -> Dict[str, str]:
```

PEP 8 requires two blank lines between top-level function definitions. There is only one blank line here.

### M-3: `preserve_user_custom_section` treats default placeholder as user content

**File:** `ontos/commands/instruction_protocol.py:117-118`

```python
custom_content = match.group(1).strip()
if not custom_content:
    return content
```

The default placeholder comment (`<!-- Add your project-specific notes below. ... -->`) is not empty after stripping, so it passes the `if not custom_content` check and gets treated as "user content" to preserve. In practice this is harmless today because the placeholder is already present in the new template. But if the placeholder text ever changes in a future version, the old placeholder will be carried forward as if the user wrote it.

### M-4: `CLAUDE_MD_TEMPLATE` evaluated at import time

**File:** `ontos/commands/claude_template.py:30-37`

```python
CLAUDE_MD_TEMPLATE = "\n\n".join(
    [
        CLAUDE_HEADER_TEMPLATE,
        CLAUDE_TOOLING_NOTES,
        render_activation_protocol_head(CLAUDE_PROTOCOL_CONFIG),
        render_activation_protocol_tail(CLAUDE_PROTOCOL_CONFIG),
    ]
)
```

This renders the template at module import time, while `AGENTS.md` content is rendered at call time via `generate_agents_content()`. The asymmetry means CLAUDE.md content is frozen at import while AGENTS.md content can pick up runtime changes (e.g., different config). Not a bug today, but a latent architectural asymmetry.

### M-5: Nested `<!-- USER CUSTOM -->` markers cause truncation

**File:** `ontos/commands/instruction_protocol.py:109-113`

If a user writes `<!-- USER CUSTOM -->` or `<!-- /USER CUSTOM -->` inside their custom content, the non-greedy `.*?` in the regex will match the *first* closing marker, truncating everything after it. Edge case, but worth a comment in the code or a note in generated output warning users not to use the marker strings.

---

## What's Good About This PR

- **The core architecture is sound.** `InstructionProtocolConfig` as a frozen dataclass is the right abstraction level — configuration without behavior.
- **Clean module boundaries.** `instruction_protocol.py` is a leaf module with no internal dependencies. No circular import risk.
- **Parity by construction** is the right strategy. The proposal correctly identified that copy-paste parity always drifts.
- **USER CUSTOM preservation** across regeneration is an important UX feature, correctly carried forward.
- **The proposal and commit history are well-documented.** Clear problem statement, options analysis, and verification plan.

---

## Required Actions (prioritized)

| Priority | Action | Issue |
|----------|--------|-------|
| **P0** | Fix `preserve_user_custom_section` to use lambda replacement | B-1 |
| **P0** | Restore AGENTS.md section order: Trigger Phrases before Current Project State | B-2 |
| **P1** | Strengthen parity test to compare shared protocol content, not just headings | B-3 |
| **P1** | Restore em-dashes (or document the change) | S-1 |
| **P1** | Append trailing newline to composed output | S-2 |
| **P2** | Add unit tests for `instruction_protocol.py` (especially regex edge cases) | S-3 |
| **P2** | Remove unused `CLAUDE_MD_TEMPLATE` import from `export_claude.py` | M-1 |
| **P3** | Fix PEP 8 blank line between `find_repo_root` and `gather_stats` | M-2 |

**After P0 and P1 fixes are applied, this is ready to merge.** No architectural concerns, no scope creep, open questions properly deferred.

---

## Open Question Resolutions (verified)

1. **`.cursorrules` re-derivation?** — Deferred. `transform_to_cursorrules` still transforms from AGENTS output. Sound decision.
2. **`ontos export --all`?** — Deferred. No new commands added. Verified.
3. **`export claude` → `agents --format claude`?** — Deferred. CLI surface unchanged. Verified.
