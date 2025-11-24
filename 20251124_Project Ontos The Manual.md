# **Ontos: The Manual (v0.2 - Automated Edition)**
*Updated: 2025-11-24*

## **Phase 0: The "Future-Proof" Setup**

To ensure we can automate this later, every document **MUST** start with this YAML header. This allows us to treat text files like database records.

**The Standard Header Template:**

```yaml
---
id: unique_slug_name  # REQUIRED. Stable ID. Never change this even if filename changes.
type: [kernel | strategy | product | atom] # REQUIRED. Defines the hierarchy level.
status: [draft | active | deprecated] # Optional. Helps LLM ignore old files.
owner: [role] # Optional. Who is responsible?
depends_on: [id_of_parent_doc, id_of_other_doc] # The Logic Links.
---
```

### **Example: docs/features/stripe_checkout.md**

```yaml
---
id: feature_stripe_checkout
type: atom
status: active
depends_on: [strategy_monetization, journey_user_checkout]
---
# Stripe Checkout Specification
...
```

> **Automation:** Use `scripts/migrate_frontmatter.py` to automatically tag existing documents.

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
5.  **Architectural Violations**: Higher-layer docs (Atoms) depending on Lower-layer docs (Kernel).

## **Phase 2: The "Weekly Ritual" (Automated Maintenance)**

**Do not manually edit CONTEXT_MAP.md.** It is a disposable artifact.

Whenever you add a file or change a dependency:
1.  Update the YAML frontmatter.
2.  Run `python3 scripts/generate_context_map.py`.
3.  Fix any errors reported in the "Dependency Audit".
4.  Commit the updated map.

## **Phase 3: Vibe Coding (The Usage)**

*How to use the map to save tokens and improve context.*

**The Protocol:**
Simply tell your Agent:
> **"Activate Ontos."** (or "Ontos Activate", "Ontos")

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
> **"Archive Ontos."** (or "Ontos archive", "Archive our session")

**The Agent will:**
1.  Run `python3 scripts/end_session.py "topic-slug"`.
2.  Fill in the generated log file with **Decisions Made**, **Alternatives Rejected**, and **Files Modified**.
3.  Commit the log file to git.
