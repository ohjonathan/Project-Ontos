---
id: ontos_claude_code_skill_proposal
type: strategy
status: draft
depends_on: [ontos_manual, ontos_agent_instructions]
---

# Plan: Ontos Claude Code Skill

## Summary

Create a global Claude Code skill that auto-activates Ontos context when detecting Ontos project markers. The skill will be built using the `skill-creator` plugin (already installed) and packaged as a distributable `.skill` file.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scope | Global (`~/.claude/skills/ontos/`) | User preference; works across all repos |
| Auto-invoke | Yes | Triggers on `Ontos_Context_Map.md`, `.ontos-internal/`, `AGENTS.md` detection |
| Build Tool | `skill-creator` plugin | Proper tooling with validation, packaging, best practices |
| Distribution | `.skill` file + optional PyPI bundling | Users can install manually or via future `ontos skill install` |
| Commands | **Open for LLM review board** | See candidate list below |

## Skill Creation Workflow

Using `skill-creator` from the `document-skills` plugin:

```bash
# 1. Initialize skill scaffold
python3 ~/.claude/plugins/cache/anthropic-skills/document-skills/*/scripts/init_skill.py ontos --path ./ontos-skill

# 2. Edit SKILL.md and add references/scripts

# 3. Package for distribution
python3 ~/.claude/plugins/cache/anthropic-skills/document-skills/*/scripts/package_skill.py ./ontos-skill
# Output: ontos.skill
```

## Skill Structure

```
ontos-skill/
    SKILL.md                        # Main skill definition
    references/
        activation-protocol.md      # Full activation workflow
        command-reference.md        # CLI quick reference
    scripts/
        (none needed - uses ontos CLI directly)
```

### SKILL.md Frontmatter

```yaml
---
name: ontos
description: >
  Activate and navigate Ontos knowledge graphs. Use when you detect
  Ontos_Context_Map.md, .ontos-internal/, AGENTS.md, or .ontos.toml
  in the repository. Also use when the user says "Ontos", "Activate Ontos",
  "Archive Ontos", or asks about project context.
---
```

Note: Per skill-creator guidelines, only `name` and `description` in frontmatter. No `allowed-tools` or custom fields.

## Candidate Commands (For Review Board)

### Tier 1: Core Workflow (Recommend Include)

| Trigger | CLI Command | Action |
|---------|-------------|--------|
| "Ontos" / "Activate Ontos" | `ontos map` | Load context map, identify relevant docs, print "Loaded: [ids]" |
| "Archive Ontos" | `ontos log` | Create session log with Goal, Decisions, Impacts |
| "Query Ontos" | `ontos query` | Navigate dependency graph |
| `/ontos-doctor` | `ontos doctor` | Health check and diagnostics |

### Tier 2: Maintenance (Discuss)

| Trigger | CLI Command | Action |
|---------|-------------|--------|
| "Maintain Ontos" | `ontos doctor` + `ontos consolidate` | Weekly health check |
| "Verify Ontos" | `ontos verify` | Mark docs as current |
| "Curate Ontos" | `ontos scaffold` | Auto-generate frontmatter |

### Tier 3: Deferred

- `ontos init` - One-time setup
- `ontos agents` - Meta-command
- `ontos promote` - Complex interactive workflow

## Implementation Steps

### Phase 1: Create Skill with skill-creator

1. **Initialize skill scaffold**
   ```bash
   python3 ~/.claude/plugins/cache/anthropic-skills/document-skills/*/scripts/init_skill.py ontos --path ./ontos-skill
   ```

2. **Write SKILL.md body**
   - Extract core workflow from `Ontos_Agent_Instructions.md`
   - Keep under 500 lines per skill-creator guidelines
   - Include detection triggers and verbal command mappings

3. **Create references/**
   - `references/activation-protocol.md` - Full activation workflow
   - `references/command-reference.md` - CLI cheatsheet (from AGENTS.md pattern)

4. **Package skill**
   ```bash
   python3 ~/.claude/plugins/cache/anthropic-skills/document-skills/*/scripts/package_skill.py ./ontos-skill
   ```
   Output: `ontos.skill` file

### Phase 2: Distribution Strategy

**Option A: Manual Installation**
- User downloads `ontos.skill` from GitHub releases
- Installs via Claude Code's skill installer

**Option B: PyPI Bundling (Future)**
- Bundle `.skill` file in ontos package
- Add `ontos skill install` command that extracts to `~/.claude/skills/`

### Phase 3: Documentation

1. Add installation section to `Ontos_Manual.md`
2. Update README with Claude Code integration instructions

## Open Questions for Review Board

1. **Skill naming**: `ontos` vs `ontos-context`?
2. **Command aliasing**: CLI-mirror (`/ontos-map`) vs semantic (`/refresh-context`)?
3. **Distribution**: GitHub release only, or bundle in PyPI package?
4. **Scope of commands**: What triggers/commands should be in the skill?

## Files to Create

| File | Purpose |
|------|---------|
| `ontos-skill/SKILL.md` | Main skill definition |
| `ontos-skill/references/activation-protocol.md` | Full activation workflow |
| `ontos-skill/references/command-reference.md` | CLI cheatsheet |

## Verification

1. Run `init_skill.py` to create scaffold
2. Populate SKILL.md and references
3. Run `package_skill.py` to validate and package
4. Install `.skill` file manually in Claude Code
5. Open Claude Code in an Ontos project
6. Say "Ontos" and verify auto-activation works
