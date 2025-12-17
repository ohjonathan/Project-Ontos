# Review: Ontos v2.5 "Promises" Implementation Plan (V2)

## Findings
- Context map warning dependencies: The added `check_consolidation_status()` references `resolve_config`, `get_log_count`, and `get_logs_older_than`, but `ontos_generate_context_map.py` does not currently expose/import those helpers. The plan should specify imports or shared util location to avoid runtime NameErrors.
- ASCII consistency: Pre-commit output still uses emoji (`📦`, `⚠`). If the rationale is full ASCII compatibility (Windows/CI), consider plain-text equivalents to avoid mojibake.
- Auto-staging scope: `git add <logs_dir>` will stage all changes under logs, including unrelated/untracked files. If users keep WIP logs there, commits may unintentionally include them. Consider narrowing staging to files actually touched by consolidation (e.g., from consolidator output) or skipping untracked files.
- Test plan numbering: Two sections are labeled 7.2; minor, but can confuse execution order.

## Open question
- Should `get_logs_older_than`/log-count helpers be centralized in a shared module (e.g., `ontos_lib`) and imported in both the hook and context-map script to prevent duplication and drift?
