---
id: ontos_product_roadmap
status: draft
type: product
---

# **Ontos Product Roadmap: From CLI to OS**

## **Phase 1: The Foundation (v0.1 \- MVP)**

Theme: "Clean Data, Trusted Context"  
Goal: Ensure the source data is valid ("Sanitization") before building the graph, then prove that "Pruning" works better than "Stuffing."

### **Features**

* **1\. Document Sanitizer (ontos groom):**  
  * *The Gatekeeper.* Runs before initialization.  
  * **Monolith Splitter:** Detects massive files (\>1000 lines) and suggests logical split points based on headers.  
  * **De-Duplication:** Identifies overlapping content (e.g., "Problem Statement" exists in both pitch.md and strategy.md).  
  * **Format Enforcer:** standardized Markdown headers so the Ontology Builder can actually read them.  
* **2\. Ontology Builder (ontos init):**  
  * **Auto-Detection:** Scans directory, identifying dependencies based on content (e.g., "This file mentions 'Stripe', linking to 'Monetization'").  
  * **Visualization:** ontos map generates an ASCII tree showing the relationship graph.  
* **3\. Smart Context Loader (ontos context):**  
  * **Task-Specific Loading:** "I'm debugging payments" \-\> Loads monetization.md \+ payment\_flow.md (Ignores marketing.md).  
  * **Tiered Injection:** Combines Global Constraints (Mission) with Local Context (Task).  
  * **Output:** Formatted text block copied to system clipboard.  
* **4\. Drift Detection (ontos doctor):**  
  * **Impact Analysis:** "Change in pricing.md detected. This affects 3 child documents."  
  * **Status:** Reports the drift but does *not* auto-fix it yet.

### **Technical Dependencies**

* Python 3.10+  
* PyYAML / NetworkX  
* **No Database:** File system is the database.

## **Phase 2: Integration & Memory (v1.0)**

Theme: "Workflow Friction Removal"  
Goal: Move Ontos from a "tool you switch to" to a "layer that lives where you work." Capture the "Lost Knowledge" of AI chats.

### **Features**

* **Universal Conversation Tracker:**  
  * **The Problem:** Decisions made in ChatGPT are lost when the tab closes.  
  * **The Solution:** A centralized log (.ontos/history.json) searchable via CLI.  
  * **Implementation:**  
    * *VS Code Extension:* Auto-logs chat sessions in the sidebar.  
    * *CLI Wrapper:* ontos chat "query" logs the prompt and the generated context.  
  * **Query:** "When did we decide on webhooks?" \-\> Searches the conversation history.  
* **VS Code / Cursor Extension:**  
  * Sidebar visualization of the Ontology Graph.  
  * Right-click "Copy Smart Context."  
* **Multi-Platform Push:**  
  * ontos context \--json: Output tailored for LangChain, AutoGPT, or API payloads.  
  * **Local Embeddings:** "True" semantic search (finding "billing" when you search "payments").

### **Technical Dependencies**

* **Local Vector Store:** Lightweight integration (e.g., LanceDB).  
* **TypeScript:** For the VS Code extension.

## **Phase 3: The Write-Back (v2.0)**

Theme: "The Self-Healing Repository"  
Goal: Close the loop. Allow Ontos to safely update documentation based on code changes and chat decisions.

### **Features**

* **Change Propagation II (One-Click Update):**  
  * **Interactive Patching (ontos patch):**  
  * System prompts: "Monetization changed. Update landing\_page.md to reflect new 3.3% fee?"  
  * User Action: \[Confirm\] \-\> Ontos writes the file.  
* **Reverse-Sync (Code-to-Doc):**  
  * Parses code structures to flag outdated documentation.  
  * *Scenario:* You change a variable const FEE \= 0.04 in code. Ontos flags monetization.md.  
* **Multi-Agent Protocol:**  
  * Shared state locking to prevent race conditions when multiple agents access the graph.

### **Technical Dependencies**

* **LLM API Integration:** Requires API keys to generate diffs.  
* **AST Parsing:** For deep code analysis.

## **The Critical Path (Dependencies)**

1. **Sanitization (Phase 1\) is the prerequisite.** You cannot build a graph on dirty data. ontos groom must be run before ontos init.  
2. **The Ontology (Phase 1\) is the blocker.** If the system doesn't understand dependencies, "Smart Context" is just keyword search.  
3. **Trust (Phase 1\) blocks Automation (Phase 3).** Users must trust the *Read* accuracy before allowing *Write* access.  
4. **Extensions (Phase 2\) block Conversation Tracking.** You cannot effectively track conversations without being inside the IDE or wrapping the API.