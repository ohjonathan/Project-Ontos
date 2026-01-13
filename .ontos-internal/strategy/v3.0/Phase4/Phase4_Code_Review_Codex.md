# Phase 4 Code Review: Adversarial Reviewer (PR #44)

**Reviewer:** Codex (Adversarial)
**Date:** 2026-01-13

## Summary

| Attack Surface | Robustness |
|----------------|------------|
| Legacy deletion | Fragile |
| Cross-platform | Fragile |
| Doctor command | Robust |
| Export command | Adequate |
| Hook dispatcher | Fragile |
| JSON output | Fragile |

**Recommendation:** Request Changes

---

<details>
<summary><strong>Legacy Deletion Attack</strong></summary>

Commands run:
```
rg -n "ontos_lib|ontos_generate_context_map|ontos_end_session" -g"*.py" -g"*.md" -g"*.toml" -g"*.txt" .
rg -n "importlib|__import__" ontos -g"*.py" | rg -i "ontos_"
```

| Deleted File | References Found? | Where? | Severity |
|--------------|-------------------|--------|----------|
| ontos_lib.py | Yes | `ontos_init.py:237`, `tests/test_config.py:38`, `docs/reference/Ontos_Manual.md:484` | Critical |
| ontos_generate_context_map.py | Yes | `docs/reference/Ontos_Manual.md:189`, `tests/test_cycle_detection.py:4`, `ontos/_scripts/ontos_pre_push_check.py:148` | Critical |
| ontos_end_session.py | Yes | `docs/reference/Ontos_Manual.md:104`, `tests/test_end_session.py:11`, `ontos/_scripts/ontos_pre_push_check.py:180` | Critical |

**Safe to ship?** No — risks remain

</details>

<details>
<summary><strong>Cross-Platform Attack</strong></summary>

| Issue | Code Handles? | How? |
|-------|---------------|------|
| No shebang | ❌ | Hook shim is `#!/usr/bin/env python3` only (`ontos/commands/init.py:214`) |
| chmod fails | ✅ | Guarded with `if os.name != 'nt'` (`ontos/commands/init.py:250`) |
| Path separators | ✅ | `Path` usage in hook install |
| Long paths | ❌ | Not handled or documented |
| Python not in PATH | ⚠️ | `sys.executable` used but hook execution still depends on git invoking Python |

Evidence:
- Hook shim content: `ontos/commands/init.py:214-245`
- Repo hook template is bash: `ontos/_hooks/pre-push:1`

| Platform | Will Work? | Confidence |
|----------|------------|------------|
| Linux | Yes | Medium |
| macOS | Yes | Medium |
| Windows | No | Low |

</details>

<details>
<summary><strong>Doctor Command Attack</strong></summary>

Tests run:
```
PYTHONPATH=... python3 -m ontos --json doctor
PYTHONPATH=... python3 -m ontos --json doctor -v  (outside git/config)
```

| Scenario | Tested? | Behavior | Acceptable? |
|----------|---------|----------|-------------|
| Not in git repo | ✅ | Warns, continues | ✅ |
| Config file missing | ✅ | Fails with guidance | ✅ |
| Empty repository | ✅ | Fails config/docs/context map checks | ✅ |
| Git not installed | ❌ | Not tested | — |
| Config file corrupt | ❌ | Not tested | — |
| No write permissions | ❌ | Not tested | — |

</details>

<details>
<summary><strong>Export Command Attack</strong></summary>

Test run:
```
PYTHONPATH=... python3 -m ontos --json export -o /tmp/ontos-outside-test/CLAUDE.md
```

| Concern | Risk Level | Mitigated? |
|---------|------------|------------|
| Path traversal | Med | ✅ (rejects outside repo) |
| Exports secrets | High | ✅ (static template) |
| Sensitive content | Med | ✅ (static template) |

</details>

<details>
<summary><strong>Hook Dispatcher Attack</strong></summary>

| Input | Behavior | Secure? |
|-------|----------|---------|
| Unknown hook type | Warns + allow | ✅ (CLI disallows) |
| Malformed arguments | Not handled | ❌ |

| Scenario | Exit Code | Correct? |
|----------|-----------|----------|
| Hook fails | 1 (not implemented) | ❌ (never blocks) |
| Hook throws exception | 0 | ❌ (silently allows) |

</details>

<details>
<summary><strong>JSON Output Attack</strong></summary>

Tests run:
```
PYTHONPATH=... python3 -m ontos doctor --json
PYTHONPATH=... python3 -m ontos --json doctor
PYTHONPATH=... python3 -m ontos --json map
PYTHONPATH=... python3 -m ontos --json init
```

| Command | Same Schema? | Verified? |
|---------|--------------|-----------|
| doctor --json | ❌ | ✅ (status/checks/summary) |
| init --json | ❌ | ✅ (status/message/exit_code + stray stdout) |
| export --json | ❌ | ✅ (status/message/exit_code) |
| map --json | ❌ | ✅ (E_INTERNAL due to options mismatch) |

Key failures:
- `ontos doctor --json` fails unless `--json` appears before the command.
- `ontos map --json` throws `E_INTERNAL` because `GenerateMapOptions` lacks `json_output`/`quiet`.
- `ontos init --json` emits a non-JSON warning to stdout before JSON output.

</details>

---

## Issues Summary

### Critical

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-C1 | Legacy scripts still referenced across docs/tests | Legacy deletion | Deletion will break workflows/tests (`ontos_init.py:237`, `docs/reference/Ontos_Manual.md:104`) |
| X-C2 | JSON output contaminated by stdout warnings | JSON output | Machine parsing breaks (`ontos/commands/init.py:90`) |

### High

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-H1 | `ontos doctor --json` fails after command | JSON output | Common CLI usage breaks (`ontos/cli.py:19`) |
| X-H2 | `ontos map --json` crashes | JSON output | Hard failure (`ontos/cli.py:136`, `ontos/commands/map.py:20`) |
| X-H3 | Hook never blocks on validation errors | Hook dispatcher | Hooks ineffective (`ontos/commands/hook.py:24`) |

### Medium

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-M1 | Windows hook execution unclear | Cross-platform | Hooks may not run on Windows (`ontos/commands/init.py:214`) |

---

## Verdict

**Robustness:** Fragile

**Recommendation:** Request Changes

**Top Risks:**
1. Legacy deletions are unsafe due to active references across docs/tests.
2. JSON output is inconsistent and can emit invalid JSON (stdout contamination, map crash).
3. Hooks do not enforce validation and Windows execution is unreliable.

**Summary:** The Phase 4 implementation still has critical breakage risks around deletion safety and JSON output. Fix JSON schema/behavior, stabilize `map --json`, and resolve deletion dependencies before merge.

---

**Review signed by:**
- **Role:** Adversarial Reviewer
- **Model:** Codex (OpenAI)
- **Date:** 2026-01-13
- **Review Type:** Code Review (Phase 4 Implementation)
