---
id: phase3_implementation_spec_review_codex
status: draft
reviewer: Codex
---

# Phase 3 Implementation Spec Review (Codex)

Reviewer: Codex
Date: 2026-01-13
Scope: Phase 3 (Configuration & Init)

---

## Gemini — Peer Review

### 1. Open Questions Research

#### 1.1 Config File Location

| Tool | Config Location | Hidden? | Notes |
|------|-----------------|---------|-------|
| Prettier | `.prettierrc`, `prettier.config.js` | Mixed | https://prettier.io/docs/en/configuration.html |
| ESLint | `eslint.config.js|mjs|cjs|ts` | No | https://eslint.org/docs/latest/use/configure/configuration-files |
| Black | `pyproject.toml` `[tool.black]` | No | https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html |
| Ruff | `pyproject.toml`, `ruff.toml`, `.ruff.toml` | Mixed | https://docs.astral.sh/ruff/configuration/ |
| Cargo | `Cargo.toml` | No | https://doc.rust-lang.org/cargo/reference/manifest.html |
| Poetry | `pyproject.toml` `[tool.poetry]` | No | https://python-poetry.org/docs/pyproject/ |

**Patterns observed:**
- Visible root config is common (Cargo, ESLint).
- Python tooling converges on `pyproject.toml` with `[tool.*]` sections.

**Recommendation for Ontos:** `.ontos.toml`
- Rationale: language-agnostic, aligns with roadmap, avoids Python-only coupling. Optional `pyproject.toml [tool.ontos]` could be future enhancement.

#### 1.2 Init Failure Behavior

| Tool | Behavior | Exit Code | Message |
|------|----------|-----------|---------|
| Git | Reinitializes existing repo | 0 | https://git-scm.com/docs/git-init |
| npm | Creates/updates package.json (interactive) | 0 | https://docs.npmjs.com/cli/v10/commands/npm-init |
| Cargo | Creates package in existing dir | 0 | https://doc.rust-lang.org/cargo/commands/cargo-init.html |
| Poetry | Interactive creation of pyproject.toml | 0 | https://python-poetry.org/docs/cli/ |

**Patterns observed:**
- Many tools re-run init successfully (git, npm).
- Interactive flows are common for project setup.

**Recommendation for Ontos:** Error with exit code 1 + `--force`.
- Rationale: Ontos writes config + hooks + directories; silent reinit risks clobbering.

#### 1.3 Init UX Flow

| Tool | Default Behavior | Wizard? | Interactive Flag |
|------|------------------|---------|------------------|
| npm | Interactive prompts by default | Yes | `-y` for defaults |
| cargo | Minimal defaults | No | Flags |
| poetry | Wizard-style prompts | Yes | Flags |

**Recommendation for Ontos:** Smart defaults with optional `--interactive`.
- Rationale: supports automation and discoverable UX.

---

### 2. Spec Completeness

| Section | Present? | Complete? | Notes |
|---------|----------|-----------|-------|
| Overview & Scope | Yes | Yes | — |
| Entry/Exit Criteria | Yes | Partial | Missing `--force` + export tip in exit criteria |
| Current State Analysis | Yes | Yes | — |
| Target State | Yes | Yes | — |
| File Specifications | Yes | Partial | Missing config resolution logic |
| Migration Tasks | Yes | Partial | No CLI config resolution tasks |
| Test Specifications | Yes | Partial | No config resolution tests |

**Missing Elements:**
- Config resolution implementation details (high impact)
- Project type detection in init (medium)
- Init creates initial context map (high)

---

### 3. Config System Design

| Dataclass | Purpose | Fields Complete? | Defaults Sensible? |
|-----------|---------|------------------|-------------------|
| OntosSection | Version info | Yes | Yes |
| PathsConfig | Directory paths | Yes | Yes |
| ScanningConfig | Skip patterns | Yes | Yes |
| ValidationConfig | Validation rules | Yes | Yes |
| WorkflowConfig | Workflow settings | Yes | Yes |
| HooksConfig | Hook settings | Yes | Yes |

**Config Resolution:** Not implemented/tested (CLI/env/file/default missing in spec).

**Open Questions:**
- Missing `dict_to_config` behavior spec
- No config validation or migration path

---

### 4. Init Command UX

| Step | Specified? | User-Friendly? | Suggestion |
|------|------------|----------------|------------|
| Check existing config | Yes | Yes | — |
| Check git repo | Yes | Partial | `.git` dir check fails for worktrees/submodules |
| Detect legacy | Yes | Yes | — |
| Create config | Yes | Partial | No smart defaults or template comments |
| Create directories | Yes | Yes | Validate paths within repo |
| Install hooks | Yes | Partial | `.git/hooks` creation not handled |
| Success message | Yes | Partial | Doesn’t mention hooks skipped |

**UX Concerns:**
- Interactive flag unused
- Hook skip not summarized in final message

---

### 5. Implementability

| Module | Detailed Enough? | Could Implement? |
|--------|------------------|-----------------|
| core/config.py | Yes | Yes |
| io/config.py | Yes | Yes |
| commands/init.py | Yes | Yes |
| CLI updates | No | No |

**Ambiguities:**
- `dict_to_config` implementation details
- `--interactive` flow definition
- Config resolution placement

---

### 6. Test Coverage

**Missing Tests:**
- Config precedence tests
- Init creates initial context map
- Hook detection false positives
- Windows hook permissions

---

### 7. Positive Observations

- Clear exit codes
- Clean layer separation
- Hook shim fallback to `python -m ontos`

---

### 8. Summary

| Question | Recommendation | Confidence |
|----------|----------------|------------|
| Config location | `.ontos.toml` | Med |
| Init failure | Error + `--force` | High |
| Init UX | Smart defaults + optional interactive | High |

**Issues by severity:**
- Critical: 0
- Major: 4
- Minor: 6

**Verdict:** Request revision

---

## Claude — Alignment Review

### Roadmap Alignment (v1.5 Section 5)

**Missing or partial vs roadmap:**
- Config resolution in CLI (missing)
- Project type detection (missing)
- Init creates initial context map (missing)
- Comment-preserving TOML template (roadmap requirement; spec says no changes to io/toml.py)

**Exit Codes:** Matches roadmap.

**Config Template:** Matches roadmap.

**Architecture:** Aligned with core/io separation.

**Verdict:** Major deviations; must fix missing roadmap requirements.

---

## Codex — Adversarial Review

### 1. Open Questions Attack

**Config location downsides:**
- `.ontos.toml`: hidden; discoverability fair.
- `ontos.toml`: visible but nonstandard.
- `.ontos/config.toml`: lowest discoverability.
- `pyproject.toml`: Python-centric; conflicts for non-Python.

**Best:** `.ontos.toml`
**Worst:** `.ontos/config.toml`

**Init failure:**
- Silent success has highest confusion.
- Error + `--force` is safest.

**Init UX:**
- Wizard by default is worst for automation.
- Smart defaults + optional interactive is best.

---

### 2. Config Parsing Attack

**Unaddressed scenarios:** invalid TOML, missing sections, wrong types, unknown sections.

**High-risk bugs:**
- Silent fallback on invalid TOML
- Path traversal via config paths

---

### 3. Init Command Attack

**Edge cases not handled:**
- Git worktrees/submodules (`.git` is file)
- Bare repos
- Read-only directories
- Concurrent init

**High-risk:** false “not a git repo” for submodules/worktrees.

---

### 4. Hook Installation Attack

**Edge cases not handled:**
- `.git/hooks` missing or symlink
- Hook file is dir/symlink
- Permissions not set on Windows

**High-risk:** false positive hook detection using substring match for "ontos" + "shim".

---

### 5. Cross-Platform Attack

**Windows issues:** shebang, chmod, long paths, CRLF.
**macOS issues:** quarantine, case-insensitive FS.
**Linux issues:** SELinux context.

---

### 6. Security Attack

**Risks:**
- Path traversal via config path values
- Hook overwrites on false detection

---

### 7. User Confusion Attack

**Confusing scenarios:**
- Parent config applies to child
- Multiple projects in one repo
- Hooks skipped but init says success

---

## Final Consolidated Verdict (Codex)

**Recommendation:** Request changes

**Blocking issues:**
1. Missing config resolution (CLI/env/file/default) and tests
2. Init missing project-type detection + initial context map creation
3. Unsafe hook detection (false positives) + missing hook edge cases
4. Unvalidated config paths allow traversal

**Top fixes:**
1. Implement config resolution in CLI; add precedence tests
2. Add initial context map creation in init
3. Replace hook detection with explicit marker + checksum; handle `.git` worktrees and hook dir creation
4. Validate config paths relative to repo root
