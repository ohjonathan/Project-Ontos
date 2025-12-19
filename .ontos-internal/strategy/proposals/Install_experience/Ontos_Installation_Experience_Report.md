# Ontos Installation Experience Report

**Date:** 2025-12-18
**Installer:** Claude (AI Agent)
**Project Ontos Version:** 2.5.2
**Target Repository:** Test-Personal-ERP (empty project)

---

## Executive Summary

The installation process required significant manual intervention, undocumented steps, and troubleshooting. What should be a simple `git clone && ./install.sh` experience instead required 7+ manual steps, script failures, and documentation hunting.

---

## Detailed Installation Timeline

### Step 1: Clone Repository ✅
**Action:** `git clone https://github.com/ohjona/Project-Ontos /tmp/Project-Ontos`
**Result:** Success
**Friction:** None

---

### Step 2: Identify Files to Copy ⚠️
**Action:** Manual inspection of cloned repository structure
**Result:** Required `ls -la` commands to understand what to copy

**Friction Points:**
1. **No manifest file** — User instructions said "copy `.ontos/` folder and `ontos_init.py`" but there was no canonical list of required files
2. **Ambiguous documentation location** — User requested:
   - `docs/reference/Ontos_Agent_Instructions.md`
   - `.ontos-internal/reference/Common_Concepts.md`

   But the repo had `Common_Concepts.md` in TWO locations:
   - `/docs/reference/Common_Concepts.md` (~430 bytes, stub)
   - `/.ontos-internal/reference/Common_Concepts.md` (~2627 bytes, full version)

   **Why this is bad:** An installer doesn't know which is authoritative. The stub version in `docs/reference/` appears to be a simplified copy, but this isn't documented anywhere.

3. **No install script** — Manual `cp` commands required for each component

---

### Step 3: Copy Core Files ✅
**Actions:**
```bash
cp -r /tmp/Project-Ontos/.ontos /Users/jonathanoh/Dev/Test-Personal-ERP/
cp /tmp/Project-Ontos/ontos_init.py /Users/jonathanoh/Dev/Test-Personal-ERP/
```
**Result:** Success
**Friction:** None (once files were identified)

---

### Step 4: Create Documentation Structure ✅
**Actions:**
```bash
mkdir -p docs/reference
cp .../docs/reference/Ontos_Agent_Instructions.md docs/reference/
cp .../.ontos-internal/reference/Common_Concepts.md docs/reference/
```
**Result:** Success
**Friction:** Had to create directory structure manually

---

### Step 5: Run Initialization Script ❌❌✅
**Action:** `python3 ontos_init.py`

#### Attempt 1: FAILED
```
EOFError: EOF when reading a line
```
**Reason:** Script requires interactive input but was run non-interactively. The script uses `input()` calls that fail when stdin is not a TTY.

**Friction:**
- No `--non-interactive` or `--defaults` flag
- No environment variable configuration option
- No config file pre-seeding option

#### Attempt 2: FAILED
```bash
echo "2" | python3 ontos_init.py
```
```
EOFError: EOF when reading a line
```
**Reason:** Script requires MULTIPLE inputs:
1. Mode selection (1-3)
2. Source name for logs

The first `input()` consumed the "2", then the second `input()` hit EOF.

**Friction:**
- No documentation of how many inputs are required
- No way to know input sequence without reading source code or trial-and-error

#### Attempt 3: SUCCESS
```bash
printf "2\nClaude\n" | python3 ontos_init.py
```
**Result:** Successfully initialized

**Why this matters:** An AI agent (or CI/CD pipeline, or scripted installer) cannot reliably run this script without:
- Reading the source code to count `input()` calls
- Guessing the order and valid values
- Trial-and-error attempts

---

### Step 6: "Initiate Ontos" Command ⚠️
**User Request:** "Initiate Ontos"

**Friction Points:**
1. **Command not self-evident** — Had to read `Ontos_Agent_Instructions.md` to understand what "Initiate Ontos" means
2. **Documentation buried** — The agent instructions file wasn't in a standard location; user had to specify copying it manually
3. **Activation procedure is 6 steps:**
   - Check for context map
   - Generate if missing
   - Read map
   - Check consolidation status
   - Read relevant files
   - Print loaded IDs

   **Why this is friction:** This should be a single command: `python3 .ontos/scripts/ontos_activate.py`

---

### Step 7: "Migrate Ontos" Command ⚠️
**User Request:** "Migrate Ontos"

**Friction Points:**
1. **No "migrate" command documented** — Had to explore `.ontos/scripts/` directory to find migration scripts
2. **Multiple migration scripts with unclear purposes:**
   - `ontos_migrate_frontmatter.py` — for untagged files
   - `ontos_migrate_v2.py` — for v1→v2 schema

   **Question:** Which one is "Migrate Ontos"? Both? Neither?

3. **Had to run `--help` on each** to understand their purpose
4. **Migration is also part of `ontos_maintain.py`** — So there are 3 places migration logic lives

---

### Step 8: Uninstall Attempt ⚠️
**User Provided Commands:**
```bash
rm -rf .ontos/
rm -f Ontos_Context_Map.md Ontos_Agent_Instructions.md
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes
```

**Critical Issue:** The commands are in the WRONG ORDER.
- Line 1 deletes `.ontos/`
- Line 3 tries to run a script FROM `.ontos/`

**Required Fix:** Reorder to run frontmatter removal BEFORE deleting `.ontos/`

**Additional Cleanup Required:**
- `ontos_init.py` — not mentioned in uninstall
- `ontos_config.py` — not mentioned in uninstall
- Git hooks (`pre-push`, `pre-commit`) — not mentioned in uninstall
- `docs/` subdirectories created by init — not mentioned

---

## Summary of Issues

### Critical Issues (Blocks Installation)

| Issue | Impact | Root Cause |
|-------|--------|------------|
| `ontos_init.py` requires interactive input | Cannot automate installation | Uses `input()` without non-interactive fallback |
| Multiple inputs required, undocumented | Trial-and-error needed | No `--help` showing required inputs |

### High-Friction Issues

| Issue | Impact | Root Cause |
|-------|--------|------------|
| No install script | Manual `cp` commands required | Missing `install.sh` or `make install` |
| Duplicate `Common_Concepts.md` files | Confusion about which to use | Two versions exist with different content |
| Uninstall commands in wrong order | Script fails if followed literally | Documentation error |
| Incomplete uninstall instructions | Leaves orphan files | Missing `ontos_init.py`, `ontos_config.py`, hooks |

### Medium-Friction Issues

| Issue | Impact | Root Cause |
|-------|--------|------------|
| "Initiate Ontos" not a script | Manual multi-step process | No `ontos_activate.py` command |
| "Migrate Ontos" ambiguous | Multiple scripts to discover | No unified migration command |
| Agent instructions not auto-installed | Extra manual copy step | Not part of `ontos_init.py` |

---

## Recommendations

### 1. Create `install.sh`
```bash
#!/bin/bash
# One-command installation
git clone https://github.com/ohjona/Project-Ontos /tmp/ontos-install
cp -r /tmp/ontos-install/.ontos .
cp /tmp/ontos-install/ontos_init.py .
mkdir -p docs/reference
cp /tmp/ontos-install/docs/reference/*.md docs/reference/
python3 ontos_init.py --defaults  # <-- needs to exist
rm -rf /tmp/ontos-install
```

### 2. Add Non-Interactive Mode to `ontos_init.py`
```python
# Support these patterns:
python3 ontos_init.py --defaults                    # Use all defaults
python3 ontos_init.py --mode=prompted --source=Claude  # Explicit values
ONTOS_MODE=prompted ONTOS_SOURCE=Claude python3 ontos_init.py  # Env vars
```

### 3. Fix Uninstall Documentation
Correct order:
```bash
# 1. Remove frontmatter FIRST (requires .ontos/)
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes

# 2. Remove git hooks
rm -f .git/hooks/pre-push .git/hooks/pre-commit

# 3. Remove Ontos files
rm -rf .ontos/
rm -f Ontos_Context_Map.md ontos_init.py ontos_config.py

# 4. Optionally remove created directories
rm -rf docs/logs docs/archive docs/strategy
```

### 4. Consolidate Migration Commands
```bash
# Single command that does everything:
python3 .ontos/scripts/ontos_migrate.py --all
```

### 5. Add `ontos_activate.py`
```bash
# Instead of 6-step manual process:
python3 .ontos/scripts/ontos_activate.py
# Output: "Ontos activated. Loaded: [id1, id2, id3]"
```

### 6. Resolve Duplicate Files
Either:
- Remove `docs/reference/Common_Concepts.md` stub from repo, OR
- Make `.ontos-internal/reference/Common_Concepts.md` a symlink, OR
- Document which is authoritative

---

## Conclusion

The current Ontos installation requires **7+ manual steps**, **3 failed attempts** at running the init script, and **documentation archaeology** to understand commands. An AI agent or developer unfamiliar with the system would struggle significantly.

**Time spent on installation:** ~15 minutes of active troubleshooting
**Expected time for good DX:** <1 minute (`curl | bash` or `npx`)

The tooling itself appears well-designed once installed, but the onboarding experience creates unnecessary friction that could deter adoption.
