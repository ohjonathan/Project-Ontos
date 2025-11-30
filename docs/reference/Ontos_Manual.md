---
id: ontos_manual
title: "Ontos: The Manual"
type: kernel
status: active
depends_on: []
---

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

> **Automation:** Use `scripts/migrate_frontmatter.py` to scan for untagged files, then tag them using your AI agent.

## **Document Type Taxonomy**

Ontos uses four hierarchical document types. When tagging documents, select the type that best matches the document's *purpose*, not its format.

| Type | Rank | Definition | Signal Words |
|------|------|------------|--------------|
| `kernel` | 0 | Immutable foundational principles that rarely change. | mission, values, philosophy, principles, "why we exist" |
| `strategy` | 1 | High-level decisions about goals, audiences, and approaches. | goals, roadmap, monetization, target market, competitive positioning |
| `product` | 2 | User-facing features, journeys, and requirements. | user flow, feature spec, requirements, user story, journey |
| `atom` | 3 | Technical implementation details and specifications. | API, schema, config, implementation, technical spec, code |

### Dependency Rule

Dependencies flow **down** the hierarchy. Higher-ranked documents can depend on lower-ranked documents.

- ✅ `atom` → `product` → `strategy` → `kernel` (valid chain)
- ❌ `kernel` → `atom` (architectural violation)

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
python3 scripts/generate_context_map.py
```

This generates `CONTEXT_MAP.md`, which visualizes the graph and performs **5 Integrity Checks**:
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
1.  Run `scripts/migrate_frontmatter.py` to catch untagged files.
2.  Run `scripts/generate_context_map.py` to rebuild the graph.
3.  Fix any errors reported (Broken Links, Cycles, etc.).
4.  Commit the updated map.

**Do not manually edit CONTEXT_MAP.md.** It is a disposable artifact.

### Strict Mode (CI/CD)

To enforce graph integrity in pipelines, use the `--strict` flag:
```bash
python3 scripts/generate_context_map.py --strict
```
This will exit with an error code if any issues are found.

## **Phase 3: Vibe Coding (The Usage)**

*How to use the map to save tokens and improve context.*

**The Protocol:**
Simply tell your Agent:
> **"Ontos"** (or "Activate Ontos")

The Agent will follow this strict 6-step protocol:
1.  **Check Map**: Look for `CONTEXT_MAP.md`.
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
3. Run `scripts/generate_context_map.py` to verify integrity."

## **Phase 5: The "Session Commit" (Archival)**

*Run this at the end of a coding session to save your "Decision History" to the repo.*

**The Protocol:**
Tell your Agent:
> **"Archive Ontos"** (or "Ontos archive")

**The Agent will:**
1.  Run `python3 scripts/end_session.py "topic-slug"`.
2.  Fill in the generated log file with **Decisions Made**, **Alternatives Rejected**, and **Files Modified**.
3.  Commit the log file to git.

## **Troubleshooting**

### "My file doesn't appear in the context map"

**Cause:** File is missing YAML frontmatter or the `id` field.

**Solution:**
1. Run `python3 scripts/migrate_frontmatter.py` to identify untagged files
2. Add frontmatter to the file:
   ```yaml
   ---
   id: your_unique_id
   type: atom
   ---
   ```
3. Regenerate the map: `python3 scripts/generate_context_map.py`

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
