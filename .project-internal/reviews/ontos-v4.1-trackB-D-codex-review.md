**Verdict Summary**

| Item | Result |
|---|---|
| Overall verdict | Needs fixes |
| Full test confirmation | `python3.14 -m pytest tests -v --tb=short` => `1103 passed, 2 skipped`; `python3.14 -m pytest .ontos/scripts/tests -v --tb=short` => `152 passed`; total `1255 passed, 2 skipped` |
| Reviewer 1 | Blocking `read_only` registration break; minor test-quality concerns |
| Reviewer 2 | Confirms `read_only` break, missing `workspace_id` enforcement, bundle gap |
| Reviewer 3 | Confirms `read_only` break and bundle gap as implementation drift |

**Blocking Issues**

1. `read_only=True` still advertises all four write tools in `tools/list`.
   [server.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/server.py#L163) always calls `_register_write_tools(...)`, and I reproduced `list_tools()` returning `scaffold_document`, `log_session`, `promote_document`, and `rename_document` under `read_only=True`. The current tests only cover call-time refusal, not registration-time stripping: [test_write_tools.py](/Users/jonathanoh/Dev/Ontos-dev/tests/mcp/test_write_tools.py#L244), [test_rename_document.py](/Users/jonathanoh/Dev/Ontos-dev/tests/mcp/test_rename_document.py#L345). Cross-reviewer confirmation: Reviewer 1, Reviewer 2, Reviewer 3.

2. Track B's bundle-config work did not land.
   [tools.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/tools.py#L411) still forwards only `token_budget`; [portfolio_config.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/portfolio_config.py#L19) and [portfolio_config.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/portfolio_config.py#L26) still use the old `8192 / 5 / 14` defaults; [bundler.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/bundler.py#L31) still defaults the same way. That misses the A4 requirement to wire `bundle_token_budget`, `bundle_max_logs`, and `bundle_log_window_days` and update defaults to `8000 / 20 / 30`. Cross-reviewer confirmation: Reviewer 2, Reviewer 3.

3. The write tools rebuild portfolio state with a non-canonical workspace slug and can silently leave the index stale under basename collisions.
   Both single-file and rename preflight derive `slug = slugify(workspace_root.name)` in [writes.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/writes.py#L146) and [rename_tool.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/rename_tool.py#L181), then swallow rebuild failures in [writes.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/writes.py#L160). The addendum binds workspace identity to `scanner.slugify + allocate_slug` for collision handling: [ontos-v4.1-spec-addendum-v1.2.md](/Users/jonathanoh/Dev/Ontos-dev/.project-internal/reviews/ontos-v4.1-spec-addendum-v1.2.md#L44). I reproduced this with two indexed repos named `workspace`: `scaffold_document()` on the second repo returned success while `_rebuild_safely` logged `sqlite3.IntegrityError: UNIQUE constraint failed: projects.path`, and the portfolio index for `workspace-2` never picked up the new file. Cross-reviewer confirmation: lead only.

**Should-Fix**

- Missing `workspace_id` still falls back to the current workspace.
  [writes.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/writes.py#L143) and [rename_tool.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/rename_tool.py#L178) call `validate_workspace_id(...)` without `require=True`, while the Track B design explicitly says missing `workspace_id` must return a structured error and not fall back: [TrackB-Design.md](/Users/jonathanoh/Dev/Ontos-dev/.project-internal/v4.1/phaseB/TrackB-Design.md#L182), [TrackB-Design.md](/Users/jonathanoh/Dev/Ontos-dev/.project-internal/v4.1/phaseB/TrackB-Design.md#L203). Cross-reviewer confirmation: Reviewer 2.

- The single-file write tools implement A3 as rebuild-on-error only, not rollback-then-rebuild.
  [writes.py](/Users/jonathanoh/Dev/Ontos-dev/ontos/mcp/writes.py#L174) catches `commit()` failure and only calls `_rebuild_safely(...)`. The authoritative addendum says every write tool must rebuild after rollback of failed writes: [ontos-v4.1-spec-addendum-v1.2.md](/Users/jonathanoh/Dev/Ontos-dev/.project-internal/reviews/ontos-v4.1-spec-addendum-v1.2.md#L59). This is partly a doc inconsistency, because the Dev 2 subsection of the Track B implementation spec softened that to rebuild-on-error only: [v4.1_TrackB_Implementation_Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.project-internal/v4.1/phaseB/v4.1_TrackB_Implementation_Spec.md#L146). Cross-reviewer confirmation: lead only.

**Minor**

- Several new tests are source-inspection or symbol-identity assertions rather than behavioral regressions: [test_write_tools.py](/Users/jonathanoh/Dev/Ontos-dev/tests/mcp/test_write_tools.py#L474), [test_context_contention.py](/Users/jonathanoh/Dev/Ontos-dev/tests/test_context_contention.py#L272), [test_rename_document.py](/Users/jonathanoh/Dev/Ontos-dev/tests/mcp/test_rename_document.py#L368). Reviewer 1 flagged these; I agree they are weaker than the multiprocessing and end-to-end cases elsewhere in the PR.

**Agreement Analysis**

- Consensus: `read_only` registration is broken. All three reviewers confirmed it.
- Consensus: bundle-config wiring/defaults are still missing. Reviewers 2 and 3 confirmed it; I verified it locally.
- No reviewer disputed another reviewer's findings.
- Single-reviewer findings preserved: missing `workspace_id` enforcement (Reviewer 2), brittle source-inspection tests (Reviewer 1), slug-collision stale-index bug and the A3 rollback gap (lead).
- Verified with no finding: `owns_lock=False` call sites are present, the A1 regression tests are substantive, the `build_rename_plan` equivalence test is meaningful, and call-time `E_READ_ONLY` refusal exists for all four write tools.

**Required Actions**

1. Skip `_register_write_tools(...)` entirely when `read_only=True`, and add a `list_tools()` regression test.
2. Wire `load_portfolio_config()` into `get_context_bundle()`, pass all three bundle fields through, and update defaults/template text to `8000 / 20 / 30`.
3. Stop deriving rebuild slugs from `workspace_root.name`; use the canonical portfolio slug, including collision suffixes, on every write-tool rebuild path.
4. Decide whether `workspace_id` is truly required for write tools; then align code and tests with the chosen contract. Right now the design note and implementation disagree.
5. Tighten tests away from `inspect.getsource()` / symbol-identity assertions where behavior can be checked directly.
