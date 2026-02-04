---
id: migration_v2_to_v3
type: reference
status: active
depends_on: [ontos_manual]
---

# Migration Guide: v2.x → v3.0

This guide covers the breaking changes and migration steps for upgrading from Ontos v2.x to v3.0.

## What Changed in v3.0

### Package Structure

**Before (v2.x):**
- Scripts in `.ontos/scripts/` executed directly
- `ontos_lib.py` shim for shared functions
- `install.py` for installation

**After (v3.0):**
- Proper Python package under `ontos/`
- `ontos.core.*` modules with clean imports
- PyPI-installable: `pip install ontos`

### Installation

**Before:**
```bash
curl -sO https://raw.githubusercontent.com/.../install.py
python3 install.py
```

**After:**
```bash
pip install ontos
ontos init
```

### CLI Commands

**Before:**
```bash
python3 .ontos/scripts/ontos_end_session.py -e feature
python3 .ontos/scripts/ontos_generate_context_map.py
python3 .ontos/scripts/ontos_maintain.py
```

**After:**
```bash
ontos archive -e feature
ontos map
ontos maintain
```

### Import Changes (for custom scripts)

If you have custom scripts that imported from `ontos_lib`, update them:

| Old Import | New Import |
|------------|------------|
| `from ontos_lib import parse_frontmatter` | `from ontos.core.frontmatter import parse_frontmatter` |
| `from ontos_lib import resolve_config` | `from ontos.core.paths import resolve_config` |
| `from ontos_lib import check_staleness` | `from ontos.core.staleness import check_staleness` |
| `from ontos_lib import SessionContext` | `from ontos.core.context import SessionContext` |
| `from ontos_lib import find_draft_proposals` | `from ontos.core.proposals import find_draft_proposals` |
| `from ontos_lib import generate_decision_history` | `from ontos.core.history import generate_decision_history` |

## Migration Steps

### 1. Backup Current Installation

```bash
cp -r .ontos .ontos.backup
cp ontos_config.py ontos_config.py.backup
```

### 2. Install v3.0

```bash
pip install ontos>=3.0
```

### 3. Verify Installation

```bash
ontos --version  # Should show 3.0.1
ontos doctor     # Check installation health
```

### 4. Update Git Hooks

```bash
ontos init --force  # Reinstall v3.0 hooks
```

### 5. Update Custom Scripts

If you have custom scripts importing from `ontos_lib`, update the imports as shown above.

### 6. Clean Up

The following files are no longer needed and can be removed:

- `.ontos/scripts/ontos_lib.py` (now in `ontos.core.*`)
- `install.py` (replaced by `pip install`)

## Preserved Features

Everything else works the same:

- ✅ `ontos_config.py` - Your settings are preserved
- ✅ Session logs and archives
- ✅ Context map format
- ✅ Frontmatter schema
- ✅ Git hooks behavior
- ✅ Agent instructions

## Rollback

If you need to revert to v2.x:

```bash
pip uninstall ontos
cp -r .ontos.backup .ontos
cp ontos_config.py.backup ontos_config.py
```

## Getting Help

- Run `ontos doctor` for diagnostics
- Check [Ontos Manual](Ontos_Manual.md) for complete reference
- Open an issue at [GitHub](https://github.com/ohjonathan/Project-Ontos/issues)
