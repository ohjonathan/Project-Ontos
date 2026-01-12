# Obsidian compatibility guide for external markdown generators

**Project Ontos can achieve full Obsidian compatibility by following specific file encoding, YAML frontmatter, and link syntax conventions.** The key requirements are UTF-8 encoding, valid YAML frontmatter at file start, and consistent internal link formatting. Obsidian's local-first architecture means it simply reads standard markdown files from disk—no proprietary database or special registration required. External tools that generate properly formatted `.md` files will integrate seamlessly with Obsidian's graph view, backlinks, search, and properties features.

## Core file requirements for Obsidian compatibility

Obsidian's file handling is straightforward but has several non-negotiable requirements that external generators must follow.

**Encoding and format specifications:**
- **UTF-8 encoding is mandatory**—Obsidian only reads/writes UTF-8; non-UTF-8 files cause character corruption
- File extension must be `.md` (`.markdown` not natively supported)
- Line endings: LF preferred, but CRLF accepted
- BOM not required (UTF-8 without BOM preferred)

**Filename restrictions vary by platform:**

| Platform | Forbidden Characters |
|----------|---------------------|
| All platforms | `[ ] # ^ |` and filenames cannot start with `.` |
| macOS/iOS/Linux | `\ / :` |
| Windows | `* " \ / < > : | ?` |

The restrictions on `[ ] # ^ |` exist because these characters conflict with Obsidian's wikilink syntax. Maximum filename length is approximately **252 characters** (OS-dependent, accounting for `.md` extension).

**Vault structure:** A vault is simply any folder containing markdown files. When opened in Obsidian, it creates a `.obsidian` configuration folder. No enforced hierarchy exists—Obsidian works with flat structures or deep nesting equally well. The key constraint: **never create vaults within vaults**, as this breaks internal link resolution.

## YAML frontmatter parsing and the Properties feature

Obsidian parses YAML frontmatter using standard YAML 1.1/1.2 specifications with specific constraints that Project Ontos must follow.

**Frontmatter placement rules:**
- Must be at the **absolute top** of the file—no whitespace or content can precede it
- Must start with `---` on line 1
- Must end with `---` on its own line
- Uses spaces for indentation (tabs cause parsing errors)

**Natively recognized properties (as of Obsidian 1.9):**

| Property | Type | Purpose |
|----------|------|---------|
| `tags` | List | Note categorization; supports nested tags like `project/ontos` |
| `aliases` | List | Alternative names for linking (enables `[[Full Title|Alias]]`) |
| `cssclasses` | List | CSS classes for styling individual notes |

The singular forms (`tag`, `alias`, `cssclass`) are deprecated—Obsidian's Properties editor auto-converts them to plural forms.

**Property types supported by the Properties UI:**
- **Text**: Free-form strings (`author: "Ada Lovelace"`)
- **List**: Multiple values (`tags: [a, b, c]`)
- **Number**: Integers and decimals (`rating: 8.5`)
- **Checkbox**: Boolean (`completed: true`)
- **Date**: ISO 8601 format (`created: 2023-08-11`)
- **DateTime**: Date with time (`modified: 2023-08-11T06:16`)

**Critical syntax requirements:**
```yaml
---
title: "Value with: colon"           # Quotes required for special chars
tags: [project, documentation]       # Inline array format
aliases:                             # Block list format
  - Project Ontos
  - Ontos Documentation
link: "[[Related Note]]"             # Wikilinks in YAML require quotes
created: 2025-01-11                  # ISO 8601 date format
---
```

**Malformed YAML behavior:** Invalid YAML displays an error in the Properties UI but the note remains functional—only metadata parsing fails. Common errors include tabs instead of spaces, missing quotes around special characters, and incorrect indentation.

## Wikilink syntax specification and link resolution

Obsidian supports two link formats: wikilinks (default) and standard markdown links. Understanding both is essential for Project Ontos compatibility.

**Complete wikilink syntax:**

```markdown
[[filename]]                    # Basic link (extension optional)
[[filename|display text]]       # Custom display text
[[filename#Heading]]            # Link to specific heading
[[filename#Heading#Subheading]] # Nested heading chain
[[filename^block-id]]           # Block reference
![[filename]]                   # Embed entire note
![[filename#Heading]]           # Embed specific section
![[image.png]]                  # Embed image (extension required for non-md)
```

**Link resolution mechanics:**
- Resolution is **case-insensitive**: `[[mynote]]` matches `MyNote.md`
- Shortest unique path used by default—full path only when duplicates exist
- Links to non-existent files display "faded out" and **clicking creates the note**
- Automatic link updates when files are moved/renamed (configurable setting)

**Block references** use alphanumeric IDs defined at the end of content blocks:
```markdown
This is a paragraph. ^my-block-id

> Quote text here

^quote-id
```
Block IDs must contain only **Latin letters, numbers, and dashes**.

**Markdown links alternative:**
```markdown
[Display Text](Note%20Name.md)        # Spaces require URL encoding
[Display Text](path/to/note.md#heading)
![alt text](image.png)
```

**Compatibility tradeoff:** Wikilinks offer better Obsidian integration (automatic rename updates, backlinks panel) but are Obsidian-specific. Standard markdown links provide universal portability but require URL encoding for spaces.

## How backlinks and the graph view compute relationships

The graph view and backlinks are powered by Obsidian's **MetadataCache**—an IndexedDB-backed index that parses all markdown files in the vault.

**Backlinks system:**
- **Linked mentions**: Explicit `[[wikilink]]` references are automatically tracked
- **Unlinked mentions**: Plain text matching note titles (including aliases) detected automatically
- Backlinks update **effectively in real-time** as you edit
- Cache rebuilds automatically; manual rebuild available via Settings → Files and links → Rebuild metadata cache

**Graph view data model:**

| Node Type | Description | How to Enable |
|-----------|-------------|---------------|
| Notes | Any `.md` file in vault | Always shown |
| Tags | Tags from notes | Toggle "Tags" filter |
| Attachments | Images, PDFs, etc. | Toggle "Attachments" filter |
| Unresolved links | Links to non-existent notes | Disable "Existing files only" |

**What creates edges (connections):**
- Wikilinks: `[[Note]]` creates edge from source to target
- Markdown links: `[text](note.md)` if resolved to internal note
- Embeds: `![[Note]]` creates connection
- Shared tags: When Tags filter enabled, notes connect through tag nodes

**NOT counted as connections:** Plain text mentions, links in code blocks, external URLs, or frontmatter property values (unless using `[[link]]` syntax in quoted strings).

**Minimum viable file for graph appearance:**
```markdown
# Empty Note
```
Even an empty `.md` file appears as an orphan node. For connections, include at least one internal link.

## Tags: inline syntax and hierarchical organization

Obsidian's tag system supports both inline tags and frontmatter-defined tags, with full hierarchical nesting.

**Inline tag syntax rules:**
- Must be preceded by whitespace or start of line
- Valid characters: `A-Z`, `a-z`, `0-9`, `_`, `-`, `/`
- Must contain **at least one non-numerical character**
- Forward slash `/` creates hierarchy: `#project/ontos/subtopic`

**Frontmatter tags:**
```yaml
tags:
  - project
  - project/ontos          # Nested tag
  - documentation
```
In frontmatter, omit the `#` prefix—use `project` not `#project`.

**Hierarchical tag behavior:**
- Searching parent tag **includes all child tags** (searching `#project` finds `#project/ontos`)
- Tags View displays collapsible hierarchy with aggregate counts
- Graph view shows nested tags as **separate nodes** (no built-in hierarchy visualization—requires community plugins)

**Tags are case-insensitive** in search and the Tags View, though some edge cases exist with graph view display.

## Search operators and indexing behavior

Obsidian's search uses both full-text indexing and structured metadata queries.

**Key search operators:**

| Operator | Example | Function |
|----------|---------|----------|
| `tag:` | `tag:#project` | Search tags (faster than `#project`) |
| `path:` | `path:"Daily Notes"` | Search by file path |
| `file:` | `file:".jpg"` | Search filename |
| `content:` | `content:keyword` | Search body only |
| `line:(...)` | `line:(foo bar)` | Terms on same line |
| `section:(...)` | `section:(foo bar)` | Terms in same heading section |
| `[property]` | `[status]` | Notes containing property |
| `[property:value]` | `[status:done]` | Notes with specific property value |

**Boolean operators:** Space = AND, `OR` explicit, `-` for negation, parentheses for grouping. Regular expressions supported via `/pattern/` syntax.

**External file change detection:**
- Obsidian monitors filesystem for external modifications via file watcher
- Changes typically detected within seconds (may require window focus on Windows/Linux)
- If file is open during external edit, may need to close/reopen to see changes
- "Force reload" command available for manual refresh

## Technical architecture and the MetadataCache API

Understanding Obsidian's internals helps Project Ontos generate optimally compatible files.

**Platform stack:**
- **Desktop**: Electron v34.3.0 with CodeMirror 6 editor
- **Mobile**: Capacitor v5.x
- **Data storage**: Plain text files with IndexedDB-cached metadata

**MetadataCache structure (what Obsidian indexes per file):**
- `frontmatter`: Parsed YAML properties
- `frontmatterLinks`: Wikilinks found in frontmatter (added v1.4)
- `headings`: Array of heading positions and levels
- `links`: Array of internal link references
- `embeds`: Embedded content references
- `tags`: Tag occurrences
- `blocks`: Block reference definitions

**Obsidian Flavored Markdown extends CommonMark/GFM with:**
- Wikilinks: `[[note]]`, `[[note|alias]]`
- Embeds: `![[note]]`
- Block references: `^block-id`
- Highlights: `==text==`
- Callouts: `> [!note]`
- Comments: `%%hidden%%`

**No formal parser specification exists**—the parser is proprietary. Third-party tools like `obsidian-export` (Rust) and `mdformat-obsidian` (Python) provide external parsing capabilities.

## Community organizational patterns

Understanding common Obsidian usage patterns helps Project Ontos generate files that align with user expectations.

**MOC (Maps of Content):** Hub notes containing links to related notes, functioning as dynamic tables of contents. No strict naming convention—common patterns include `Topic MOC.md` or dedicated `/MapsOfContent/` folder.

**PARA system folders:**
```
/Projects/    - Active, time-bound projects
/Areas/       - Ongoing responsibilities  
/Resources/   - Reference materials
/Archives/    - Completed/inactive items
```

**Dominant philosophy:** Most Obsidian users prefer **link-first organization** over rigid folder hierarchies, using flat structures with navigation via links and search rather than folder drilling.

**Zettelkasten conventions:** Date-prefixed UIDs (`202501111322 Note Title.md`) exist but many users find them unnecessary—Obsidian's metadata already tracks creation dates, and descriptive filenames improve link readability.

## Complete compatibility checklist for Project Ontos

**File requirements:**
- ✅ UTF-8 encoding (no BOM)
- ✅ `.md` extension
- ✅ LF line endings
- ✅ No forbidden characters: `[ ] # ^ | : ? * / \ < > "`
- ✅ Filename ≤ 252 characters

**Frontmatter:**
- ✅ Valid YAML at absolute top of file
- ✅ Delimited by `---` lines
- ✅ Space after colons in key-value pairs
- ✅ Tags without `#` prefix
- ✅ Special characters in values quoted
- ✅ Wikilinks in YAML quoted: `"[[Note]]"`

**Links:**
- ✅ Choose format: wikilinks `[[note]]` OR markdown `[text](note.md)`
- ✅ Consistent format throughout vault
- ✅ Heading links use `#` syntax
- ✅ Asset paths relative to vault or note location

**For graph visualization:**
- ✅ Include `[[internal links]]` between related documents
- ✅ Use consistent `tags` in frontmatter for topic clustering
- ✅ Consider MOC-style hub documents for hierarchical navigation

**Example Ontos-generated file:**
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

## Module structure

The system consists of three primary modules...

See also: [[API Reference]], [[Configuration Guide]]
```

This structure ensures the file appears correctly in Obsidian's graph view (connected to linked notes), Properties panel (displaying all frontmatter), backlinks (tracking all references), and search (indexing all content and metadata).