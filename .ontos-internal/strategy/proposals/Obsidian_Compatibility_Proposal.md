---
id: obsidian_compatibility_proposal
type: strategy
status: draft
depends_on: [v3_0_implementation_roadmap]
concepts: [obsidian, wikilinks, graph-view, backlinks, interoperability]
---

# Chief Architect Briefing: Obsidian Compatibility Feature

**To:** Chief Architect (Claude Opus 4.5)
**From:** Research Assistant
**Date:** 2026-01-13
**Subject:** Obsidian Compatibility - Historical Context, Research Materials, and Implementation Gap

---

## 1. Executive Summary

**Situation:** Obsidian compatibility was researched and planned for v2.9.7 but was never implemented. The project pivoted directly from v2.9.6 to v3.0, and this feature fell through the cracks. The user has now requested a detailed implementation specification.

**Current State:**
- 314 markdown files exist in Project Ontos
- 297 files have valid YAML frontmatter (structurally compatible)
- Files use standard markdown links `[text](path.md)` instead of Obsidian wikilinks `[[note]]`
- Files use `concepts: []` instead of Obsidian's `tags: []`
- No `aliases` field support
- **Result:** Files open in Obsidian but don't leverage graph view, backlinks, or tag features

**Chief Architect Tasks:**
1. Determine where this feature belongs in the v3.x roadmap
2. Design implementation approach based on current codebase architecture
3. Write a detailed implementation specification

---

## 2. Historical Context: The v2.9.7 Gap

### 2.1 What Happened

| Version | Date | Obsidian Status |
|---------|------|-----------------|
| v2.9.6 | 2026-01-12 | **Explicitly deferred** to v2.9.7 (see Section 3.1) |
| v2.9.7 | — | **Never created** |
| v3.0 | 2026-01-12+ | No mention of Obsidian in 1,174-line roadmap |

### 2.2 The Deferral Decision

In `v2.9.6_Implementation_Specification.md`, line 62, under "OUT of Scope (Cut List)":

```
| Feature                      | Reason           | Deferred To |
|------------------------------|------------------|-------------|
| Obsidian wikilink generation | Separate feature | v2.9.7      |
```

**Rationale at the time:** v2.9.6 was focused solely on "Ontology Architecture" - creating a single source of truth for type/field definitions via `ontology.py`. Obsidian compatibility was considered a separate concern.

### 2.3 Why v2.9.7 Never Happened

The project immediately pivoted to v3.0 ("Distribution & Polish") which focused on:
- `pip install ontos` distribution model
- God Script decomposition (breaking 3,199 lines into modules)
- CLI completion and `.ontos.toml` configuration
- MCP preparation for v4.0

Obsidian compatibility was simply not carried forward into the v3.0 planning documents.

---

## 3. Core Reference Materials

### 3.1 Primary Research Document

**File:** `.ontos-internal/archive/v2.9.6/Obsidian_Compatibility.md`

This 294-line document contains comprehensive research on Obsidian compatibility requirements:

| Section | Content |
|---------|---------|
| Core file requirements | UTF-8 encoding, filename restrictions, vault structure |
| YAML frontmatter parsing | Property types, syntax requirements, natively recognized fields |
| Wikilink syntax | Complete syntax spec including block references, embeds |
| Backlinks & graph view | How MetadataCache computes relationships |
| Tags system | Inline syntax, hierarchical organization |
| Search operators | Indexing behavior, property queries |
| Complete compatibility checklist | File requirements, frontmatter, links, graph visualization |

**Key Example from Document (lines 270-292):**
```markdown
---
title: Component Architecture
created: 2025-01-11T14:30:00
tags:
  - ontos/architecture
  - documentation
aliases:
  - Architecture Overview
parent: "[[System Documentation]]"
---

# Component architecture

This document describes the core components of [[Project Ontos]].

See also: [[API Reference]], [[Configuration Guide]]
```

### 3.2 Original Deferral Source

**File:** `.ontos-internal/archive/v2.9.6/v2.9.6_Implementation_Specification.md`

- Line 62: Obsidian deferred to v2.9.7
- Status: `complete` (v2.9.6 shipped without Obsidian)

### 3.3 Current Roadmap (No Obsidian Mention)

**File:** `.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md`

- 1,174 lines covering Phases 0-5, v3.1.x, v3.2.x+
- Zero mentions of "obsidian", "wikilink", or `[[`
- v3.1.0 "Bridge Features" section has open slots

---

## 4. Current Codebase Compatibility Analysis

### 4.1 What's Already Compatible

| Requirement | Current State | Compatible? |
|-------------|---------------|-------------|
| UTF-8 encoding | ✅ All files UTF-8 | Yes |
| `.md` extension | ✅ Standard | Yes |
| YAML frontmatter | ✅ 297/314 files have valid frontmatter | Yes |
| Frontmatter at top | ✅ Correct placement | Yes |
| `---` delimiters | ✅ Standard YAML | Yes |

### 4.2 What's NOT Compatible

| Requirement | Current State | Gap |
|-------------|---------------|-----|
| Internal links | `[text](path.md)` | Need `[[wikilinks]]` |
| Tags | `concepts: []` | Need `tags: []` |
| Aliases | Not present | Need `aliases: []` |
| Graph connections | None (standard links not indexed) | Need wikilinks |
| Backlinks | None | Need wikilinks |

### 4.3 Ontos Frontmatter Schema vs Obsidian

| Ontos Field | Obsidian Equivalent | Mapping Strategy |
|-------------|---------------------|------------------|
| `id` | (none - Obsidian uses filename) | Keep as custom property |
| `type` | (none) | Keep as custom property |
| `status` | (none) | Keep as custom property |
| `depends_on` | (none - use wikilinks) | **Convert to wikilinks in body?** |
| `concepts` | `tags` | **Map directly** |
| `impacts` | (none - use wikilinks) | Keep as custom property |

---

## 5. Previously Suggested Solution (from Research Doc)

The research document (Section "Complete compatibility checklist") suggests:

### 5.1 File-Level Changes
- Ensure UTF-8, LF line endings, no forbidden characters ✅ (already met)

### 5.2 Frontmatter Changes
- Add `tags:` field (map from `concepts:`)
- Add `aliases:` field for alternative linking names
- Quote any wikilinks in YAML: `parent: "[[Note]]"`

### 5.3 Link Format Changes
- Convert internal links from `[text](path.md)` to `[[note]]` or `[[note|display text]]`
- Consistent format throughout vault

### 5.4 Graph Visualization
- Include `[[internal links]]` between related documents
- Use consistent tags for topic clustering
- Consider MOC-style hub documents (Context Map as MOC?)

---

## 6. Open Questions for Chief Architect

### 6.1 Roadmap Placement

| Option | Pros | Cons |
|--------|------|------|
| v3.1.0 (Bridge Features) | Aligns with "Prepare for Protocol" theme; has open slots | May delay MCP prep work |
| v3.2.0+ (Protocol Prep) | Lower priority, less time pressure | Further delay |
| v3.0.x patch | Could ship sooner | Scope creep risk for v3.0 |
| Separate v3.0.x feature flag | Optional, user-enabled | Complexity |

### 6.2 Implementation Scope

**Minimal Scope:**
- Map `concepts` → `tags` in frontmatter
- Add `aliases` field support
- Generate wikilinks in Context Map output

**Medium Scope:**
- All of minimal, plus:
- Convert `depends_on` references to wikilinks in document body
- Add `--obsidian` flag to `ontos map` command

**Full Scope:**
- All of medium, plus:
- Retrofit existing `.ontos-internal/` documents
- Add `ontos export --format obsidian` command
- Obsidian vault initialization (`ontos init --obsidian`)

### 6.3 Breaking Changes

| Change | Breaking? | Mitigation |
|--------|-----------|------------|
| Add `tags` field | No | Additive |
| Add `aliases` field | No | Additive |
| Change link format | **Potentially** | Flag-based opt-in? |
| Modify Context Map output | **Yes** | Version flag? |

### 6.4 Affected Files (Current Architecture)

Based on v3.0 package structure, likely affected modules:

| Module | Purpose | Obsidian Impact |
|--------|---------|-----------------|
| `ontos/core/frontmatter.py` | Frontmatter parsing/generation | Add tags/aliases mapping |
| `ontos/commands/map.py` | Context map generation | Wikilink output format |
| `ontos/io/files.py` | File I/O | Encoding verification |
| `ontos/core/config.py` | Configuration | Obsidian mode flag |

---

## 7. Recommended Next Steps

1. **Chief Architect Decision:** Where does this belong in the roadmap?
2. **Scope Decision:** Minimal, Medium, or Full implementation?
3. **Specification:** Write detailed implementation spec with:
   - Exact frontmatter field mappings
   - Link conversion rules
   - CLI flag design (`--obsidian`? config file?)
   - Migration path for existing documents
   - Test strategy

---

## 8. Reference File Paths

| Document | Path |
|----------|------|
| Obsidian Research | `.ontos-internal/archive/v2.9.6/Obsidian_Compatibility.md` |
| v2.9.6 Spec (deferral) | `.ontos-internal/archive/v2.9.6/v2.9.6_Implementation_Specification.md` |
| v3.0 Roadmap | `.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md` |
| v3.0 Architecture | `.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md` |
| Current Context Map | `Ontos_Context_Map.md` |
| Frontmatter module | `ontos/core/frontmatter.py` |

---

*End of Briefing*
