# Ontos Foundation Issues - Revision Request

**Context:** These issues were identified during a code and documentation review of Project Ontos. Please address each issue and regenerate the affected files.

---

## Issue 1: YAML Template Syntax Error

### Problem

In `docs/template.md`, the frontmatter uses bracket notation for options:

```yaml
status: [draft | active | deprecated]
type: atom # Options: [kernel, strategy, product, atom]
```

YAML parsers interpret `[draft | active | deprecated]` as a **list containing one string**, not as documentation of valid options. This causes the `generate_context_map.py` script to misparse the template file itself.

### Evidence

The current `CONTEXT_MAP.md` shows the template's status as:

```
Status: ['draft | active | deprecated']
```

This demonstrates the YAML is being parsed incorrectly.

### Required Fix

Update `docs/template.md` to use actual default values with inline comments:

```yaml
---
id: unique_slug_name  # REQUIRED. Stable ID. Never change this.
type: atom            # REQUIRED. Options: kernel, strategy, product, atom
status: draft         # Optional. Options: draft, active, deprecated
owner: null           # Optional. Role responsible for this doc.
depends_on: []        # List of dependency IDs. Example: [auth_flow, user_model]
---
```

Also update any documentation (README, Manual, DEPLOYMENT) that shows the bracket notation as an example.

---

## Issue 2: Documentation Overlap and Confusion

### Problem

Four documents explain the same system with overlapping but inconsistent content:

| Document | Apparent Purpose | Structure Used |
|----------|------------------|----------------|
| README.md | Quick start + overview | Implicit phases, emoji headers |
| DEPLOYMENT.md | Installation guide | Numbered sections 1-6 |
| AGENT_INSTRUCTIONS.md | System prompt for agents | Numbered sections 1-4 |
| The Manual (20251124) | Full protocol reference | Phase 0-5 |

### Specific Conflicts

1. **Phase numbering mismatch:**
   - README says "Phase 1: Context Discovery" 
   - Manual says "Phase 1: The Architect (Initialization)"
   
2. **Missing content:**
   - Manual includes "Phase 0: Future-Proof Setup" that doesn't appear in other docs
   
3. **Duplication:**
   - AGENT_INSTRUCTIONS duplicates rules from both README and Manual
   - DEPLOYMENT repeats workflow explanations from README

### Questions for Clarification

1. Should the Manual be the single source of truth, with other docs referencing it?
2. Should AGENT_INSTRUCTIONS.md be a minimal, self-contained system prompt (no phases, just behavioral rules)?
3. Can DEPLOYMENT.md content be merged into the Manual as an appendix, or should it remain separate?

### Proposed Documentation Hierarchy

```
README.md              → Marketing/overview only (what + why, links to other docs)
DEPLOYMENT.md          → Step-by-step installation (how to set up)
AGENT_INSTRUCTIONS.md  → Minimal system prompt (rules only, no explanatory prose)
Manual                 → Full reference (all phases, theory, rationale)
```

Each document should have a clear, non-overlapping purpose. Cross-reference rather than duplicate.

---

## Issue 3: Activation Phrase Fragmentation

### Problem

Across all documents, these activation phrases appear for the same actions:

**For starting a session:**
- "Activate Ontos"
- "Ontos Activate"
- "Ontos"

**For ending/archiving:**
- "Archive this session"
- "We are done"
- "Archive Ontos"
- "Ontos archive"
- "Archive our session"
- "We are done. Archive our decisions."

This fragmentation creates ambiguity. An AI agent might not recognize all variants, or users might use a phrase that isn't documented in the agent's instructions.

### Required Fix

Standardize to exactly **2 phrases per action** (one primary, one alternate):

| Action | Primary Phrase | Alternate Phrase |
|--------|----------------|------------------|
| Start session | `Ontos` | `Activate Ontos` |
| Archive session | `Archive Ontos` | `Ontos archive` |

**Remove all other variants** from all documentation files, including:
- `.cursorrules`
- `AGENT_INSTRUCTIONS.md`
- `README.md`
- `DEPLOYMENT.md`
- The Manual

---

## Deliverables Requested

Please regenerate the following files with the issues above addressed:

1. **`docs/template.md`** - Corrected YAML syntax with proper default values
2. **`AGENT_INSTRUCTIONS.md`** - Minimal system prompt with standardized phrases
3. **`.cursorrules`** - Updated with standardized activation phrases
4. **`README.md`** - Deduplicated, focused on overview/marketing only
5. **`DEPLOYMENT.md`** - Deduplicated, focused on installation steps only
6. **The Manual** - Updated as the canonical reference with correct phase numbering

If consolidating documents makes more sense than fixing all separately, propose that structure instead.

---

## Additional Context

- Target platforms: Claude Code, Google Antigravity, ChatGPT Codex, Cursor (multi-agent support required)
- The `generate_context_map.py` script currently handles the YAML parsing issue with a workaround, but fixing the source template is cleaner
- This is a template/framework project, not tied to a specific implementation
