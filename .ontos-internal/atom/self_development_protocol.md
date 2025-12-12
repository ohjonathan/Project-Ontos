---
id: self_dev_protocol
type: atom
status: draft
depends_on: [v2_architecture]
---

# Ontos Self-Development Protocol

## 1. Architecture Link
Operationalizes [v2_architecture](architecture.md) for the development process.

## 2. The Golden Rule
**"Eat your own dogfood, but don't choke."**
We use Ontos to document Ontos, but we have safeguards to ensure we don't break the tool we are using.

## 3. Directory Structure
-   `.ontos-internal/`: **Project Context** (How to build Ontos). Only visible to contributors.
-   `docs/`: **User Documentation** (How to use Ontos). Visible to everyone.

## 4. Protocols

### 4.1 Contributor Mode
When working on the Ontos repo, the system automatically detects `.ontos-internal/` and sets context to **Contributor Mode**.
-   **Context Map:** Generated from `.ontos-internal/`
-   **Logs:** Saved to `.ontos-internal/logs/`

### 4.2 Safe Script Editing
**Risk:** Editing `ontos_generate_context_map.py` can break your ability to generate context.
**Mitigation:**
1.  Run tests: `pytest tests/`
2.  Manual verify: `python3 .ontos/scripts/ontos_generate_context_map.py`
3.  **NEVER** commit broken scripts.

### 4.3 Schema Migration
When changing the schema (e.g., adding `type: log`), ensure backward compatibility in `ontos_generate_context_map.py` so it can still read v1 docs.
