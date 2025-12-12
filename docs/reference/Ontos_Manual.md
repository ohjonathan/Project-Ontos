# **Ontos: The Manual (v0.4 - Production Ready)**
*Updated: 2025-11-29*

This document is the **Single Source of Truth** for the Ontos Protocol.

## **Phase 0: The "Future-Proof" Setup**

To ensure we can automate this later, every document **MUST** start with this YAML header. This allows us to treat text files like database records.

**The Standard Header Template:**

```yaml
---
id: unique_slug_name  # REQUIRED. Stable ID. Never change this.
type: atom            # REQUIRED. Options: kernel, strategy, product, atom
status: draft         # Optional. Options: draft, active, deprecated
owner: null           # Optional. Role responsible for this doc.
depends_on: []        # List of dependency IDs. Example: [auth_flow, user_model]
---
```

> **Automation:** Use `.ontos/scripts/ontos_migrate_frontmatter.py` to scan for untagged files, then tag them using your AI agent.

## **Document Type Taxonomy**

Ontos uses four hierarchical document types. When tagging documents, select the type that best matches the document's *purpose*, not its format.

| Type | Rank | Definition | Signal Words |
|------|------|------------|--------------|
| `kernel` | 0 | Immutable foundational principles that rarely change. | mission, values, philosophy, principles, "why we exist" |
| `strategy` | 1 | High-level decisions about goals, audiences, and approaches. | goals, roadmap, monetization, target market, competitive positioning |
| `product` | 2 | User-facing features, journeys, and requirements. | user flow, feature spec, requirements, user story, journey |
| `atom` | 3 | Technical implementation details and specifications. | API, schema, config, implementation, technical spec, code |

### Dependency Rule

Dependencies flow **down** the hierarchy (towards stability). Lower-level documents depend on higher-level documents — implementation details depend on abstractions, not the reverse.

- ✅ `atom` → `product` → `strategy` → `kernel` (valid: details depend on abstractions)
- ❌ `kernel` → `atom` (invalid: abstractions should not depend on details)

### Classification Heuristic

When uncertain, ask: *"If this document changes, what else breaks?"*

- If everything breaks → `kernel`
- If business direction changes → `strategy`
- If user experience changes → `product`
- If only implementation changes → `atom`

## **Phase 1: The "Architect" (Initialization)**

Instead of prompting the LLM to hallucinate a map, we now use a deterministic script.

**Run:**
```bash
python3 .ontos/scripts/ontos_generate_context_map.py
```

This generates `Ontos_Context_Map.md`, which visualizes the graph and performs **5 Integrity Checks**:
1.  **Broken Links**: IDs that don't exist.
2.  **Circular Dependencies**: Infinite loops (A -> B -> A).
3.  **Orphaned Nodes**: Files disconnected from the graph.
4.  **Dependency Depth**: Chains deeper than 5 layers.
5.  **Architectural Violations**: Lower-layer docs (Kernel) depending on Higher-layer docs (Atoms).

## **Phase 2: The "Weekly Ritual" (Automated Maintenance)**

**The Protocol:**
Tell your Agent:
> **"Maintain Ontos"**

**The Agent will:**
1.  Run `.ontos/scripts/ontos_migrate_frontmatter.py` to catch untagged files.
2.  Run `.ontos/scripts/ontos_generate_context_map.py` to rebuild the graph.
3.  Fix any errors reported (Broken Links, Cycles, etc.).
4.  Commit the updated map.

**Do not manually edit `Ontos_Context_Map.md`.** It is a disposable artifact.

### Strict Mode (CI/CD)

To enforce graph integrity in pipelines, use the `--strict` flag:
```bash
python3 .ontos/scripts/ontos_generate_context_map.py --strict
```
This will exit with an error code if any issues are found.

## **Phase 3: Vibe Coding (The Usage)**

*How to use the map to save tokens and improve context.*

**The Protocol:**
Simply tell your Agent:
> **"Ontos"** (or "Activate Ontos")

The Agent will follow this strict 6-step protocol:
1.  **Check Map**: Look for `Ontos_Context_Map.md`.
2.  **Generate**: Run the script if missing.
3.  **Read**: Read the map to understand the project structure.
4.  **Identify**: Identify relevant documentation IDs for your request.
5.  **Load**: Read *only* the specific files needed.
6.  **Confirm**: Respond with "Loaded: [list of doc IDs]".

## **Phase 4: The Update Loop (The Write-Back)**

*When you make a decision in Chat, update the docs.*

**The Prompt:**

"We just decided to change the pricing to $30/month.

1. Find the file with id: `strategy_monetization`.
2. Update the markdown content.
3. Run `.ontos/scripts/ontos_generate_context_map.py` to verify integrity."

## **Phase 5: The "Session Commit" (Archival)**

*Run this at the end of a coding session to save your "Decision History" to the repo.*

**The Protocol:**
Tell your Agent:
> **"Archive Ontos"** (or "Ontos archive")

**The Agent will:**
1.  Run `python3 .ontos/scripts/ontos_end_session.py "topic-slug" --source "LLM Name"` (where "LLM Name" is the agent's name, e.g., "Claude Code", "Gemini", "Cursor").
2.  Fill in the generated log file with **Decisions Made**, **Alternatives Rejected**, and **Files Modified**.
3.  Commit the log file to git.

## **Troubleshooting**

### "My file doesn't appear in the context map"

**Cause:** File is missing YAML frontmatter or the `id` field.

**Solution:**
1. Run `python3 .ontos/scripts/ontos_migrate_frontmatter.py` to identify untagged files
2. Add frontmatter to the file:
   ```yaml
   ---
   id: your_unique_id
   type: atom
   ---
   ```
3. Regenerate the map: `python3 .ontos/scripts/ontos_generate_context_map.py`

### "How do I fix a circular dependency?"

**Example Error:** `[CYCLE] Circular dependency detected: doc_a -> doc_b -> doc_a`

**Solution:**
1. Identify which dependency is incorrect (usually the one that points "up" the hierarchy)
2. Remove the problematic `depends_on` entry from one of the files
3. Consider if documents should be merged or restructured

### "Two files have the same ID"

**Behavior:** Only the last-scanned file will appear in the map.

**Solution:**
1. Search for duplicate IDs: `grep -r "^id:" docs/`
2. Rename one of the IDs to be unique
3. Update any `depends_on` references to the renamed ID

### "Architectural violation error"

**Example Error:** `[ARCHITECTURE] kernel_mission (kernel) depends on higher-layer api_spec (atom)`

**Explanation:** Kernels are foundational and should not depend on implementation details.

**Solution:**
1. Review if the dependency is actually needed
2. If needed, consider changing the document type:
   - Maybe `kernel_mission` should be `strategy`
   - Or `api_spec` should be elevated to `product`
3. Remove the dependency if it's not essential

## **Configuration**

Ontos behavior can be customized via `.ontos/scripts/ontos_config.py`. This file is never overwritten by `ontos_update.py`, so your customizations are safe.

### Workflow Enforcement Settings

These settings control how strictly Ontos enforces workflow rules:

| Setting | Default | Description |
|---------|---------|-------------|
| `ENFORCE_ARCHIVE_BEFORE_PUSH` | `True` | **Pre-push hook behavior.** When `True`, push is blocked until session is archived. When `False`, shows advisory reminder only. |
| `REQUIRE_SOURCE_IN_LOGS` | `True` | **Session log authorship.** When `True`, `--source` flag is required in `ontos_end_session.py`. When `False`, source is optional. |

### Customization Examples

**Relaxed mode** (for solo developers or rapid prototyping):

```python
# .ontos/scripts/ontos_config.py

# Allow push without archiving (advisory only)
ENFORCE_ARCHIVE_BEFORE_PUSH = False

# Make --source optional in session logs
REQUIRE_SOURCE_IN_LOGS = False
```

**Strict mode** (default, recommended for teams):

```python
# .ontos/scripts/ontos_config.py

# Block push until session is archived
ENFORCE_ARCHIVE_BEFORE_PUSH = True

# Require source attribution in all logs
REQUIRE_SOURCE_IN_LOGS = True
```

### Directory Settings

```python
# Custom documentation directory
DOCS_DIR = os.path.join(PROJECT_ROOT, 'documentation')

# Custom session logs directory
LOGS_DIR = os.path.join(PROJECT_ROOT, 'documentation/session-logs')

# Additional patterns to skip during scanning
SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS + ['drafts/', 'archive/']
```

### Emergency Bypass

Even with `ENFORCE_ARCHIVE_BEFORE_PUSH = True`, you can bypass the hook in emergencies:

```bash
git push --no-verify
```

Use sparingly — you'll lose context!
