---
id: product_requirement_document__ontos_(v0.1_mvp)
status: draft
type: product
---

# **Product Requirement Document: Ontos (v0.1 MVP)**

| Metadata | Details |
| :---- | :---- |
| **Product Name** | Ontos |
| **Version** | v0.1 (MVP) |
| **Status** | Draft |
| **Core Value** | "The Read-Only Context Engine" |
| **Target User** | The "Vibe Coder" (Solo Founders, Agile Devs) |

## **1\. Executive Summary**

Ontos is a local-first CLI tool that acts as a "Context Operating System" for startup documentation. It solves the problem of **Context Fragmentation** by transforming static Markdown files into a semantic knowledge graph.

**The Problem:** Founders currently act as manual "human middleware," copy-pasting 10+ documents into LLMs to provide context. This leads to high token costs, "lost in the middle" recall failures, and outdated context.

**The Solution:** Ontos parses the project structure locally and provides a context command that intelligently prunes and assembles a laser-focused prompt for AI agents (Cursor, Claude, etc.).

**MVP Philosophy:** **Read-Only First.** The MVP will scan, structure, and retrieve data but will *not* automatically rewrite user files to ensure data safety and build trust.

## **2\. User Stories**

| ID | As a... | I want to... | So that... |
| :---- | :---- | :---- | :---- |
| **US-1** | Founder | Clean up my messy notes folder | I can have a structured base for the ontology. |
| **US-2** | Developer | Automatically map my docs to a standard startup hierarchy | I don't have to manually configure relationships. |
| **US-3** | Vibe Coder | Get context for a specific task (e.g., "Payment") | I can paste it into Cursor without bloating the context window with irrelevant marketing text. |
| **US-4** | Project Lead | See which documents are outdated | I know if my code implies a strategy change that I haven't documented yet. |

## **3\. Functional Requirements**

### **3.1. The Sanitizer (ontos groom)**

*Pre-requisite step to ensure "Garbage In" doesn't happen.*

* **FR-1.1 Monolith Detection:** System MUST identify files exceeding 1,000 lines.  
* **FR-1.2 Split Suggestion:** System SHOULD suggest split points based on H1 headers.  
* **FR-1.3 Header Standardization:** System MUST warn if files lack standard Markdown headers (H1/H2).

### **3.2. The Ontology Builder (ontos init)**

*Transforms a folder into a Graph.*

* **FR-2.1 Auto-Discovery:** System MUST scan a target directory for .md files.  
* **FR-2.2 Heuristic Tagging:** System MUST assign a type based on filename/content keywords:  
  * mission, vision, value $\\rightarrow$ **Level 0 (Kernel)**  
  * strategy, persona, stack $\\rightarrow$ **Level 1 (Strategy)**  
  * roadmap, journey, schema $\\rightarrow$ **Level 2 (Product)**  
  * feature, spec, component $\\rightarrow$ **Level 3 (Atom)**  
* **FR-2.3 Non-Destructive Write:** System MUST NOT overwrite content. Metadata MUST be stored in YAML frontmatter.

### **3.3. The Visualizer (ontos map)**

*Visual verification of the graph.*

* **FR-3.1 ASCII Tree:** System MUST output a CLI-based tree view of the hierarchy.  
* **FR-3.2 Relationship Display:** Output MUST visually indicate parent-child relationships (indentation).

### **3.4. Smart Context Retrieval (ontos context)**

*The core value proposition.*

* **FR-4.1 Natural Language Input:** System MUST accept a user query string (e.g., "Refactor stripe checkout").  
* **FR-4.2 Keyword Matching:** System MUST identify the "Active Task Node" via keyword search.  
* **FR-4.3 Tiered Assembly:** System MUST construct the final output using the **Pruning Algorithm**:  
  1. **Kernel Layer:** 100% of Mission/Values nodes.  
  2. **Focus Layer:** 100% of the Active Task Node.  
  3. **Graph Layer:** Relevant snippets (first 2 paragraphs) of Parent Nodes (e.g., Strategy).  
* **FR-4.4 Clipboard Output:** System MUST copy the final text block directly to the OS clipboard.

### **3.5. Drift Detection (ontos doctor)**

*Basic integrity checking.*

* **FR-5.1 Timestamp Analysis:** System MUST compare modification times of Parent vs. Child nodes.  
* **FR-5.2 Stale Alerting:** IF Parent.mod\_time \> Child.mod\_time, System MUST flag Child as "Stale/Needs Review."

## **4\. The "Startup Standard" Ontology**

The system will enforce this hard-coded Directed Acyclic Graph (DAG) logic.

* **Kernel (L0):** Constrains ALL.  
* **Strategy (L1):** Constrains Product & Atoms.  
* **Product (L2):** Constrains Atoms.  
* **Atom (L3):** Implementation layer.

**Edge Logic:**

* depends\_on: Explicit dependency (defined in YAML).  
* implies: Heuristic dependency (inferred by file structure).

## **5\. Technical Constraints (MVP)**

* **Language:** Python 3.10+  
* **Database:** **None.** The File System \+ Frontmatter is the database.  
* **Graph Library:** NetworkX (for in-memory traversal).  
* **Parsing:** PyYAML (metadata) \+ Regex/AST (header parsing).  
* **Interface:** Terminal / Command Line only.  
* **OS Support:** MacOS, Linux, Windows (WSL).

## **6\. Success Metrics**

* **Token Reduction:** Average context payload should decrease by \>70% compared to "upload all files."  
* **Setup Time:** Time from pip install to ontos context \< 2 minutes.  
* **Accuracy:** "Smart Context" includes the correct "Strategy" parent node \>90% of the time.