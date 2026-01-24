---
id: dual_mode_matrix
type: atom
status: active
depends_on: [schema]
---

# Dual-Mode Support Matrix

Reference document tracking which Ontos features work in Contributor Mode vs User Mode.

**Contributor Mode:** Developing Project Ontos itself (`.ontos-internal/`)
**User Mode:** Using Ontos in your own project (`docs/`)

---

## 1. Directory Structure

| Directory | Contributor Mode | User Mode | Notes |
|-----------|------------------|-----------|-------|
| Documentation root | `.ontos-internal/` | `docs/` | Set by `is_ontos_repo()` |
| Session logs | `.ontos-internal/logs/` | `docs/logs/` | |
| Kernel docs | `.ontos-internal/kernel/` | `docs/kernel/` | v3.1.1+ |
| Strategy docs | `.ontos-internal/strategy/` | `docs/strategy/` | |
| Product docs | — | `docs/product/` | v3.1.1+ |
| Atom docs | `.ontos-internal/atom/` | `docs/atom/` | v3.1.1+ |
| Proposals | `.ontos-internal/strategy/proposals/` | `docs/strategy/proposals/` | v2.5.2+ |
| Archive (logs) | `.ontos-internal/archive/logs/` | `docs/archive/logs/` | v2.5.2+ |
| Archive (proposals) | `.ontos-internal/archive/proposals/` | `docs/archive/proposals/` | v2.5.2+ |
| Reference docs | `.ontos-internal/reference/` | `docs/reference/` | |

---

## 2. Scripts

| Script | Contributor | User | Notes |
|--------|-------------|------|-------|
| `ontos_init.py` | ✅ | ✅ | Creates mode-appropriate structure |
| `ontos_end_session.py` | ✅ | ✅ | Uses `get_logs_dir()` |
| `ontos_generate_context_map.py` | ✅ | ✅ | Scans mode-appropriate dirs |
| `ontos_consolidate.py` | ✅ | ✅ | Uses path helpers |
| `ontos_maintain.py` | ✅ | ✅ | Orchestrates other scripts |
| `ontos_query.py` | ✅ | ✅ | Uses path helpers |
| `ontos_migrate_frontmatter.py` | ✅ | ✅ | |
| `ontos_pre_push_check.py` | ✅ | ✅ | |
| `ontos_pre_commit_check.py` | ✅ | ✅ | |
| `ontos_update.py` | ❌ | ✅ | Users update from GitHub |
| `ontos_install_hooks.py` | ✅ | ✅ | |

---

## 3. Path Helpers (`ontos_lib.py`)

| Function | Contributor Mode | User Mode | Backward Compat |
|----------|------------------|-----------|-----------------|
| `get_logs_dir()` | `.ontos-internal/logs/` | `docs/logs/` | N/A |
| `get_archive_dir()` | `.ontos-internal/archive/` | `docs/archive/` | N/A |
| `get_archive_logs_dir()` | `.ontos-internal/archive/logs/` | `docs/archive/logs/` | Falls back to `docs/archive/` |
| `get_archive_proposals_dir()` | `.ontos-internal/archive/proposals/` | `docs/archive/proposals/` | N/A (new in v2.5.2) |
| `get_proposals_dir()` | `.ontos-internal/strategy/proposals/` | `docs/strategy/proposals/` | N/A (new in v2.5.2) |
| `get_decision_history_path()` | `.ontos-internal/strategy/decision_history.md` | `docs/strategy/decision_history.md` | Falls back to `docs/decision_history.md` |
| `get_concepts_path()` | `.ontos-internal/reference/Common_Concepts.md` | `docs/reference/Common_Concepts.md` | Falls back to `docs/Common_Concepts.md` |

---

## 4. Features

| Feature | Contributor | User | Notes |
|---------|-------------|------|-------|
| Session archival | ✅ | ✅ | Core workflow |
| Pre-push blocking | ✅ | ✅ | Configurable via mode |
| Pre-commit consolidation | ✅ | ✅ | Automated mode only |
| Context map generation | ✅ | ✅ | |
| Lint warnings | ✅ | ✅ | |
| Log consolidation | ✅ | ✅ | |
| Hook installation | ✅ | ✅ | |
| Mode selection (init) | ❌ | ✅ | Contributors don't run init |
| Version release reminder | ✅ | ❌ | Contributors only (v2.6+) |

---

## 5. Config Settings

| Setting | Contributor | User | Default |
|---------|-------------|------|---------|
| `ONTOS_MODE` | N/A (hardcoded) | `prompted` | User chooses at init |
| `DOCS_DIR` | `.ontos-internal` | `docs` | Auto-detected |
| `LOGS_DIR` | Derived from DOCS_DIR | Derived | |
| `ENFORCE_ARCHIVE_BEFORE_PUSH` | `True` | Mode-dependent | |
| `AUTO_ARCHIVE_ON_PUSH` | `False` | Mode-dependent | |
| `AUTO_CONSOLIDATE_ON_COMMIT` | `False` | Mode-dependent | |
| `LOG_RETENTION_COUNT` | `15` | `15` | Same for both |
| `DEFAULT_SOURCE` | Set in config | Set at init | |

---

## 6. Templates

| Template | Contributor | User | Location |
|----------|-------------|------|----------|
| `decision_history.md` | ✅ | ✅ | `.ontos/templates/` |
| `Common_Concepts.md` | ✅ | ✅ | `.ontos/templates/` |
| `ontos_config.py` | ❌ | ✅ | `.ontos/templates/` |
| Session log template | ✅ | ✅ | Embedded in script |

---

## 7. Testing Requirements

All new features MUST be tested in both modes:

```bash
# Run tests in contributor mode
pytest --mode=contributor

# Run tests in user mode
pytest --mode=user
```

### Test Fixtures

| Fixture | Purpose |
|---------|---------|
| `project_mode` | Get current test mode |
| `mode_aware_project` | Create temp project with mode-appropriate structure |
| `docs_dir` | Get docs directory based on mode |

### Adding New Features Checklist

- [ ] Does the feature use path helpers from `ontos_lib.py`?
- [ ] Is the feature tested in both modes?
- [ ] Is the feature documented in this matrix?
- [ ] Does the feature have appropriate fallbacks for older installations?

---

## 8. Detection Logic

```python
# From ontos_config_defaults.py
def is_ontos_repo() -> bool:
    """Check if this is the Ontos repository itself (contributor mode).

    Returns:
        True if .ontos-internal/ exists (contributor mode),
        False otherwise (user mode).
    """
    return os.path.exists(os.path.join(PROJECT_ROOT, '.ontos-internal'))
```

**Key insight:** The presence of `.ontos-internal/` directory is the single source of truth for mode detection.

---

## 9. Version History

| Version | Changes |
|---------|---------|
| v3.1.1 | Full type hierarchy in user mode: kernel/, product/, atom/ subdirectories |
| v2.5.2 | Added nested directory structure, template loader, path helpers with backward compat |
| v2.5.1 | Added proposals directory concept |
| v2.5.0 | Mode promises, consolidation behavior per mode |
| v2.4.0 | Mode system (automated/prompted/advisory) |
| v1.5.0 | Initial dual-mode support via `is_ontos_repo()` |

---

## 10. Common Pitfalls

| Pitfall | How to Avoid |
|---------|--------------|
| Hardcoding `docs/` path | Use `resolve_config('DOCS_DIR')` or path helpers |
| Hardcoding `.ontos-internal/` | Use `is_ontos_repo()` check |
| Testing only in contributor mode | Always run `pytest --mode=user` |
| Missing backward compatibility | Use path helpers with fallback logic |
| Forgetting to update this matrix | Add to PR checklist |
