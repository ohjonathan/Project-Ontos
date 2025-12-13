<!--
Ontos Context Map
Generated: 2025-12-13 12:38:46 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
# Ontos Context Map
Generated on: 2025-12-13 21:38:46
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal`

## 1. Hierarchy Tree
### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **decision_history** (decision_history.md) ~424 tokens
  - Status: active
  - Depends On: mission
- **v2_strategy** (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission

### ATOM
- **schema** (schema.md) ~314 tokens
  - Status: active
  - Depends On: v2_strategy

### LOG
- **log_20251213_cleanup_broken_links** (2025-12-13_cleanup-broken-links.md) ~417 tokens
  - Status: active
  - Impacts: schema
- **log_20251213_documentation_compaction** (2025-12-13_documentation-compaction.md) ~902 tokens
  - Status: active
  - Impacts: schema, v2_strategy, mission
- **log_20251213_gemini_feedback_fixes** (2025-12-13_gemini-feedback-fixes.md) ~416 tokens
  - Status: active
  - Impacts: schema


## 2. Recent Timeline
- **2025-12-13** [fix] **Gemini Feedback Fixes** (`log_20251213_gemini_feedback_fixes`)
  - Impacted: `schema`
  - Concepts: gemini-review, installation, ontos-init, documentation-consistency
- **2025-12-13** [chore] **Documentation Compaction** (`log_20251213_documentation_compaction`)
  - Impacted: `schema`, `v2_strategy`, `mission`
  - Concepts: documentation-compaction, archive, token-reduction, minimal-example
- **2025-12-13** [chore] **Cleanup Broken Links** (`log_20251213_cleanup_broken_links`)
  - Impacted: `schema`
  - Concepts: cleanup, broken-links, legacy-removal, documentation

## 3. Dependency Audit
No issues found.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| decision_history | [decision_history.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/decision_history.md) | strategy |
| log_20251213_cleanup_broken_links | [2025-12-13_cleanup-broken-links.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_cleanup-broken-links.md) | log |
| log_20251213_documentation_compaction | [2025-12-13_documentation-compaction.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_documentation-compaction.md) | log |
| log_20251213_gemini_feedback_fixes | [2025-12-13_gemini-feedback-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_gemini-feedback-fixes.md) | log |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
