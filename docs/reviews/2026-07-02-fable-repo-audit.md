---
id: project-ontos-fable-repo-audit-2026-07
type: review
status: complete
---

# Ontos v4.7.0 — Comprehensive Repo Audit

*HEAD `589d919` · date 2026-07-02 · auditor: Claude Fable 5 · method: 15-dimension multi-agent audit with adversarial verification. Every finding below survived at least one hostile refutation pass; P0s survived two.*

---

## 1. Executive summary

**Overall health grade: C+**

Ontos is a genuinely capable, self-hosting documentation-integrity tool with a well-architected modern core. Where it is good, it is very good; where it is weak, the weakness is systemic rather than local. The grade is dragged out of B range by three things: one confirmed data-corruption P0 that fires on documented, everyday write commands; a cluster of write-path and cross-surface data-integrity P1s; and a legacy substrate that occupies ~50% of the tracked tree and still gates every commit with frozen v2.8.0 logic. It is held out of C/C- range by the quality of the newest slices, a real 1,442-test suite at 77.76% coverage (core modules mostly >90%), and disciplined foundations (temp-file+rename writes, workspace locking, `yaml.safe_load` everywhere, clean packaging).

**Top 5 actions (do these first):**

1. **Replace the hand-rolled YAML serializer** (`D2b-roundtrip-3`, the lone P0). It silently corrupts user files on `ontos promote`, `ontos migrate`, and MCP `promote_document`. Serialize via `yaml.safe_dump` (or the existing `io/yaml.dump_yaml`) and add a re-parse assertion before every write. This also underpins the `ontos log` corruption (`D3b-structure-1`).
2. **Rewire pre-commit/CI off `.ontos/scripts/` and delete the vendored fork** (`D5a-repo-redundancy-1`, `-2`). Every commit is currently validated by a frozen v2.8.0 copy of the package, not the shipped v4.7.0 rules — the documented root cause of pre-commit failing on `main` while the modern CLI passes.
3. **Remove the arbitrary-code-execution path from `ontos doctor`** (`D4b-trust-1`). Diagnostics must not spawn a `command` read verbatim from a repo-committed `.cursor/mcp.json`.
4. **Fix the body-reference scanner** (`D1a-graph-link-1`, `-6`). `ontos rename` silently leaves aliased/heading wikilinks dangling, and `ontos link-check` on the flagship repo itself exits 1 with 50/50 false positives — the tool fails its own gate.
5. **Reconcile counts, exit codes, and envelope status across CLI and MCP** (`D1b-counts-1..4`, `D7-cli-consistency-1/3/4`). Sibling commands report different numbers for identical repo state, defeating the machine-consumption contract that is the product's core value proposition.

**Honest overall assessment of the Opus-built codebase.** The modern core is competently engineered: the dependency-graph engine, the shared validation primitives introduced in #133, the MCP write-tool locking substrate, and the v4.7 link-diagnostics work are all sound, and the test suite is real rather than theater. The trouble is that this strong core sits on top of a large, half-retired v2 substrate the project never finished removing, and that its many parallel surfaces (CLI vs MCP; map vs activate vs link-check vs doctor) were each built at different times and never reconciled — so they now disagree about counts, exit codes, envelope shapes, and even where session logs are written. The single most dangerous defect is small and eminently fixable (a non-YAML-safe serializer). Read as a whole, this is a codebase that grew faster than it was consolidated: excellent in its newest slices, accreted and self-contradictory across its older ones.

**Register totals:** 1 P0, 27 P1, 63 P2 confirmed; 1 finding refuted. (A handful of entries absorb additional same-root-cause raw findings, noted inline as "merges …".)

---

## 2. Answers to your seven questions

### Q1 — Constructive feedback: what is critical, what can improve, how

**Critical (fix before the next release):** the serializer P0 (`D2b-roundtrip-3`) is the only true ship-blocker — it turns valid user documents into unparseable or type-flipped YAML on three documented write paths, silently. Everything else is schedulable, but the following P1 clusters are close behind and should not linger: silent data corruption from writes (`D2b-roundtrip-1`, `-4`; `D3b-structure-1`; `D2a-write-safety-2/3/5`), the machine-consumption contract breaks (`D7-cli-consistency-1/3/4`, `D1c-envelope-4`, `D1b-counts-1..4`), the RCE in `doctor` (`D4b-trust-1`), and the legacy-fork commit gating (`D5a-repo-redundancy-1/2`).

**What can improve, and how:** the CLI/MCP surfaces need one shared serializer, one shared frontmatter splitter, one exit-code taxonomy, and one envelope-status rule (see roadmap §5). The `commands/log.py` hand-rolled paths should be deleted in favor of the shared helpers the MCP side already uses. Config type validation should cover `paths.*`/`scanning.*` (`D4a-config-2`). Documentation aimed at agents (Agent Instructions, Manual §1/§6) needs a from-scratch rewrite against `cli.py` registrations.

**What is done well — say so.** This is a fair peer review, and several dimensions came back clean or strong:
- **Graph orchestration** (`D1a` summary): no dict mutation during iteration, no stale caching, linear regexes (no catastrophic backtracking), `--limit` CLI-guarded.
- **#133 shared count primitives** (`D1b` summary) genuinely fixed the historical query-vs-validator orphan split; bounded-sample grouping never hides totals.
- **Write substrate** (`D2a`, `D2b` summaries): every mutation goes through temp-file+rename; MCP writes run under a flock; path containment held up under active attack (traversal, `~`, absolute `logs_dir` all rejected); `content_hash.py` is sound; retrofit/rename byte-preservation and line-ending detection are well designed.
- **Security posture** (`D4b` summary): `yaml.safe_load` exclusively, no `shell=True`/`os.system`, fixed git argv, clean wheel packaging (`.ontos-internal/`, `docs/`, `.ontos/` cannot ship).
- **Test suite** (`D6a`/`D6b` summaries): the big MCP test files run real servers against real git repos and assert on-disk/git state; `validation.py` 96.9%, `graph.py` 94.9%, `writes.py` 90.6%.

### Q2 — Quality/execution/purpose-fit of the Opus-authored slices (per version-slice)

Fable authored only the v4.7.0 slice; everything else is Opus. Attribution below is inferred from the file/feature churn map in Appendix C, not per-line `git blame`, so cross-slice findings are flagged explicitly. Of 88 confirmed findings, **81 land in Opus-authored slices and 7 in the Fable slice.**

- **Opus 4.5 — foundational core + CLI + commands + v2-era docs + the legacy migration layer (v2.x→v3.2): ~54 confirmed findings. Worst: `D2b-roundtrip-3` (the P0).** This slice carries the structural debt: the non-YAML-safe serializer (`D2b-roundtrip-3`), the copy-pasted `split('---',2)` family (`D3a-parsers-3`), the divergent fallback parser (`D3a-parsers-2`), `commands/log.py`'s hand-rolled frontmatter and dead `ontos_config` import (`D3b-structure-1/2`), incomplete config validation (`D4a-config-2`), the exit-code overload and 1,880-line `cli.py` boilerplate (`D7-cli-consistency-3`, `D3b-structure-6`), the phantom-modes Manual (`D8-docs-clarity-5`), the stale Agent Instructions (`D8-docs-clarity-1`), and the entire `.ontos/scripts` legacy layer + vendored fork that still gates commits (`D5a-repo-redundancy-1/2`). Purpose-fit: the *design* is right (surgical edit helpers exist, shared serializer exists) but the older command code doesn't use its own better primitives. This is the slice most in need of consolidation.
- **Opus 4.6 — MCP write-tools / portfolio / retrofit / rename (v3.3→v4.3): ~14 confirmed findings. Worst: `D2a-write-safety-3` (MCP rename's forced-LIBRARY scope is guard-only → duplicate IDs and dangling cross-scope refs, reproduced end-to-end).** Also `D2a-write-safety-5` (rename's `git checkout -- .` rollback can revert unrelated user edits made after the pre-lock clean check) and `D2b-roundtrip-1` (the shared surgical helper bakes U+FFFD into any non-UTF-8 file). Execution quality here is high on the happy path — the locking and A3 rollback design is thoughtful — but the failure/edge paths are under-hardened, and `rename_tool.py` copy-pastes ~115 lines of `writes.py` (`D3b-structure-3`). The shipped personal-machine portfolio default (`D4a-config-1`) also lives here.
- **Opus 4.7 — graph / body_refs / mcp tools / doctor / activation (v4.4→v4.6): ~13 confirmed findings. Worst: `D4b-trust-1` (arbitrary code execution via `ontos doctor` reading a repo-committed `.cursor/mcp.json`).** The body-reference scanner (`body_refs.py`) is the recurring theme: silent partial renames on aliased wikilinks (`D1a-graph-link-1`), the non-CommonMark fence machine (`D1a-graph-link-2`), body-relative line numbers (`D1a-graph-link-3`), and the source-file/stem-vs-id false positives whose normalization lives here (`D1a-graph-link-6`, straddling into Fable's classifier). Plus the `map`-vs-`activate` concept-vocabulary count split (`D1b-counts-1`) and the graph recursion cliff (`D1a-graph-link-4`). This slice's core algorithms are solid (graph orchestration scored clean); the defects are in edge-case correctness and the trust boundary.
- **Fable 5 — v4.7.0 link-diagnostics / link-check / warning-grouping + client docs (v4.7.0): 7 confirmed findings, the cleanest slice. Worst: `D7-cli-consistency-4` / `D1b-counts-4` (the new link-check surface reports findings as `status:"success"` while sibling commands report `error`, and `maintain`'s frontmatter-only scan vouches "No broken references" while `link-check` exits 1 on the same repo).** Notably, most Fable findings are *consistency gaps the new link-check surface exposed in older commands* rather than fresh bugs it introduced, plus one provably output-neutral perf pass it added (`D1a-graph-link-7`) and the exit-code-derived `result_status` (`D1c-envelope-5`, P2). The one clear execution miss is docs-scope: the v4.7 doc-refresh commit `b458ab6` fixed only the MCP tool table and left the stale Agent Instructions untouched (`D8-docs-clarity-1`).

**Net purpose-fit read:** the Opus slices built the right architecture but repeatedly (a) shipped commands that bypass their own better shared helpers, and (b) added a new parallel surface without reconciling it with the existing ones. Fable's slice is materially cleaner but inherited — and in a couple of cases surfaced — the cross-surface contradictions rather than closing them.

### Q3 — Redundant work: what can be reduced/removed

The repo carries roughly 60% dead-or-duplicated weight by file count, but very little can be *plain-deleted* because legacy paths remain load-bearing.

- **`.ontos/scripts/` (8,781 lines of v2 scripts + a 3,053-line vendored fork of the whole package)** still gates every commit and CI run and is coupled to 11 test files (`D5a-repo-redundancy-1/2`). 63% of the v2 scripts already exist verbatim in the archive. **Rewire → then archive**, never plain-delete.
- **Genuinely dead and safe to remove:** `ontos/_hooks/*` (ships to PyPI, imports a nonexistent `ontos._scripts`, `D5a-repo-redundancy-3`); `ontos/_templates/` (dead package data, `D5b-dead-code-2`); 11 tracked `.bak` files that violate the repo's own `.gitignore` (`D5a-repo-redundancy-6`); `io/obsidian.py` (dead duplicate, `D5b-dead-code-6`); a dozen v2-compat functions in `paths.py` (`D5b-dead-code-3`); three uncalled command wrappers + two re-export shims (`D5b-dead-code-8`); six scattered dead helpers (`D5b-dead-code-10`, worst: a second MCP error-envelope helper `tool_error`); `_create_directories` (`D5b-dead-code-9`); the dead `required_version` config key (`D5b-dead-code-7`); the dead `_cmd_export` handler pinned by a test asserting the wrong behavior (`D3b-structure-7`).
- **Structural duplication to collapse:** the 5-copy MCP exception cascade (`D3b-structure-4`), `rename_tool.py`↔`writes.py` substrate (`D3b-structure-3`), the double cross-workspace guard (`D3b-structure-5`), and the output-neutral known-ID body-scan pass costing ~65% of `body_scan` time (`D1a-graph-link-7`).
- **Extraction candidates:** `.ontos-internal/` (643 files, 50.5% of tree, 7.4M) and `.project-internal/` (25 stale files) — but note the verifier corrected the "only two couplings" premise: `.ontos-internal/` is the actively dogfooded contributor-mode store with ~50 live references, so only the frozen `archive/` (460 files) is cleanly extractable (`D5a-repo-redundancy-4`).

### Q4 — Code smells, anti-patterns, God classes/functions

- **`cli.py` is the God module:** 1,880 lines, 27 `_register_*` + 33 `_cmd_*` functions repeating three motifs (25 JSON-tail duplicates, 21 `getattr(args,"scope",None)` copies), with observable copy-paste drift — `tree -f` triggers `map`'s deprecation warning against `tree`'s own flag, `validate` silently drops `--portfolio` (`D3b-structure-6`). The `getattr`-default idiom makes missing registrations fail *silently* (wrong behavior) rather than loudly.
- **`commands/maintain.py`** (486 stmts) is the largest command module and mixes many concerns.
- **Duplicate error-envelope helpers** in the MCP layer (`tool_error` vs `_tool_error_result`, `D5b-dead-code-10`) invite divergent shapes.
- **Dead configuration arms** that mislead maintainers: `severity_map:{"broken_link":"warning"}` is never consulted because `depends_on` always wins the lookup (`D1b-counts-6`); the unreachable `circular_severity` ternary in `build_graph` (`D1a-graph-link-9`); the `sys.argv` string-scan workaround for argparse inheritance that misfires on positionals after `--` (`D7-cli-consistency-10`).
- **Latent engine sharp edges** in `context.py`: two buffered writes to the same path make `commit()` raise *after* applying the write (`D2a-write-safety-9`); locale-dependent write encoding (`D2a-write-safety-7`); test infra performs `sys.path`/`sys.modules` surgery at import time (`D6b-test-quality-9`).

### Q5 — Test suite evaluation (unit vs integration), gaps in critical logic

Suite is green (1,442 passed, 2 skipped) at **77.76%** over 13,521 statements. The "untested core" fear is largely false: `validation.py` 96.9%, `graph.py` 94.9%, `frontmatter.py` 89.8%, `content_hash`/`warning_groups` 100% (earlier confusion traced to basename collisions with the vendored legacy copies). Integration coverage is strong where it matters most — the MCP write-tool tests run real servers against real git repos and assert on-disk/git state.

**The real gap is structural: coverage concentrates on pure core functions while shipped WRITE paths and user-mode (non-dogfood) branches are dark.**
- `commands/promote.py` at **33.3%** — the entire file-rewrite chain is uncovered (`D6a-test-gaps-3`, folded into `D2b-roundtrip-4`).
- Git-hook strict-mode blocking (`return 1`, the feature's whole point) has **no test** (`D6a-test-gaps-4`).
- `paths.py` user-mode/back-compat resolution — which decides where PyPI users' logs and archives go — is untested; only contributor mode is dogfooded (`D6a-test-gaps-5`).
- The MCP fail-closed guards (`is_workspace_clean`/`rollback_path`) have no pins on the closed direction (`D6a-test-gaps-9`).
- **Digging inside the gaps found real latent defects**, proving they aren't theoretical: block-style YAML lists silently dropped by the exported decision-history parser (`D3a-parsers-2`), empty git diff making `suggest_impacts` propose every document (`D6a-test-gaps-2`), `write_config` emitting unparseable TOML (`D6a-test-gaps-8`).
- **Rotted test infrastructure:** golden-master harness hard-skipped since v3.0 (`D6a-test-gaps-6`), `--mode user` fixture broken since `ontos_init.py` was deleted (`D6b-test-quality-2`), a vacuous test with commented-out assertions and committed LLM narration (`D6b-test-quality-1`), three `pass`-body stubs (`D6b-test-quality-6`), dead golden fixtures loaded but never compared (`D6b-test-quality-5`), an unconsumed `legacy` pytest marker (`D6a-test-gaps-10`).

### Q6 — Does sensitive configuration rely on hardcoded values or environment variables

Mixed, and the hardcoding is the problem.
- **Hardcoded personal-machine layout ships as the default:** `portfolio_config.py` bakes the author's `~/Dev`, `~/Dev/.dev-hub/registry/projects.json`, and `~/Dev/archive` into every user's `~/.config/ontos/portfolio.toml`, triplicated across the dataclass defaults, the config template, and the load fallbacks (`D4a-config-1`). It is opt-in (portfolio mode), and the README documents it as an editable template, hence P2 — but the default should be neutral.
- **Config type validation is incomplete** (`D4a-config-2`, P1): `paths.*`/`scanning.*` bypass the type table, so a string `skip_patterns` silently empties the context map and a non-string `docs_dir` crashes opaquely.
- **Magic numbers scattered, not env-driven:** the 8000 bundle-token default is written in three independent places (`D4a-config-5`); `log_retention_count` is ignored by `ontos consolidate` with two divergent defaults 15/20 (`D4a-config-3`); `required_version` is parsed but never enforced (`D5b-dead-code-7`).
- **Locale-dependent encoding** on the write choke-point (`D2a-write-safety-7`) is effectively an implicit environmental dependency where readers pin UTF-8 but the writer does not.
- **No secrets/credentials were found hardcoded** — the sensitive-config exposure here is machine-layout and path defaults, not tokens. Env-var usage is minimal and appropriate (e.g., `AUTO_CONSOLIDATE` override).

### Q7 — Concrete recommendations: refactoring, standardizing, improving context clarity

- **Serializer/parser consolidation:** one YAML-safe `serialize_frontmatter` (`D2b-roundtrip-3/-4`, `D3b-structure-1`), one fence-aware `^---$` splitter consumed by all five readers (`D3a-parsers-3`), delete `_fallback_yaml_parse` (PyYAML is a hard dep, so its rationale is dead — `D3a-parsers-2`).
- **CLI/MCP dispatch unification:** a declarative command table to collapse `cli.py` (`D3b-structure-6`); one `_write_common.py` for the MCP substrate (`D3b-structure-3/-4/-5`); route promote/migrate/log through the surgical `frontmatter_edit` helpers (`D2b-roundtrip-4`).
- **Standardize the machine contract:** publish an exit-code taxonomy (`D7-cli-consistency-3`), pick one envelope-status rule (`D7-cli-consistency-4`), migrate the `Tuple[int,str]` wrapper commands to structured `data` payloads (`D7-cli-consistency-5`), fix `map --json` stream discipline (`D7-cli-consistency-1`), align `verify --portfolio` and `env --json` (`D7-cli-consistency-6/-7`).
- **Context clarity for contributors:** add a current `Architecture.md`/`CONTRIBUTING.md` (the two existing arch maps are v3.0-era and unindexed — `D8-docs-clarity-6`), regenerate the root `CLAUDE.md` via `ontos export claude --force` so the two root instruction files stop contradicting (`D8-docs-clarity-8`), rewrite Manual §1/§6 to the real `.ontos.toml` surface (`D8-docs-clarity-5`), and make the Tier-1 map table carry real summaries (`D8-docs-clarity-4`).

---

## 3. Findings register

Effort: S/M/L. Verification: CONFIRMED unless noted. "Double-confirmed" marks the P0 that survived two hostile passes.

## P0 — fix before next release

### D2b-roundtrip-3 — `serialize_frontmatter` emits invalid or semantics-changing YAML for ordinary string values
**File:** `ontos/core/schema.py:370` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED (double-confirmed)** · merges D2a-write-safety-1, D3a-parsers-1, D3a-parsers-5

```
if ':' in value or value.startswith('{') or value.startswith('['):
            return f'{key}: "{value}"'
```

**Claim.** `_serialize_field()` hand-rolls YAML with no escaping. Embedded double quotes in colon-containing strings produce unparseable output; the inline-list branch joins items with `, ` without quoting, so an item containing a comma re-splits; quoted scalars lose their quotes so `"4.10"→4.1`, `"007"→7`, `"no"→False` on reload; and values starting with `#` serialize as a YAML comment, reloading as `None`. Fired on real user frontmatter by `ontos promote` (promote.py:141), `ontos migrate` (migrate.py:204), and MCP `promote_document` (writes.py:627).

**Impact.** A file valid before promotion becomes unparseable afterward (dropped from the graph as `parse_error` on the next `map`), or its values silently change type/content — dependency IDs with commas split into phantom deps, version strings become floats, notes become null. The MCP path executes autonomously with no human in the loop.

**Fix.** Serialize scalars/lists with `yaml.safe_dump` (the unused `io/yaml.dump_yaml` already exists), or adopt the more careful `_serialize_item` quoting from `retrofit.py:588-607`. Add a re-parse assertion before every rewrite.

**Verification evidence.** Both passes reproduced all four modes via the real `serialize_frontmatter → parse_frontmatter_content` round-trip: `{'title':'Q3 plan: "final" version'}` → `title: "Q3 plan: "final" version"` → `ValueError` on reload; `{'depends_on':['design_v1,final']}` → reloads as two items; `{'version':'4.10','build':'007','flag':'no'}` → `{4.1, 7, False}`; `{'note':'#42 follow-up'}` → `None`. All three write paths re-serialize the FULL parsed user frontmatter (`migrate.py:204` copy, `promote.py:141` via `curation.py:416`, `writes.py:627`). Second pass: *"Silent data corruption plus unparseable-output-on-valid-input across documented commands (promote, migrate) and an MCP write tool, operating on the user's own trusted files, is a canonical ship-blocking data-integrity defect. P0 holds; unlike D4b there is no documented exclusion and no security-boundary escape hatch."*

---

## P1 — schedule within 1–2 releases

### D4b-trust-1 — `ontos doctor` executes attacker-controlled command from repo-committed `.cursor/mcp.json` (arbitrary code execution)
**File:** `ontos/core/mcp_shared.py:375` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        result = subprocess.run(
            [command, *args],
            input=payload,
```

**Claim.** `probe_mcp_initialize` runs `subprocess.run([command, *args])` with `command`/`args` taken verbatim from `repo_root/.cursor/mcp.json`. `ontos doctor` unconditionally calls `check_cursor_mcp` (doctor.py:924) → `inspect_cursor_ontos_config(scope='project')`, which after cheap shape checks (`resolve_executable` succeeds, `'serve' in args`, an absolute existing `--workspace`) calls `probe_mcp_initialize` (cursor_mcp.py:262). Padding ignored tokens (`python3 -c '<payload>' serve --workspace /tmp`) satisfies every check while executing arbitrary code.

**Impact.** A victim who clones/opens an untrusted repo and runs `ontos doctor` (a documented troubleshooting command) gets arbitrary local code execution. `.cursor/mcp.json` is routinely committed — a realistic supply-chain RCE.

**Fix.** Do not execute repo-sourced commands during read-only diagnostics. Drop the live probe for project-scoped configs, or gate behind explicit opt-in and only probe when the resolved `command` equals Ontos's own launcher (`resolve_ontos_launcher()`), rejecting any non-managed form.

**Verification evidence.** Reproduced end-to-end: crafted `.cursor/mcp.json` with `command=python3, args=[-c, <writes /tmp/PWNED_ONTOS>, serve, --workspace, <abs>]`; `.venv/bin/ontos doctor` created the marker file. Severity note (why P1 not P0): *"SECURITY.md:59 explicitly documents the exact threat-model exclusion the entire exploit depends on ('Don't run ontos on untrusted repositories'). That places this in the same accepted-risk class as git hooks, Makefiles, npm scripts... It remains a legitimate hardening/defense-in-depth finding — the shape checks give false confidence and the probe silently spawns a committed-config binary with no confirmation."*

### D1a-graph-link-1 — `rename --apply` silently skips aliased/heading wikilinks; link-check mis-reports them
**File:** `ontos/core/body_refs.py:766` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        raw_inner = match.group(0)[2:-2]
        inner = raw_inner.strip()
```

**Claim.** `_iter_wikilink_id_candidates` never splits Obsidian alias (`[[id|Alias]]`) or heading (`[[id#Section]]`) syntax off the inner text, and `_iter_exact_id_matches`' boundary rules reject the id prefix. So `ontos rename old new --apply` rewrites `[[old]]` but silently leaves `[[old|Alias]]` and `[[old#Section]]` dangling, and link-check reports the whole inner string as broken.

**Impact.** Obsidian-style vaults (a first-class Ontos audience) get silent partial renames that corrupt the doc graph, violating the command's advertised "atomic ID rename across frontmatter and body references"; link-check also hard-fails (exit 1) on perfectly valid aliased wikilinks, blocking hooks/CI.

**Fix.** In `_iter_wikilink_id_candidates`, split the inner text on the first `|` and `#` and yield only the id segment with correct span; for rename, treat `|`/`#` as hard trailing boundaries inside `[[...]]`.

**Verification evidence.** Reproduced against the installed v4.7.0 package: `[[beta|The Beta Doc]] and [[beta#Section One]] and [[beta]]` → `link-check --json` reports broken values `beta|The Beta Doc` / `beta#Section One` (exit 1) though `beta` exists; after `rename beta beta2 --apply` ("2 file(s) updated", no skip warning) the body still reads `[[beta|The Beta Doc]] ... [[beta2]]` — two silent dangling refs. Ontos's own `map --obsidian` emits the very `[[filename|alias]]` syntax its scanner cannot handle (map.py:736).

### D1a-graph-link-6 — Relative links to source files and stem/id-mismatched docs flagged broken; the flagship repo's own link-check exits 1 with 50/50 false positives
**File:** `ontos/core/body_refs.py:655` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
    if "/" in target or "\\" in target:
        target = target.replace("\\", "/").rsplit("/", 1)[-1]
    if target.lower().endswith(".md"):
        target = target[:-3]
```

**Claim.** `_normalize_markdown_target` reduces every relative target to its bare basename and compares case-exactly to frontmatter ids, with no file-existence fallback (`_classify_reference`, link_diagnostics.py:669 `if value in active_ids`). Two false-positive classes result: links to non-markdown files (`(ontos/core/graph.py:170)` → pseudo-id `graph.py:170`) and valid `.md` links whose stem differs from the id (`Ontos_Manual.md` id `ontos_manual`).

**Impact.** link-check permanently exits 1 on ordinary engineering docs that link to code, burying real broken references in noise and making the exit code unusable in hooks/CI. The flagship dogfood repo ships in this state.

**Fix.** Before id comparison, resolve the raw relative target against the source doc's directory/repo root: if it exists and is a loaded doc, use its actual id; if it exists but isn't a doc (or is non-`.md`), classify as a file reference (reuse the #134 file-dependency bucket).

**Verification evidence.** Fresh clone at HEAD: `ontos link-check --json` → exit 1, **49** broken body refs (finder's 50 included a leftover untracked working-tree doc), all `body.markdown_link_target`, 42 file-with-line-anchor links + 7 stem-vs-id mismatches, zero true positives. Straddles the Fable classifier: normalization is Opus 4.7 (`body_refs.py`), the missing file-existence fallback is in `link_diagnostics.py` (Fable).

### D2a-write-safety-2 — `rollback_path` deletes tracked files and reports success when `git checkout` fails for unrelated reasons
**File:** `ontos/core/git.py:123` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
            abs_path.unlink()
```

**Claim.** `rollback_path` assumes any non-zero `git checkout -- <path>` means the path is untracked and unlinks it. Checkout can fail for other reasons — most commonly `.git/index.lock` held by a concurrent git process — in which case a TRACKED document is deleted and the function returns `None` (success), so the MCP error envelope never mentions the deletion.

**Impact.** All three single-file MCP write tools (`scaffold_document`, `log_session`, `promote_document`) call this on commit failure. A user whose IDE touches git at the wrong moment ends up with the target document deleted instead of restored, with rollback reported as success.

**Fix.** Determine trackedness explicitly (`git ls-files --error-unmatch <rel>`) before choosing checkout vs unlink; treat checkout failure of a tracked path as rollback *failure*.

**Verification evidence.** Reproduced: with `.git/index.lock` held, `git checkout` exits 128; `rollback_path(root, tracked)` deleted the tracked file and returned `None` while `git ls-files` still listed it. Broader than claimed — in a non-git workspace the same unlink deletes the doc.

### D2a-write-safety-3 — MCP `rename_document`'s forced LIBRARY scope is guard-only: cross-scope collision check bypassed, `.ontos-internal` left inconsistent
**File:** `ontos/mcp/rename_tool.py:430` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
    scope = ScanScope.LIBRARY
```

**Claim.** `build_rename_plan` uses `scope` only for the `if scope == ScanScope.DOCS` cross-scope collision guard; the files rewritten are `snapshot.documents`, built with `scope=None` → config `default_scope`. With default docs scope the collision guard is unconditionally bypassed; with `default_scope=library` the tool rewrites `.ontos-internal` files — contradicting the CB-B3 comment that `default_scope` "must NOT propagate to MCP write tools."

**Impact.** Users with an `.ontos-internal` store get silent graph corruption from the MCP surface: a rename the CLI refuses (`cross_scope_collision`) succeeds via MCP, creating a duplicate document ID across scopes and leaving internal references dangling.

**Fix.** Build the rename snapshot at true LIBRARY scope for MCP (so internal collisions are detected/rewritten consistently), or keep the docs-scope set and pass `scope=ScanScope.DOCS` so the guard fires. Add a parity test.

**Verification evidence.** Both corruption modes reproduced. Docs default: MCP rename `doc_a→doc_b` returned `isError=False`, `updated_files=['docs/a.md','docs/ref.md']`, leaving `.ontos-internal/x.md` with id `doc_b` (duplicate) and `depends_on:[doc_a]` (dangling); CLI refuses with `cross_scope_collision`. Library default: MCP rewrote `.ontos-internal/x.md`, proving `default_scope` DOES propagate. Note: a fix must revisit the pinned regression test `test_rename_scope_forced_library.py` whose "CA ruling" the implementation already contradicts.

### D2a-write-safety-5 — MCP rename rollback runs `git checkout -- .` against a pre-lock clean check, and can revert unrelated user edits
**File:** `ontos/mcp/rename_tool.py:305` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED** (confidence: medium)

```
        reason = _git_checkout_rollback(workspace_root)
```

**Claim.** The clean-worktree precondition that makes `git checkout -- .` "safe" is verified once in `_preflight` (line 198), before the lock is acquired and before the plan phase reads every document. It is never re-verified before the destructive checkout at line 305 (or 519). Any tracked file the user modifies between preflight and rollback is reverted to HEAD, unrecoverably; the rollback is also unscoped.

**Impact.** A user saving an edit to any tracked file (source code included) while an agent-triggered `rename_document` runs loses that edit permanently if the rename's commit then fails for an unrelated reason. The failure envelope reports the commit error, not the collateral revert.

**Fix.** Scope the rollback to the planned file set (`git checkout -- <paths>`), which the plan already enumerates, or re-run `is_workspace_clean` immediately before checkout and downgrade to scoped rollback on failure.

**Verification evidence.** Reproduced: patched `commit` to write to tracked `src/app.py` (simulating an editor save in the window) then raise `OSError(ENOSPC)`; `rename_document` returned `E_INTERNAL` mentioning only "No space left on device", and `src/app.py` was silently reverted to HEAD content.

### D2b-roundtrip-1 — Frontmatter edits permanently bake U+FFFD into files with any non-UTF-8 byte
**File:** `ontos/core/frontmatter_edit.py:51` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED** · merges D2a-write-safety-4

```
decoded = raw.decode("utf-8", errors="replace")
```

**Claim.** `_read_decoded_content()` decodes with `errors="replace"`, and all three write-back consumers (`frontmatter_repair.py:219`, `retrofit.py:492`, `rename.py:682`) write the decoded string back, so every invalid-UTF-8 byte anywhere in the file — including the untouched body — is silently replaced with U+FFFD and committed.

**Impact.** Mixed-encoding docs (latin-1/Windows-1252 accents are common) get their content destroyed by a frontmatter-only edit; the command exits 0 with no warning, so the mojibake gets committed. Affects `ontos maintain --fix-frontmatter-enums --apply`, `retrofit --apply`, `rename --apply`.

**Fix.** Decode strictly in `_read_decoded_content`; let callers convert `UnicodeDecodeError` into an unpatchable-format warning that skips the file. Keep `errors='replace'` only for read-only diagnostics.

**Verification evidence.** Reproduced twice: `maintain --fix-frontmatter-enums --apply` on a doc with body byte `0xE9` → "Updated 1 file(s)", exit 0, body now `Caf\xef\xbf\xbd`; same via `rename --apply`. No U+FFFD guard anywhere; other `errors='replace'` uses are read-only.

### D2b-roundtrip-4 — promote/migrate do full destructive rewrites: comments, key order, quoting, and whole-file line endings lost
**File:** `ontos/commands/promote.py:142` · **Effort:** M · **Owner Q:** 7 · **Verification: CONFIRMED** · merges D6a-test-gaps-3

```
new_content = f"---\n{fm_yaml}\n---{body}"
```

**Claim.** `ontos promote`, `ontos migrate` (migrate.py:207), and MCP `promote_document` (writes.py:627) rebuild the whole frontmatter from the parsed dict instead of using the surgical `frontmatter_edit` machinery that rename/retrofit already share: YAML comments are deleted, keys reordered to schema `field_order`, quoting stripped, and because the file is read via `read_text` (universal newlines) and rewritten in text mode, ALL line endings — body included — are normalized to the platform default.

**Impact.** Editing one field yields a whole-file diff: reviewer comments vanish, CRLF repos churn every line, dumbed-down quoting feeds the type flips in `D2b-roundtrip-3`. Inconsistent with rename/retrofit, which preserve formatting byte-for-byte.

**Fix.** Route promote/migrate/promote_document through `core/frontmatter_edit` (byte-preserving read, targeted line insert/replace with detected line ending).

**Verification evidence.** Real `apply_promotion()` + `ctx.commit()` on a CRLF file with a comment and `version: "4.10"`: comment survived False, CRLF survived False (body included), keys reordered, title requoted, version reparsed as float 4.1. `promote.py:33.3%` coverage — the entire rewrite chain is untested.

### D3a-parsers-3 — The `---` substring split is copy-pasted across five frontmatter splitters; any `---` inside a value truncates parsing
**File:** `ontos/io/yaml.py:60` · **Effort:** M · **Owner Q:** 3 · **Verification: CONFIRMED** · merges D2b-roundtrip-2

```
    parts = content.split('---', 2)
```

**Claim.** All splitters use substring `split('---', 2)` instead of matching fence lines (`^---$`): `io/yaml.py:60`, `frontmatter_edit.py:74`, `frontmatter.py:56`, `history.py:111`, `promote.py:128`. A `---` inside a value — e.g. `title: "phase --- two"` with a proper closing fence (valid per Jekyll/Hugo) — truncates the YAML: the canonical parser raises (doc ejected as `parse_error`), while `_split_frontmatter` mis-splits silently.

**Impact.** Users with legitimate `---` substrings (em-dash runs, date ranges) lose those documents from map/query/health; the edit path's silent mis-split shifts fields into the body. Fixing correctly requires five synchronized changes today.

**Fix.** Introduce one shared fence-aware splitter (first `^---\s*$` after line 0) in `io/yaml.py` (or a new `core/fm_split.py`) and have all five consumers use it; delete the four inline copies as part of parser consolidation.

**Verification evidence.** Reproduced on `title: "phase --- two"`: `parse_frontmatter_content` raises `ValueError('while scanning a quoted scalar')`; `_split_frontmatter` returns frontmatter `'\nid: doc_e\ntitle: "phase '`. Separately `parse_yaml` accepts the same block, proving the split alone is the cause.

### D3b-structure-1 — CLI `ontos log` hand-rolls YAML frontmatter; unescaped `--source`/`--event-type` write unparseable documents (MCP path escapes correctly)
**File:** `ontos/commands/log.py:188` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        f"source: {source}",
```

**Claim.** `_build_frontmatter` builds frontmatter by raw f-string concatenation while the MCP path (`writes.py:_log_session_impl`) uses `serialize_frontmatter`, which quotes YAML-special values. Any `--source`/`--event-type` containing `:` produces a log whose frontmatter fails `yaml.safe_load`.

**Impact.** `ontos log` is the command CLAUDE.md tells every session to run, documented as `-s <tool/agent name>`. A colon-bearing source silently creates a document the next `ontos map` reports as `parse_error` and excludes from the context map, consolidate, and health counts.

**Fix.** Delete `_build_frontmatter` (log.py:174-201) and build the dict + `serialize_frontmatter(fm)` exactly as `writes.py:493-504` does — one serializer for all five writers.

**Verification evidence.** `ontos log "toy session" -e chore -s "agent: claude [test]" --auto` printed success, wrote `source: agent: claude [test]`; `parse_frontmatter_content` raised `ValueError('mapping values are not allowed here')`; `ontos map` reported 1 `parse_error` and the log was absent from the map. (Depends on the same serializer fix as `D2b-roundtrip-3`.)

### D3b-structure-2 — CLI `ontos log` ignores configured `[paths] logs_dir`; MCP honors it — same verb writes to different directories
**File:** `ontos/commands/log.py:113` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        from ontos_config import LOGS_DIR
        logs_dir = Path(LOGS_DIR)
```

**Claim.** `create_session_log` resolves the logs dir via a legacy v2 `import ontos_config` (a module that exists nowhere in installed packages) with a hardcoded `docs/logs` fallback, bypassing both `core/paths.py:get_logs_dir()` and the `.ontos.toml [paths] logs_dir` key. The MCP counterpart (`writes.py:474`) honors config.

**Impact.** Any user who sets `logs_dir` (a key `ontos init` itself writes) gets split-brain logs: CLI writes `docs/logs/`, MCP writes the configured dir; CLI logs then live outside where `consolidate` and log-count helpers look. Only the CLI writes the `.ontos/session_archived` marker, so pre-push behavior also diverges.

**Fix.** Replace log.py:111-122 with `logs_dir = Path(get_logs_dir(repo_root=project_root))`, collapsing three resolvers to one; `writes.py:474` should call the same helper.

**Verification evidence.** With `[paths] logs_dir="notes/journal"`, `ontos log ... --auto` wrote `docs/logs/...` while config and `get_logs_dir()` both resolve `notes/journal`. `ontos init --yes` writes `logs_dir="docs/logs"` into `.ontos.toml`.

### D4a-config-2 — Config type validation is incomplete: `paths.*`/`scanning.*` bypass checks — a string `skip_patterns` silently hides all documents
**File:** `ontos/core/config.py:150` · **Effort:** S · **Owner Q:** 6 · **Verification: CONFIRMED**

```
    list_of_str_requirements = [
        ("validation", "allowed_orphan_types"),
        ("validation", "allowed_orphan_paths"),
        ("validation", "allowed_external_dependency_paths"),
    ]
```

**Claim.** `_validate_types` checks only a hardcoded subset. `scanning.skip_patterns`/`scan_paths` are not in `list_of_str_requirements`, and `paths.docs_dir/logs_dir/context_map` are not in `type_requirements` (they only reach `_validate_path`, which does `repo_root / path_str` and raises `TypeError` on a non-str).

**Impact.** `skip_patterns = "archive/*"` (a string) passes validation; iterated char-by-char, its `*` matches every file — the map goes from 8 documents to 0 with no warning. `docs_dir = 123` surfaces as an opaque `unsupported operand type(s) for /: 'PosixPath' and 'int'`.

**Fix.** Add `scanning.skip_patterns`/`scan_paths` to `list_of_str_requirements`, and `paths.docs_dir/logs_dir/context_map` (str) to `type_requirements`.

**Verification evidence.** Reproduced: `skip_patterns="archive/*"` → "Documents: 0" exit 0, zero warnings; `docs_dir=123` → opaque Config error exit 1.

### D1b-counts-1 — `ontos map` counts concept-vocabulary warnings that `activate` and `doctor` never compute — 4 vs 0 on this repo at HEAD
**File:** `ontos/commands/activate.py:125` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        content, validation = generate_context_map(
            docs,
            gen_config,
            GenerateMapOptions(max_dependency_depth=config.validation.max_dependency_depth),
        )
```

**Claim.** `run_activation` calls `generate_context_map` without `known_concepts`, while `map_command` loads and passes it (`map.py:954`), so the unknown-concept check runs only in `ontos map`. `doctor`'s `activation_health` delegates to `run_activation` and prints "counts match `ontos activate`", silently disagreeing with map. Map's JSON also carries no `count_basis` label (violates health.py:17-18).

**Impact.** `ontos map --strict` (the documented CI/pre-commit gate) exits 2 on a repo `doctor` declares "Activation clean." Users of the documented session workflow see contradictory totals.

**Fix.** Load `known_concepts` in `run_activation` too (same helper), so activate/doctor/map validate identically. #133's promise was unified counts, not labeled disagreement.

**Verification evidence.** On pristine clone at HEAD: `map --json` warnings=4 (`curation` "Unknown concept" for `validation`/`health`), `map --strict` exit 2; `activate --json` warnings=0; `doctor --json` "Activation clean." Substring `basis` absent from map JSON.

### D1b-counts-2 — MCP snapshot pipeline ignores configured `max_dependency_depth` — MCP activate emits phantom depth warnings the CLI never reports
**File:** `ontos/io/snapshot.py:83` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
    orchestrator = ValidationOrchestrator(
        filtered_docs,
        {
            "allowed_orphan_types": config.validation.allowed_orphan_types,
```

**Claim.** `create_snapshot` builds its orchestrator config without `max_dependency_depth`, so `validate_graph` falls back to hard-coded 5 (validation.py:181). The MCP `context_map` tool has the same defect (tools.py:280). CLI activate/map pass the configured value.

**Impact.** Any project with `max_dependency_depth != 5` gets depth warnings from MCP activate/list_validation_warnings/context_map that the CLI does not produce; agent workflows chase nonexistent problems and MCP vs CLI counts disagree.

**Fix.** Add `"max_dependency_depth": config.validation.max_dependency_depth` to the orchestrator config, and pass it into `GenerateMapOptions` in the MCP `context_map` tool.

**Verification evidence.** Toy with `max_dependency_depth=10` and an 8-deep chain: `activate --json` warnings=0; `create_snapshot` → 3 warnings "Dependency depth 6/7/8 exceeds max 5."

### D1b-counts-3 — Generated context map counts as a document/orphan in link-check, query --health, doctor and MCP — but not in activate, map, or maintain
**File:** `ontos/commands/link_check.py:52` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        base_skip_patterns=list(config.scanning.skip_patterns),
```

**Claim.** activate/map/maintain exclude the generated context map from scanning; `link_check_command`, `scan_docs_for_query`, `doctor`'s `check_docs_directory`, and `create_snapshot` do not. When the map is inside scanned scope (`context_map="docs/Ontos_Context_Map.md"`), its own generated frontmatter (`id: ontos_context_map, type: reference` — not in default `allowed_orphan_types`) parses as a real orphan, inflating counts on the surfaces that don't skip it. query --health and link-check both label the divergent count `graph_validation`, defeating #133's basis contract.

**Impact.** On a clean repo, `ontos link-check` exits 2 flagging Ontos's own artifact as an orphan while activate/doctor report clean; query --health and MCP doc_count disagree with activate by 1.

**Fix.** Centralize the exclusion in `collect_scoped_documents` (or a shared helper) rather than relying on 7 call sites to remember it.

**Verification evidence.** Toy with the map inside scope: `activate` documents=2/clean; `link-check` exit 2, orphans `['ontos_context_map']`; `query --health` total_docs=3; `create_snapshot` doc_count=3 with orphan warning; identical `graph_validation` basis on the two disagreeing surfaces.

### D1b-counts-4 — `maintain` check_links reports "No broken references" while link-check exits 1 with broken_references=1 for identical state
**File:** `ontos/commands/maintain.py:631` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        doc_paths=doc_paths,
        scope=scope,
        include_body=False,
```

**Claim.** `_task_check_links` runs `run_link_diagnostics` with `include_body=False`, so body references are never scanned, yet its success message asserts "No broken references, duplicates, or scope-relative orphans." (maintain.py:715) and its JSON reuses the `broken_links` counter that standalone link-check populates from frontmatter PLUS body. No basis label indicates the narrower pipeline.

**Impact.** A user running `ontos maintain` as the weekly health gate is told the graph has no broken references (exit 0), while `ontos link-check` fails (exit 1) on a body reference to a nonexistent doc — broken docs ship because the maintenance surface vouched for them.

**Fix.** Either run the body scan in maintain (cheap after #135), or rename the metric (`broken_frontmatter_links`), update the message, and add a `count_basis` field.

**Verification evidence.** Toy with `[[nonexistent_doc_id]]` in a body: `link-check` exit 1 broken_body=1; `maintain` exit 0 check_links success "No broken references..." broken_links=0, no `count_basis`.

### D7-cli-consistency-1 — `map --json` interleaves human text with the JSON envelope and emits no JSON at all on fatal load errors
**File:** `ontos/commands/map.py:899` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED** · merges D1c-envelope-1, D1c-envelope-2

```
    if load_result.issues and not options.quiet:
```

**Claim.** In `--json` mode map prints "Load diagnostics:" blocks (and `--sync-agents` prints progress) to stdout before the envelope, because the gate checks only `options.quiet`, and `_cmd_map` passes `quiet=args.quiet` (not `quiet-or-json`, unlike every other handler). Worse, on `has_fatal_errors`/`duplicate_ids` it returns 1 (lines 917-918) without emitting any envelope — `map --json --quiet` on duplicate IDs produces exit 1 with zero bytes.

**Impact.** Any machine consumer of `map --json` gets unparseable stdout on a single load warning (invalid enum/reference type, common in migrating repos), and no diagnostics on duplicate-ID failures. Violates the #135 contract ("stdout must stay a single parseable JSON document").

**Fix.** Route load-diagnostics/sync-agents progress to stderr (or gate on `not json_output`); emit `emit_command_error(...)` on the fatal-load path; make `_cmd_map` pass `quiet=args.quiet or args.json`.

**Verification evidence.** `type:bogus_type` doc → stdout begins "Load diagnostics:..." then the envelope, `json.load` raises. Two docs sharing an id → `map --json --quiet` exit 1, 0 bytes stdout, 0 bytes stderr.

### D7-cli-consistency-3 — Exit code 2 is overloaded: usage errors, strict warnings, orphans-only, and missing subcommand are indistinguishable
**File:** `ontos/commands/map.py:996` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED** · merges D1c-envelope-6

```
    elif options.strict and result.warnings:
        exit_code = 2
```

**Claim.** Exit 2 simultaneously means argparse bad usage, `OntosUserError`, no command, map strict-mode warnings, link-check orphans-only, and verify --portfolio config errors — while the shared `--limit` validator classifies an equally pure usage error as exit 1 `E_USER_INPUT`, and `OntosUserError` with the *same code* exits 2. No taxonomy is documented; Manual line 942 even says "--strict — Exit 1 on any issue" which is wrong.

**Impact.** CI gates cannot distinguish "you typo'd a flag" from "your docs have strict warnings" or "orphans exist" without parsing text; the same machine code maps to two exit codes.

**Fix.** Document and enforce a taxonomy (e.g. 0=clean, 1=findings, 2=usage, 3=warnings-only, 5=internal, 130=interrupt); move `_reject_invalid_limit` to exit 2 and strict-warnings/orphans off exit 2 (gate behind a `schema_version` bump).

**Verification evidence.** Live: `map --nonsense`→2, `map --strict`(warnings)→2, `link-check`(orphans)→2, `ontos`(no cmd)→2, `maintain --skip bogus --json`→2+`E_USER_INPUT`, `link-check --limit 0 --json`→1+`E_USER_INPUT`.

### D7-cli-consistency-4 — Envelope status semantics contradict: findings are "success" for link-check but "error" for map/schema-migrate
**File:** `ontos/commands/link_check.py:78` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED** · merges D1c-envelope-3

```
        emit_command_success(
            command="link-check",
            exit_code=result.exit_code,
```

**Claim.** link-check emits `status='success', error=null` even for nonzero outcomes, while map emits `emit_command_error`/`E_COMMAND_FAILED` for the equivalent "issues found" (map.py:1037), and `schema-migrate --check` reports "5 files need migration" as `status='error'` — three different answers to whether findings are an error.

**Impact.** A consumer branching on `status` treats orphan findings as clean success under link-check but as command failure under map/schema-migrate; `E_COMMAND_FAILED` is uninformative next to link-check's structured `result_status`.

**Fix.** Pick one semantic (recommend link-check's: `status` = did the command execute; findings in `data.result_status`) and apply to map/doctor/schema-migrate; bump `schema_version` once.

**Verification evidence.** Live: link-check orphans → `{status:success, exit_code:2}`; map --strict same 7 warnings → `{status:error, E_COMMAND_FAILED}`; schema-migrate --check → `{status:error, E_COMMAND_FAILED}`. Only link-check's side has documented design intent (Manual 679-682, #131).

### D1c-envelope-4 — `query --json` classifies missing-project/bad-config as exit 5 `E_INTERNAL` while peers return exit 1 `E_COMMAND_FAILED`
**File:** `ontos/commands/query.py:213` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
    root = find_project_root()
```

**Claim.** `_run_query_command` calls `find_project_root()` (and `scan_docs_for_query` calls `load_project_config`) unguarded, so `FileNotFoundError`/config exceptions fall through to `cli.main()`'s generic `except Exception` → "Internal error", `E_INTERNAL`, exit 5 — the same environmental failures that map/link-check/activate deliberately report as exit 1 `E_COMMAND_FAILED`.

**Impact.** Agents get contradictory signals for identical conditions: "not an Ontos project" is routine from map (exit 1) but a reported internal crash from query (exit 5). Automation escalating `E_INTERNAL` files false crash reports.

**Fix.** Wrap `find_project_root()`/`load_project_config()` in try/except returning `(1, message)` like `link_check_command`.

**Verification evidence.** Empty dir: `query --health --json`→exit 5 `E_INTERNAL`; `map`/`link-check`→exit 1 `E_COMMAND_FAILED`; `activate`→exit 1 `E_ACTIVATION_UNUSABLE`. Same divergence with malformed `.ontos.toml`.

### D7-cli-consistency-2 — `consolidate --json` and `promote --json` block on stdin prompts and print prompt text to stdout before the envelope
**File:** `ontos/commands/consolidate.py:260` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
                confirm = input(f"   Archive this log? [y/N/edit]: ").strip().lower()
```

**Claim.** The interactive confirmation loop is gated only on `not options.all`, never on `json_output`/`quiet`, so `consolidate --json` hangs on a TTY, and at EOF the prompt text is written to stdout ahead of the JSON envelope. `promote` has the identical pattern (promote.py:248/281).

**Impact.** Automation with `--json` deadlocks (TTY) or gets corrupt stdout that fails `json.loads`; the envelope reports "Consolidated 0 logs" as success, silently doing nothing.

**Fix.** Make `json_output` (and `quiet`) imply non-interactive (auto-decline or require `--all`/`--yes` and emit `E_USER_INPUT`); route narration through `OutputHandler`.

**Verification evidence.** `consolidate --count 1 --json </dev/null` → two prompts + "Skipped." then the envelope, exit 0; held-open stdin blocks; `promote --json </dev/null` prints separators/Type/Path/Blockers before the envelope.

### D8-docs-clarity-1 — Agent Instructions ship 7+ commands that fail on v4.7.0
**File:** `docs/reference/Ontos_Agent_Instructions.md:106` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
ontos log --enhance
```

**Claim.** The README-linked "Commands for AI agents" reference instructs agents to run nonexistent commands: `log --enhance` (L106), `update` (L156), `migrate --check` (should be `schema-migrate --check`, L157/195), `stub docs/feature.md` (L183, stub takes no positional), `map --include-rejected` (L273), legacy scripts `ontos_verify.py`/`ontos_end_session.py` (L242/372), and a v2.9.4 curl installer (L162-170) contradicting pip.

**Impact.** The doc's sole audience is agents that execute commands literally; each stale entry produces a failed shell command mid-session, and the `--enhance` exit-code protocol is pure fiction.

**Fix.** Rewrite against `cli.py`: `log -e <type>`, `pipx upgrade ontos`, `schema-migrate --check`, `stub --goal ... --type ...`, drop `--include-rejected`/legacy scripts.

**Verification evidence.** Ran each against v4.7.0: all failed as claimed; `grep enhance/include_rejected` in `ontos/` → nothing. The v4.7 doc-refresh `b458ab6` changed only 7 lines (MCP table), leaving the v2.x sections presented as current.

### D8-docs-clarity-2 — Shipped generator emits always-failing `ontos query <id>` into every AGENTS.md/CLAUDE.md
**File:** `ontos/core/instruction_protocol.py:70` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
| `ontos query <id>` | Find document by ID |"""
```

**Claim.** The Quick Reference baked into every generated AGENTS.md/CLAUDE.md/.cursorrules advertises `ontos query <id>`, but the query command has no positional and requires one of six mutually exclusive flags, so the advertised form always errors.

**Impact.** Every user of `ontos agents`/`ontos export claude` (and this repo's own AGENTS.md:63) hands agents a guaranteed-failing command inside the mandatory activation protocol whose Core Invariants say "If a command fails, read the error message."

**Fix.** Change the template row to `ontos query --depends-on <id>` (or `--list-ids`), or add an optional positional to query; regenerate.

**Verification evidence.** `ontos query someid` → "error: one of the arguments --depends-on ... is required." Template live in both generators; failing command present in the repo's own AGENTS.md:63 and .cursorrules:52.

### D8-docs-clarity-4 — Context map Tier-1 Recent Activity reads a `summary` field no tool ever writes
**File:** `ontos/commands/map.py:271` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
            summary = doc.frontmatter.get("summary", "No summary")
```

**Claim.** The map's flagship Tier-1 "Recent Activity" table sources its Summary column from a `summary:` key, but neither `ontos log` nor MCP `log_session`/`session_end` ever emit it, and no doc tells users to add it — so the column is structurally always "No summary."

**Impact.** The first thing every agent reads for orientation (~2k tokens) carries zero recent-work signal; this repo's own map shows all displayed logs as "No summary." `history.py` already extracts first-paragraph summaries from log bodies but map.py doesn't use it.

**Fix.** Have `log`/`session_end` write a one-line `summary:`, or reuse `history.py`'s body-paragraph extraction as the fallback.

**Verification evidence.** `grep '^summary:' docs/logs/*.md` = 0 of 63; `Ontos_Context_Map.md` lines 33-35 all read "No summary"; the only candidate writer (`curation.py` `summary_seed`) is discarded by `promote.py:135`.

### D8-docs-clarity-5 — Manual documents a workflow-mode config system that does not exist in the package
**File:** `docs/reference/Ontos_Manual.md:479` · **Effort:** M · **Owner Q:** 7 · **Verification: CONFIRMED** · merges D8-docs-clarity-10

```
ONTOS_MODE = "prompted"  # "automated", "prompted", or "advisory"
```

**Claim.** Manual §1 "Configuration Modes (v2.5)" and §6 tell users to edit `ontos_config.py` with `ONTOS_MODE`/`AUTO_ARCHIVE_ON_PUSH`/`ENFORCE_ARCHIVE_BEFORE_PUSH`/`AUTO_CONSOLIDATE` presets, but the v4 `WorkflowConfig` has only `log_retention_count`; `ONTOS_MODE` is a dead load into `SessionContext.config` no code reads back, and `ENFORCE_ARCHIVE_BEFORE_PUSH`/`REQUIRE_SOURCE_IN_LOGS` appear nowhere.

**Impact.** A newcomer configuring "their mode" per the Manual's first Core Concepts section changes nothing; downstream sections and Agent Instructions reference the same phantom system, so both humans and agents build a false mental model.

**Fix.** Rewrite Manual §1/§6 to the real `.ontos.toml` surface (`[ontos]`, `[paths]`, `[scanning]`, `[validation]`, `[workflow].log_retention_count`, `[hooks]`, `[mcp]`); strip mode language from Agent Instructions and the maintain task.

**Verification evidence.** Grep of `ontos/` finds only the dead `context.py:91` load and an unrelated "advisory locking" docstring. Nuance: `AUTO_CONSOLIDATE` is NOT phantom (`maintain.py:204-224` honors it), but the presets that would set it are nonexistent — the phantom mode system and newcomer misdirection stand.

### D5a-repo-redundancy-1 — Commit gating and CI still run the superseded `.ontos/scripts` layer; 63% of its 8,781 lines already duplicated in the archive
**File:** `.pre-commit-config.yaml:9` · **Effort:** L · **Owner Q:** 3 · **Verification: CONFIRMED** · merges D6b-test-quality-8, D6b-test-quality-10

```
        entry: python3 .ontos/scripts/ontos_generate_context_map.py --strict --quiet --check
```

**Claim.** `.ontos/scripts/` (22 scripts, 8,781 lines + 1,444 test lines run by CI) is the v2 implementation the project itself declared superseded (`ARCHIVED.txt`: "Use 'ontos <command>' instead."), yet it still gates every commit via pre-commit and CI. 7 of 22 scripts are byte-identical to archived copies; 5,552/8,781 lines (63.2%) exist verbatim in the archive. 11 main-suite test files couple to it.

**Impact.** Contributors maintain and CI-test two divergent implementations; the known pre-commit failure on `main` (3 ARCHITECTURE errors) and the consolidate-hook dirtying are artifacts of this legacy layer, not the shipped package.

**Fix.** Rewire then archive: point `ontos-validate` at `ontos map --strict --quiet` (add a `--check` no-write flag for parity), point `ontos-consolidate` at `ontos hook pre-commit`, drop the legacy CI pytest step, port/delete the 11 tests, then move `.ontos/scripts/` into the archive.

**Verification evidence.** Reproduced the pre-commit failure (3 ARCHITECTURE + 2 LINT, exit 1) from the legacy script on a copy of `main` while modern `ontos map --strict` produced zero ARCHITECTURE errors. Scripts self-describe as "removed in v3.0" while shipping v4.7.0.

### D5a-repo-redundancy-2 — A stale 3,053-line vendored fork of the ontos package shadows the real package in every pre-commit run
**File:** `.ontos/scripts/ontos_generate_context_map.py:14` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED** · merges D3a-parsers-4

```
from ontos.core.context import SessionContext
```

**Claim.** `.ontos/scripts/` contains a nested `ontos/` tree (14 modules, 3,053 lines). Because `sys.path[0]` is the script's directory, this fork — reporting `__version__` 2.8.0 — satisfies all `from ontos.core...` imports in the pre-commit scripts, not the installed v4.7.0 package. 12 of 14 modules have diverged (config 83 vs 337 lines, frontmatter 122 vs 369).

**Impact.** Every commit is validated by frozen v2.x-era logic. Any fix in `ontos/core/` silently does not apply to the hook path — the likely root cause of pre-commit failing on `main` while the modern CLI disagrees.

**Fix.** Falls out of the hook/CI rewire (D5a-repo-redundancy-1): once `.pre-commit-config.yaml` calls the CLI, delete/archive `.ontos/scripts/ontos/` in the same PR.

**Verification evidence.** `sys.path.insert(0,'.ontos/scripts'); import ontos` → `.ontos/scripts/ontos/__init__.py`, `__version__='2.8.0'`. On an identical repo copy the legacy script and `ontos map --strict` disagree on the same tree.

---

## P2 — hygiene

### D1a-graph-link-2 — Non-CommonMark fence parsing: single-line ` ```code``` ` swallows subsequent diagnostics; ` ```python ` closes a plain fence
**File:** `ontos/core/body_refs.py:271` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
def _detect_fence_opener(line_text: str) -> Optional[Tuple[str, int]]:
    stripped = line_text.lstrip()
    if len(stripped) < 3:
        return None
    marker = stripped[0]
```

**Claim.** (a) A line-leading triple-backtick inline span is treated as a fence opener, pushing the rest of the doc into CODE_FENCE zone so all later broken links are skipped (false clean). (b) `_is_fence_closer` accepts any line starting with ≥ min_len markers, so ` ```python ` closes an open ` ``` ` fence and fenced code is scanned as text (false positives). **Impact.** (a) false negatives defeat the tool's purpose; (b) example code inside fences produces spurious broken refs. **Fix.** Reject opener remainders containing the marker char; require closers to be marker-run only. **Verification.** Both reproduced; but at HEAD the (a) trigger occurs 0 times in the shipped corpus and a CommonMark cross-check found 0 shipped findings inside code zones — real bug, limited current impact.

### D1a-graph-link-3 — Body-reference locations report body-relative line numbers as if they were file lines
**File:** `ontos/core/link_diagnostics.py:473` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
            known_scan = scan_body_references(
                path=doc.filepath,
                body=doc.content,
```

**Claim.** `run_link_diagnostics` scans `doc.content` (frontmatter-stripped, lstripped) but emits `ReferenceLocation.line` alongside `source_path` as a file coordinate; every reported body line is short by the frontmatter block plus stripped blanks. `rename.py:648` handles this correctly, so the two surfaces disagree. **Impact.** Navigation from `source_path:line` lands 7-15 lines above the real reference; automated fixers editing by line number patch the wrong line. **Fix.** Add the body's starting line offset (as rename computes) before constructing `ReferenceLocation`. **Verification.** Toy with 6-line frontmatter: ref on file line 11 reported as line 4, line 13 as line 6.

### D1a-graph-link-4 — `ontos map`/`query` crash with RecursionError on dependency chains deeper than ~1000
**File:** `ontos/core/graph.py:315` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        for neighbor in graph.edges.get(node, []):
            if neighbor in graph.nodes:  # Only follow valid edges
                dfs(neighbor, path)
```

**Claim.** `detect_cycles` and `calculate_depths` recurse once per chain link with no `setrecursionlimit`, so any acyclic chain deeper than ~1000 kills them, despite the docstring advertising O(V+E). **Impact.** On a large corpus with a deep chain, `ontos map` aborts with "maximum recursion depth exceeded" (exit 5) and produces no context map; query and MCP graph cache fail identically. **Fix.** Convert both traversals to iterative form. **Verification.** 1500-doc linear chain → `ontos map` exit 5. (P2 as filed: >1000-deep chains are pathological for doc graphs.)

### D1a-graph-link-5 — Case-insensitive filesystems make `_resolve_depends_on_path` drop real edges and diverge from Linux classification
**File:** `ontos/core/graph.py:91` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        if resolved in docs_by_resolved_path:
            return docs_by_resolved_path[resolved], None, None
        if candidate.exists():
            return None, candidate, resolved
```

**Claim.** The loaded-doc lookup is a case-exact dict compare (macOS `resolve()` doesn't case-normalize) while `candidate.exists()` is case-insensitive on APFS, so a case-mismatched `depends_on` misses the dict, hits `exists()=True`, drops the edge, and is reported as an OUT_OF_SCOPE warning; on case-sensitive Linux the same repo yields a hard BROKEN_LINK error. **Impact.** Same doc set validates differently per platform (soft warning locally, hard error in CI); the edge silently vanishes. **Fix.** Compare via `os.path.normcase` keys or `samefile` before falling through. **Verification.** Both halves reproduced, the case-sensitive half on a real case-sensitive APFS image.

### D1a-graph-link-7 — Known-ID body-scan pass is provably output-neutral yet costs ~65% of body_scan time
**File:** `ontos/core/link_diagnostics.py:476` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
                known_ids=active_ids,
                include_skipped=False,
            )
```

**Claim.** Pass 1 restricts matches to `known_ids=active_ids`, but `_classify_reference`'s first action (line 669 `if value in active_ids: return`) unconditionally discards every such value — each pass-1 match is generated then dropped, and the position-dedup interplay cannot change results. **Impact.** The most expensive scan in the #131/#135 "200x faster" hot path is wasted work: on the 144-doc corpus, neutralizing pass 1 drops body_scan 99ms→34ms with identical findings. **Fix.** Delete the known-ID pass and the seen_positions merge; keep only the generic scan. **Verification.** Byte-identical findings with pass 1 neutralized; git archaeology shows the discard existed in pass 1's origin commit, so it was output-neutral from inception.

### D1a-graph-link-8 — Broken-dep values round-trip through the human message and are corrupted by quotes (or silently dropped)
**File:** `ontos/core/link_diagnostics.py:22` · **Effort:** S · **Owner Q:** 7 · **Verification: CONFIRMED**

```
_QUOTED_VALUE_RE = re.compile(r"'([^']+)'")
```

**Claim.** `run_link_diagnostics` recovers the broken dep value by regexing the first single-quoted substring out of `ValidationError.message`, even though #134 added a structured `context` dict to avoid message parsing — BROKEN_LINK never populates it (graph.py:272-279). Any value with an apostrophe is truncated. **Impact.** JSON consumers get a wrong `value` (and suggestions for the wrong string); some errors visible to map/verify are invisible to link-check. **Fix.** Populate `context={'dep_value': dep_id}` on BROKEN_LINK and read `error.context`. **Verification.** `depends_on: ["don't-exist"]` → link-check value `don` with suggestions for `don`.

### D1a-graph-link-9 — Unreachable circular_severity branch in build_graph's broken-link reporting
**File:** `ontos/core/graph.py:278` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
                severity=circular_severity if dep_id == doc_id else depends_on_severity
```

**Claim.** If `dep_id == doc_id` then `dep_id` is necessarily in `existing_ids`, so the loop short-circuits at line 195 and never reaches the error construction — the `circular_severity` arm can never fire. Self-loops are surfaced by `detect_cycles`. **Impact.** Dead code implying self-deps get special severity here; the `circular` severity_map key silently has no effect. **Fix.** Use `depends_on_severity` directly, or detect `dep_id == doc_id` before the existing_ids check. **Verification.** `depends_on=['selfy']` → no BROKEN_LINK from build_graph; `detect_cycles` → `[['selfy','selfy']]`.

### D1b-counts-5 — MCP activate `warnings_total` includes error-severity and load-issue records; CLI's identically-named field is warnings-only
**File:** `ontos/mcp/tools.py:197` · **Effort:** S · **Owner Q:** 7 · **Verification: CONFIRMED**

```
        "warnings_total": len(records),
```

**Claim.** `_normalize_warnings` concatenates validation errors, warnings, and snapshot load-issues; CLI activate's `warnings_total` counts only warning-severity. Same field name, different populations. **Impact.** Tooling asserting CLI/MCP parity sees `warnings_total` disagree even after other count bugs are fixed. **Fix.** Report `errors_total` separately; restrict `warnings_total` to warning-severity; keep load issues under a `load_issues` counter. **Verification.** 1 broken link + 4 orphans → CLI warnings_total=4/errors=1, MCP warnings_total=5.

### D1b-counts-6 — Dead `'broken_link':'warning'` severity override — broken depends_on always errors despite the configured downgrade
**File:** `ontos/commands/map.py:145` · **Effort:** S · **Owner Q:** 4 · **Verification: CONFIRMED**

```
            "severity_map": {
                "broken_link": "warning",
                "concepts": "warning"
            },
```

**Claim.** The orchestrator merges this over `REFERENCE_SEVERITY_DEFAULT` (which has `depends_on:'error'`), and build_graph resolves via `severity_map.get("depends_on", severity_map.get("broken_link", ...))` — `depends_on` always wins, so `broken_link` is never consulted. **Impact.** Whoever tunes this expecting warnings gets errors; `doctor` exits 1 for a single broken link. **Fix.** Delete the dead key or change to `depends_on:'warning'` if the downgrade is wanted; add a test. **Verification.** Broken link surfaces as error on every surface; git shows the key was dead from birth (c5bd84e).

### D1c-envelope-5 — link-check `result_status` is exit-code-derived, so parse-failed docs report "clean"
**File:** `ontos/core/link_diagnostics.py:155` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        if self.exit_code == 0:
            return "clean"
```

**Claim.** `result_status` maps exit_code 0 → "clean" even when `load_warnings > 0`, i.e. a doc that failed frontmatter parsing was excluded from all reference checking; map's `result_status` was deliberately made count-based for this reason (#139). **Impact.** A CI gate reading `result_status` gets "clean" from a run where a doc was silently skipped — "clean" overstates what was verified. **Fix.** Compute `result_status` from counts like map; document the basis. **Verification.** Parse-failed doc → link-check exit 0, `result_status:"clean"`, `load_warnings:1`. Note: the finding's cross-command repro (map "warnings") was refuted — map treats parse_error as fatal (exit 1, no envelope) — so the divergence is narrower than claimed; P2.

### D1c-envelope-7 — `generator_version` provenance has two hand-maintained sources of truth with no direct sync check
**File:** `ontos/__init__.py:10` · **Effort:** S · **Owner Q:** 6 · **Verification: CONFIRMED** (confidence: medium)

```
__version__ = "4.7.0"
```

**Claim.** The map's `generator_version` (#136) reads `ontos.__version__`, hardcoded independently of `pyproject.toml`'s version; no test compares them, and the publish workflow's guard validates only the tag against `__version__`. **Impact.** If the constants drift, every map stamps the wrong version and doctor's staleness check compares against the same wrong constant. **Fix.** Derive `__version__` via `importlib.metadata.version("ontos")`, or add a test/publish step asserting equality. **Verification.** Two independent "4.7.0" constants, no comparison; drift has precedent (v3.0.4 release note). The specific PyPI-ship scenario is blocked by external invariants (skip-existing/duplicate-version), so P2.

### D2a-write-safety-6 — Multi-file rename commit is per-file atomic only; crash mid-commit leaves a half-renamed corpus and the CLI has no rollback
**File:** `ontos/core/context.py:195` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED**

```
                    temp.rename(final)
```

**Claim.** `SessionContext.commit` applies Phase 2 renames sequentially; a crash between renames leaves some files with the new ID and others old, plus orphaned `.tmp` files (no fsync). MCP got A3 git rollback; the CLI `rename --apply` path does nothing on commit failure — it prints "repository may be partially updated" without naming files or attempting recovery. **Impact.** A rename touching dozens of files that dies mid-commit leaves the graph inconsistent with no automated recovery, despite the CLI having enforced the clean-tree precondition that makes rollback trivially safe. **Fix.** Reuse the MCP A3 pattern (`git checkout -- <planned paths>`); have `commit()` report partially-applied paths. **Verification.** Reproduced half-applied state; but the enforced clean precondition guarantees `git checkout -- .` fully recovers and the exception path warns — a documented non-transactional contract, hence P2.

### D2a-write-safety-7 — Commit engine writes temp files with locale-dependent default encoding while every reader pins UTF-8
**File:** `ontos/core/context.py:176` · **Effort:** S · **Owner Q:** 6 · **Verification: CONFIRMED**

```
                    temp.write_text(op.content)
```

**Claim.** The single choke-point for all document mutations writes with no `encoding` argument (`locale.getpreferredencoding()` on 3.9-3.12), while every read path pins `encoding='utf-8'`. On a non-UTF-8 POSIX locale, non-ASCII content is silently transcoded (mojibake) or raises `UnicodeEncodeError` mid-commit. **Impact.** Users on non-UTF-8 locales (enterprise Linux/SSH) get silently corrupted content from every write command. **Fix.** `temp.write_text(op.content, encoding='utf-8')`. **Verification.** Under `LC_ALL=en_US.ISO8859-1`: 'café' written as `b'caf\xe9'` then utf-8 read raises; emoji raises `UnicodeEncodeError` mid-commit.

### D2a-write-safety-8 — CLI rename builds its plan and git-clean check outside any lock: lost-update race against concurrent MCP writers
**File:** `ontos/commands/rename.py:200` · **Effort:** M · **Owner Q:** 1 · **Verification: CONFIRMED** (confidence: medium)

```
    ctx = SessionContext.from_repo(prepared.scope_data.repo_root)
```

**Claim.** CLI `rename --apply` reads all docs and computes new_content with no lock held; the flock is acquired only inside `ctx.commit()`. A concurrent locked writer (MCP `promote_document`/`log_session`) that mutates a planned file between plan and commit is silently overwritten (no re-read, no content-hash compare). **Impact.** An agent driving the MCP server while a human runs `rename --apply` can have its write silently reverted; both report success. **Fix.** Hold the flock across plan+commit (mirror MCP), or record content hashes at plan time and abort on mismatch. **Verification.** Demonstrated end-to-end: a promote applied in the gap was silently reverted while both operations reported success. Narrow window → P2.

### D2a-write-safety-9 — Two buffered writes to the same path make commit raise after the write is applied, triggering spurious rollback
**File:** `ontos/core/context.py:175` · **Effort:** S · **Owner Q:** 4 · **Verification: CONFIRMED**

```
                    temp = op.path.with_suffix(op.path.suffix + '.tmp')
```

**Claim.** Temp paths are deterministic, so two `buffer_write` calls for the same path stage the same temp twice; Phase 2 renames it on the first entry and raises `FileNotFoundError` on the second — after the final file was already replaced. `commit()` reports failure for a write that succeeded, triggering rollback machinery against a healthy tree. **Impact.** Any caller buffering the same path twice gets a false commit failure plus an unnecessary destructive rollback (including the tracked-file-deletion hazard). **Fix.** Deduplicate `pending_writes` by target path (last write wins), or use unique temp names. **Verification.** Reproduced; latent — every current call site buffers unique paths.

### D2b-roundtrip-5 — Surgical edits drop the UTF-8 BOM, delete inline comments on the edited line, and lowercase the preserved original value
**File:** `ontos/core/frontmatter_repair.py:215` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
lines[target.line_index] = f"{edit.field}: {edit.new_value}{line_ending}"
```

**Claim.** Three lesser lossy behaviors: `_read_decoded_content` strips a leading BOM no consumer restores; enum-repair overwrites the entire line (deleting inline comments); the preserved value is `str(issue.value).strip().lower()` so 'Approved' becomes 'approved'. **Impact.** BOM-marked files (Windows editors) lose their BOM on any rename/retrofit/enum-repair apply; audit annotations deleted; provenance casing munged. **Fix.** Record BOM in `_DecodedContent` and re-prepend; splice the value preserving trailing comments; keep the original enum value verbatim. **Verification.** Reproduced: "BOM survived: False", "inline comment survived: False", "Approved"→"approved".

### D3a-parsers-2 — Live public-API history path uses the divergent fallback parser and silently drops block-style impacts/depends_on lists
**File:** `ontos/core/history.py:87` · **Effort:** M · **Owner Q:** 3 · **Verification: CONFIRMED**

```
        frontmatter = parse_frontmatter(log_path)
```

**Claim.** core/history.py calls core/frontmatter.py:parse_frontmatter with NO yaml_parser, so the hand-rolled _fallback_yaml_parse (frontmatter.py:74) runs; it cannot read block-style YAML lists (returns None for the key), so parse_log_for_history/generate_decision_history — both re-exported as top-level public API in ontos/__init__.py:28-33 — lose all impacts/concepts for logs written in block style, which is exactly the style used by real logs in this repo (docs/logs/2026-05-11_v4-4-agentic-activation-resilience.md line 10-11).

**Impact.** Any consumer of the shipped package's public history API (the intended replacement for the vendored .ontos scripts) generates a decision_history.md whose Impacts lines are silently missing for block-style logs, while `ontos map`'s canonical loader reads the same files correctly — two live code paths disagree on the same document.

**Fix.** PyYAML is a hard dependency (pyproject.toml:31 'pyyaml>=6.0,<7.0'), so the stdlib-only fallback rationale is obsolete: delete _fallback_yaml_parse, make parse_frontmatter default its yaml_parser to ontos.io.yaml.parse_yaml (or rewrite history.py on top of io/files.py:load_frontmatter + parse_frontmatter_content), and stop re-exporting the NON-CANONICAL parse_frontmatter at package top level (ontos/__init__.py:14).

---

### D3b-structure-3 — `rename_tool.py` copy-pastes ~115 lines of the write-tool substrate from `writes.py` instead of importing it
**File:** `ontos/mcp/rename_tool.py:119` · **Effort:** M · **Owner Q:** 3 · **Verification: CONFIRMED**

```
def _write_error_result(
    *,
    error_code: str,
```

**Claim.** `rename_tool.py` duplicates verbatim `_success_result`, `_write_error_result`, `_user_error_result`, `_Preflight`, the leading `_preflight` body, and the lock/except dispatch shape from `writes.py` — ~115 lines, collapsible to ~10 imports plus a `git_clean_check=True` flag. **Impact.** Five write tools share one error-envelope contract maintained in two places; the modules have already started diverging. **Fix.** Extract into `ontos/mcp/_write_common.py`. **Verification.** AST comparison (docstrings stripped) shows the four helpers AST-identical; `rename_tool.py` imports nothing from `writes.py`.

### D3b-structure-4 — Byte-identical exception cascade repeated in all three server invokers (plus twice in write modules), with two error-envelope shapes and dropped OntosUserError.code
**File:** `ontos/mcp/server.py:824` · **Effort:** M · **Owner Q:** 3 · **Verification: CONFIRMED**

```
    except OntosUserError as exc:
        return _tool_error_result(str(exc))
```

**Claim.** The `except OntosUserError/OntosInternalError/Exception` cascade in `_invoke_write_tool`, `_invoke_read_tool`, `_invoke_portfolio_tool` is byte-identical (30 lines), plus the same in `writes.py`/`rename_tool.py` — 5 copies. Read/portfolio paths return `_tool_error_result(str(exc))`, discarding `OntosUserError.code` (`__str__` returns only `.message`), while the write path preserves it. **Impact.** Error-contract drift: codes like `E_INVALID_BUDGET`/`E_DOCUMENT_NOT_FOUND` from read tools never reach clients machine-readably. **Fix.** Extract one `_tool_error_boundary(tool_name)` including `exc.code`; delete the legacy `_invoke_tool` shim. **Verification.** Stripped cascades identical; reproduced `E_INVALID_BUDGET` surfacing with the code absent from the envelope.

### D3b-structure-5 — Cross-workspace read guard implemented twice with divergent wording; CORE_TOOL_NAMES already missed list_validation_warnings
**File:** `ontos/mcp/server.py:1083` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
    if tool_name not in CORE_TOOL_NAMES:
        return False
```

**Claim.** `_is_cross_workspace_read` (gated by the hand-maintained `CORE_TOOL_NAMES`) duplicates `tools.py:_enforce_workspace_scope`, which every read impl already calls. The two emit different text (code-prefixed vs not), and `list_validation_warnings` (added in the v4.7 #132 slice) was never added to `CORE_TOOL_NAMES`, so it yields the impl message without the `E_` prefix while siblings yield the wrapper message with it. **Impact.** Clients pattern-matching the documented prefix miss `list_validation_warnings`; every future read tool must remember to update the list. **Fix.** Delete `_is_cross_workspace_read`+`CORE_TOOL_NAMES` and rely on `_enforce_workspace_scope` (fix the invoker to prepend `exc.code`). **Verification.** Reproduced the two wordings in simulated portfolio mode.

### D3b-structure-6 — `cli.py`: 60 near-identical functions / 1,880 lines of hand-rolled registration + dispatch boilerplate, with observable copy-paste drift
**File:** `ontos/cli.py:94` · **Effort:** L · **Owner Q:** 7 · **Verification: CONFIRMED**

```
    _register_activate(subparsers, global_parser)
    _register_init(subparsers, global_parser)
    _register_map(subparsers, global_parser)
```

**Claim.** 27 `_register_*` + 33 `_cmd_*` repeat three motifs (25 JSON-tail sites, 14 identical quiet-tails, 21 `getattr(args,"scope",None)`, 20 `json_output=args.json`). Drift already caused: `tree` registers only `--filter,-f` while map moved to `-F`/`-f`-deprecated, so `tree -f X` triggers map's deprecation warning against tree's own flag; the `validate` alias lacks `--portfolio`, masked by `getattr`; `-f` means --force in 6 commands, --filter in map/tree, --format in env. **Impact.** Every new command costs ~60 lines and a new chance to fork flag semantics; the `getattr`-default idiom fails silent. **Fix.** A declarative command table driving one generic registrar + dispatcher ending in a shared `_finish_command` tail. **Verification.** Counts confirmed at HEAD; `tree -f type:atom` printed map's deprecation warning, `tree -F type:atom` "unrecognized arguments."

### D3b-structure-8 — `get_context_bundle` loses the pre-activate warning in portfolio mode
**File:** `ontos/mcp/server.py:821` · **Effort:** S · **Owner Q:** 2 · **Verification: CONFIRMED** (confidence: medium)

```
        if tool_name != "activate" and not getattr(cache, "activation_performed", False):
            _attach_pre_activate_warning(tool_name, validated)
```

**Claim.** `get_context_bundle` routes through `_invoke_read_tool` (which attaches the "activation not performed" warning) in single-workspace mode but `_invoke_portfolio_tool` (which has no such attach) in portfolio mode. Same tool, same declared warnings field, different behavior. **Impact.** Portfolio-mode agents calling `get_context_bundle` before `activate` get no nudge, undermining the #115 activation protocol. **Fix.** Move the activation check into a shared post-validate step used by both invokers. **Verification.** Reproduced: warning present single-workspace, absent portfolio; `workspace_overview` still carried it, and commit 801e06d shows the warning is the intended contract.

### D4a-config-1 — Shipped portfolio default config bakes the author's personal machine layout into every user's `~/.config/ontos/portfolio.toml`
**File:** `ontos/mcp/portfolio_config.py:42` · **Effort:** S · **Owner Q:** 6 · **Verification: CONFIRMED**

```
_DEFAULT_CONFIG_TEXT = """[portfolio]
scan_roots = ["~/Dev"]
exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
registry_path = "~/Dev/.dev-hub/registry/projects.json"
```

**Claim.** `ensure_portfolio_config()` writes a hardcoded default encoding the developer's personal hub layout, duplicated in the dataclass defaults (32-33), the load fallbacks (90-91), and a cli.py fallback. Fires whenever a user opts into portfolio mode. **Impact.** `ontos verify --portfolio` writes a config pointing at nonexistent author paths then errors; a user with a `~/Dev` gets every git repo under it indexed. **Fix.** Ship neutral defaults (empty `scan_roots`, no `registry_path`), or a commented template that refuses to scan until configured. **Verification.** Reproduced with a fake HOME. P2 (not P1): the README documents these as an editable template and portfolio mode is opt-in with local-only SQLite.

### D4a-config-3 — `workflow.log_retention_count` is ignored by `ontos consolidate`; two divergent defaults (15 vs 20)
**File:** `ontos/commands/consolidate.py:21` · **Effort:** M · **Owner Q:** 6 · **Verification: CONFIRMED**

```
    count: int = 15
```

**Claim.** `ConsolidateOptions.count` defaults to 15 and `_cmd_consolidate` passes only `args.count`; consolidate reads only `paths.*`, never `workflow.log_retention_count` (default 20, consumed only by `ontos maintain`). **Impact.** With `log_retention_count=1` and 5 logs, `consolidate --all --dry-run` reports "Nothing to consolidate" (kept 5 under the hardcoded 15). **Fix.** Default `--count` from config when unset; reconcile 15/20 to one source. **Verification.** Reproduced: 8 logs, `log_retention_count=1` → "Nothing to consolidate."

### D4a-config-5 — Magic numbers for token budgets are scattered and the 8000 bundle default is triplicated
**File:** `ontos/mcp/portfolio_config.py:35` · **Effort:** S · **Owner Q:** 6 · **Verification: CONFIRMED** (confidence: medium)

```
    bundle_token_budget: int = 8000
```

**Claim.** 8000 is written three times (dataclass field, template text line 48, load fallback line 96) plus a fourth in `bundler.py:38`; the 1024/128000 bounds are inline at `tools.py:553-558`; `map.py:339` hardcodes `token_limit=2000`. None reference a shared constant. **Impact.** Low today (all agree) but a future edit silently diverges the read path from the template. **Fix.** Named module constants referenced everywhere. **Verification.** All literals confirmed; grep for a shared constant returned nothing.

### D4b-trust-2 — SECURITY.md materially understates the shipping MCP write surface and is stale for v4.7.0
**File:** `SECURITY.md:51` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
- **Read-only tools** — All v4.0 MCP tools are read-only. No tool modifies workspace files (except `export_graph` with `export_to_file`, which writes within the workspace root only)
```

**Claim.** The policy says all MCP tools are read-only, but the shipped server exposes `scaffold_document`, `log_session`, `session_end`, `promote_document`, `rename_document` (writes suppressed only by the non-default `--read-only`). The Supported Versions table tops out at 4.0.x, and §70 references `ontos/io/scan.py`, which does not exist. **Impact.** A reviewer relying on SECURITY.md mis-assesses the trust boundary of `ontos serve`. **Fix.** Document the v4.x write tools and their gating; refresh the version table; fix the file reference to `scan_scope.py`. **Verification.** `server.py:197 if not read_only: _register_write_tools(...)`; bare `ontos serve` is writable.

### D5a-repo-redundancy-3 — `ontos/_hooks/pre-commit` and `pre-push` ship to PyPI but are dead and import a nonexistent module
**File:** `ontos/_hooks/pre-commit:12` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED** · merges D4b-trust-3, D5b-dead-code-1

```
python3 -m ontos._scripts.ontos_pre_commit_check
```

**Claim.** `pyproject.toml:61` ships these hooks, but nothing consumes them (`ontos init` writes its own shim calling `ontos hook <type>`), and they delegate to `ontos._scripts`, which does not exist — so the guard makes the hook silently exit 0 forever. **Impact.** Shipped dead weight plus a trap: manually wiring these "v3.0" hooks yields a no-op that looks installed. **Fix.** Delete the files and the package-data line, or rewrite to call `ontos hook <type>` and use them from `_install_hooks`. **Verification.** `find_spec('ontos._scripts...')` → ModuleNotFoundError; built wheel ships the hooks and zero `_scripts` entries.

### D5a-repo-redundancy-4 — `.ontos-internal/` is 643 files (50.5% of the tree, 7.4M) with a narrow but non-trivial live coupling
**File:** `tests/conftest.py:69` · **Effort:** L · **Owner Q:** 3 · **Verification: CONFIRMED** (impact partially corrected) · merges D5a-repo-redundancy-8

```
            os.path.join(project_root, '.ontos-internal'),
```

**Claim (measurements).** `.ontos-internal/` is 643 of 1,273 tracked files; `archive/` alone is 460 frozen files (235 proposals, 77 logs, the 27-file scripts-v2 freeze). Tracked `.project-internal/` adds 25 stale v4.1 files. Not referenced in `.ontos.toml`/`pyproject.toml`/CI. **Impact (corrected).** The finding's "exactly two couplings, cleanly extractable" premise was refuted: `grep` shows ~50 references across 15+ modules — `.ontos-internal/` is the actively dogfooded contributor-mode documentation store (this repo's own `ontos map`/`ontos log` read and write it). Only the frozen `archive/` (460 files) and `.project-internal/` (25 files) are cleanly extraction candidates. **Fix.** Extract `archive/` and `.project-internal/` to a companion repo/branch; keep the live `.ontos-internal/` store. **Verification.** Measurements exact; the extraction-feasibility framing overstated, so retained at the P2 floor for the residual archive-bloat.

### D5a-repo-redundancy-6 — Eleven `.bak` files are tracked under `.ontos/backups/` in contradiction of the repo's own `.gitignore`
**File:** `.gitignore:39` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
*.bak
```

**Claim.** `.gitignore` bans backups three ways, yet 11 `.bak` files (180K) remain tracked under `.ontos/backups/`; only the legacy `.ontos/scripts/ontos_update.py` ever writes there. **Impact.** Dead 180K payload plus a policy contradiction — tracked files override the ignore rules. **Fix.** `git rm -r .ontos/backups`. **Verification.** `git ls-files '.ontos/backups'` → 11; `git check-ignore -v --no-index` matches `.gitignore:41`.

### D5a-repo-redundancy-7 — Committed generated artifacts churn in a third of all history; keep committing but adopt a churn-reduction policy
**File:** `Ontos_Context_Map.md:8` · **Effort:** M · **Owner Q:** 3 · **Verification: CONFIRMED** (confidence: medium)

```
generated_at: 2026-06-24 15:34:06
```

**Claim.** `Ontos_Context_Map.md` appears in 274 of 835 commits (32.8%), AGENTS.md in 43. Removal is NOT the fix (`ontos hook pre-push` and CLAUDE.md make the committed map the activation contract), but the seconds-precision `generated_at` guarantees a diff on every regeneration even when the graph is unchanged, and forces manual regen after every rebase. **Impact.** One in three commits carries generated-diff noise; every stacked-PR rebase conflicts on the header. **Fix.** Skip rewriting when only volatile header fields would change (content-hash the body); add a `.gitattributes merge=ours` driver; document the "commit the map" requirement. **Verification.** Counts confirmed; two zero-change `ontos map` runs produced a 3-hunk timestamp-only diff.

### D5b-dead-code-2 — Entire `ontos/_templates` subpackage is dead but shipped in every wheel
**File:** `ontos/_templates/templates.py:19` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
def get_decision_history_template() -> str:
```

**Claim.** `ontos/_templates/` (loader + two `.md` templates) has zero live references; the only consumer was the archived v2 `ontos_init.py`, yet `pyproject.toml:60` ships it. **Impact.** Dead template content published to PyPI under a "Single source of truth for all templates" header; the current init never creates these docs. **Fix.** Delete the subpackage and package-data entry, or wire `get_*_template` into `init_command`. **Verification.** Built wheel ships all 4 files; toy `ontos init` creates no template-derived files.

### D5b-dead-code-3 — `core/paths.py` is a v2-compat API: 12 public names have zero call sites in the package
**File:** `ontos/core/paths.py:158` · **Effort:** M · **Owner Q:** 3 · **Verification: CONFIRMED**

```
f"Run 'python3 ontos_init.py' to update.",
```

**Claim.** `PROJECT_ROOT`, `get_logs_dir`, `get_log_count`, `get_logs_older_than`, `get_archive_dir`, `get_decision_history_path`, `get_proposals_dir`, `get_archive_logs_dir`, `get_archive_proposals_dir`, `get_concepts_path`, `find_last_session_date` are never called by `ontos/` code — only re-exports and the legacy `.ontos/scripts` layer + tests, and the deprecation warning tells users to run a v2 script absent from pip installs. **Impact.** ~260 lines of mode-aware path logic maintained but never executed by any shipped command. **Fix.** Retire with the legacy layer; at minimum fix the warning to reference `ontos init`. **Verification.** Per-name grep returns only re-export lines; `ontos_init.py` exists only in the archive.

### D5b-dead-code-6 — `ontos/io/obsidian.py` is a dead module; its BOM-lenient reader is tested but never wired into scanning
**File:** `ontos/io/obsidian.py:39` · **Effort:** S · **Owner Q:** 5 · **Verification: CONFIRMED**

```
def detect_obsidian_vault(path: Path) -> bool:
```

**Claim.** No package code imports `ontos.io.obsidian`; `read_file_lenient` is consumed only by a test, `detect_obsidian_vault` has zero references; the `--obsidian` feature is output-formatting only. **Impact.** The module implies Obsidian BOM handling is in the scan path when it is not; green tests suggest otherwise. **Fix.** Integrate `read_file_lenient` into the scan path or delete the module + its tests. **Verification.** After `ontos map --obsidian`, `ontos.io.obsidian` absent from `sys.modules`. Nuance: the scan path DOES handle BOM via an inline duplicate in `io/files.py`, so no user-facing regression — a dead duplicate.

### D5b-dead-code-7 — Config key `[ontos].required_version` is parsed and validated but never read
**File:** `ontos/core/config.py:39` · **Effort:** S · **Owner Q:** 6 · **Verification: CONFIRMED** · merges D4a-config-4

```
required_version: Optional[str] = None
```

**Claim.** `OntosSection.required_version` is accepted as a known key (passes strict unknown-key validation) but no code reads it — version gating designed and never implemented. **Impact.** A user setting `required_version` gets silent acceptance and zero enforcement. **Fix.** Implement the check (compare against `ontos.__version__`, warn on mismatch as the V3.0 arch doc specified) or remove the field. **Verification.** `required_version='>=99.0.0'` → `ontos map` exit 0, 0 warnings; unknown keys are rejected.

### D5b-dead-code-8 — Dead public command wrappers and back-compat re-export shims with zero (or test-only) consumers
**File:** `ontos/commands/export_claude.py:50` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
def export_claude_command(options: ExportClaudeOptions) -> int:
```

**Claim.** `export_claude_command`, `migration_report_command`, `migrate_convenience_command` have zero callers (cli.py calls the `_run_*` variants); `claude_template.py` and `instruction_protocol.py` in `commands/` are pure `# noqa: F401` re-export shims imported only by tests; `agents_command`/`env_command`/`export_data_command` are test-only wrappers. **Impact.** The exit-code-only wrapper convention doubles the public surface for no runtime benefit; the shims make `commands/` look like it owns core logic. **Fix.** Delete the three wrappers; repoint the two tests at `ontos.core` and delete the shims. **Verification.** Grep returns only def lines; no wrapper convention documented.

### D5b-dead-code-9 — `init.py _create_directories` is a dead duplicate of the inline directory list in `_run_init_command`
**File:** `ontos/commands/init.py:324` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
def _create_directories(root: Path, config) -> None:
```

**Claim.** `_create_directories` is never called; `_run_init_command` inlines the same eight-directory list at 243-259 with rollback tracking the helper lacks. **Impact.** A contributor editing the named helper sees no effect. **Fix.** Delete it, or invert so `_run_init_command` calls it. **Verification.** Single grep match (the def); `ontos init --skip-hooks` created the hierarchy via the inline path.

### D5b-dead-code-10 — Six scattered defined-but-never-called helpers across mcp/, commands/, core/
**File:** `ontos/mcp/tools.py:59` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
def tool_error(message: str) -> dict[str, Any]:
```

**Claim.** Zero package callers: `mcp/tools.py:59 tool_error` (server uses its own `_tool_error_result`), `maintain.py:280 _load_docs_for_graph`, `verify.py:133 verify_document`, `schema.py:412 get_schema_info` (legacy-CI-only), `mcp/scanner.py:231 _load_registry_records` (a "backward-compatible alias" with no callers), `migrate.py:36 check_file_needs_migration`. **Impact.** Two parallel MCP error-envelope helpers is the worst — invites divergent shapes. **Fix.** Delete all six; repoint the two test-only consumers. **Verification.** Each name's only match in `ontos/` is its def; none exported via any `__init__`.

### D6a-test-gaps-2 — Empty git diff makes `suggest_impacts` propose EVERY document (latent, confirmed repro)
**File:** `ontos/io/git.py:94` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
```

**Claim.** The HEAD~1 fallback lacks the non-empty guard the primary branch has, so an empty diff returns `['']`; in `suggest_impacts` the empty basename is a substring of every doc id. **Impact.** Latent: `suggest_impacts` is reachable only via `suggest_session_impacts`, which has no live caller in the shipped CLI (`ontos log` never reads `changed_files`). **Fix.** Guard the fallback with `and result.stdout.strip()`; skip empty basenames; add tests. **Verification.** `suggest_impacts([''], {3 docs}, [])` → all 3; but `ontos log` after an empty commit wrote no `impacts` field — hence the P1 headline was downgraded to P2 (exported-but-unused API).

### D6a-test-gaps-4 — Git-hook strict-mode blocking (`return 1`) is never asserted by any test
**File:** `ontos/commands/hook.py:76` · **Effort:** S · **Owner Q:** 5 · **Verification: CONFIRMED**

```
            if config.hooks.strict:
                print(f"Error: {msg}", file=sys.stderr)
                return 1  # Block when strict
```

**Claim.** `run_pre_push_hook`'s entire validation body (71-98) is uncovered; tests cover only dispatch, the disabled path, and fail-open. The one branch where the hook blocks a push has no pin. **Impact.** Ontos installs these hooks into end-user repos; a regression flipping strict blocking to fail-open ships silently. **Fix.** Pin the four-cell matrix (strict×map-present). **Verification.** Coverage 58%, missing 71-98,121; `test_pre_push_check.py` tests the legacy script, not the shipped hook.

### D6a-test-gaps-5 — `paths.py` user-mode resolution and pre-v2.5.2 fallback chains untested
**File:** `ontos/core/paths.py:337` · **Effort:** M · **Owner Q:** 5 · **Verification: CONFIRMED** (impact corrected)

```
    old_path = str(root / docs_dir / "archive")
    if os.path.exists(old_path):
        _warn_deprecated(f'{docs_dir}/archive/', f'{docs_dir}/archive/logs/')
```

**Claim.** User-mode branches (which decide where PyPI users' logs/archives go) are dark while contributor-mode is fully covered. **Impact (corrected).** The data-integrity framing was refuted: the named functions have zero package callers — `consolidate` carries its own inline layout fallback (which IS tested in user mode, `test_consolidate_root_regression.py:121`). So this is exported-but-unused API with untested fallback chains, overlapping the dead-code dimension. **Fix.** Test or retire the exported helpers. **Verification.** Coverage 64%; `get_archive_logs_dir`/`get_decision_history_path` have zero package call sites.

### D6a-test-gaps-6 — Golden-master regression net dead since v3.0 — no end-to-end snapshot on the product's primary artifact
**File:** `tests/golden/test_golden_master.py:20` · **Effort:** L · **Owner Q:** 5 · **Verification: CONFIRMED**

```
    @pytest.mark.skip(reason="Baselines need recapture for v3.0 CLI changes")
```

**Claim.** Both golden tests are hard-skipped; they were the only end-to-end byte-stability check on `map`/`log` output, off through v3.1→v4.7 including the #136 and #132 output changes. **Impact.** Output-format regressions in the two commands every session runs are caught only if a human notices diffs in the committed map; downstream agent tooling parses this file. **Fix.** Recapture baselines under v4.7 and re-enable, or replace with a lighter pytest snapshot test. **Verification.** Ran `compare_golden_master.py --fixture small` against v4.7.0 → map/context_map/log all FAIL (128 diff lines); CI workflow is `workflow_dispatch`-only.

### D6a-test-gaps-7 — `ontos query` CLI dispatch and `query_stale` uncovered despite v4.7 churn in the same file
**File:** `ontos/commands/query.py:85` · **Effort:** M · **Owner Q:** 5 · **Verification: CONFIRMED** (scope corrected)

```
            if last_modified.tzinfo is not None:
                last_modified = last_modified.replace(tzinfo=None)
```

**Claim.** `query_stale` and the `_run_query_command` dispatch are uncovered. **Scope correction.** `query_stale` (63-91) is genuinely 100% uncovered (the test imports the legacy-script copy); four of five flag branches (`--depends-on`/`--depended-by`/`--concept`/`--stale`) plus fatal-load/empty-scope exits are untested. But `--health` and `--list-ids` ARE exercised end-to-end (`test_query_parity`, `test_health_count_consistency`), so "entirely uncovered dispatch" is false. **Fix.** Add dispatch tests per flag; pin `query_stale` fallback chain. **Verification.** Coverage missing 63-91 and the four flag branches, not the contiguous 218-287 claimed.

### D6a-test-gaps-8 — `write_config` emits unparseable TOML for nested dicts and newline strings; merge_configs/load_config_if_exists have zero tests and zero callers
**File:** `ontos/io/toml.py:92` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
        else:
            return str(v)
```

**Claim.** `write_config` (behind `save_project_config`) falls back to `str()` for unsupported types and never escapes newlines, producing files `tomllib` rejects, so the next `load_project_config` raises `ConfigError`. `load_config_if_exists`/`merge_configs` are 100% untested with no callers. **Impact.** Latent (config_to_dict is flat today): the first nested section or multi-line default corrupts every user's `.ontos.toml` on save. **Fix.** Round-trip property tests over adversarial strings; consider `tomli_w` (already a dep). **Verification.** `{'section':{'nested':{'a':1}}}` and `'line1\nline2'` both wrote files that `load_config` rejected.

### D6a-test-gaps-9 — Fail-closed guards for MCP destructive writes (is_workspace_clean / rollback_path) have no pins
**File:** `ontos/core/git.py:59` · **Effort:** S · **Owner Q:** 5 · **Verification: CONFIRMED**

```
    except FileNotFoundError:
        return False, "git executable not found on PATH"
```

**Claim.** The safety-critical fail-closed branches (git-missing, OSError/timeout, nonzero-returncode; rollback's outside-workspace/git-missing/unlink-failure) are all uncovered; the docstring declares "we fail closed" as the contract guaranteeing recovery for rename/scaffold/log/promote. **Impact.** A refactor flipping any to fail-open lets the MCP rename tool mutate a dirty tree or run without git, silently falsifying the rollback guarantee. **Fix.** Characterization tests asserting the closed direction. **Verification.** Coverage missing exactly the claimed lines; a fail-open flip would pass the whole 1442-test suite.

### D6a-test-gaps-10 — `legacy` pytest marker is registered and auto-applied but never consumed by any selection
**File:** `pyproject.toml:69` · **Effort:** S · **Owner Q:** 5 · **Verification: CONFIRMED**

```
    "legacy: tests for pre-v3.0 legacy script compatibility layer (.ontos/scripts/tests/)",
```

**Claim.** The marker is auto-applied to every test in `.ontos/scripts/tests/` but no `-m legacy`/`-m "not legacy"` expression exists; CI runs the legacy suite by explicit path, unconditionally. **Impact.** Readers infer the legacy suite is deselectable via the marker; it is not. **Fix.** Either use it (documented `-m "not legacy"` escape hatch) or remove it with the legacy layer. **Verification.** Grep for marker selection returns only the definition and the auto-application.

### D6b-test-quality-1 — Vacuous test: assertions commented out, committed LLM narration, passes while checking nothing
**File:** `tests/commands/test_consolidate_parity.py:85` · **Effort:** S · **Owner Q:** 5 · **Verification: CONFIRMED**

```
    # assert result.returncode == 0
    # assert "Consolidated 2 log(s)" in result.stdout
```

**Claim.** `test_consolidate_count_parity` spawns the CLI twice and asserts nothing (only commented-out asserts); the body contains committed AI reasoning ("# Wait, the command needs to find the root."). **Impact.** The consolidate `--count` path appears covered but is not; the narration shows the test was committed mid-thought and never reviewed. **Fix.** Finish or delete the test; strip the narration. **Verification.** "3 passed" including the assertion-free test; the `--count` success path is asserted nowhere else.

### D6b-test-quality-2 — Dual-mode test infrastructure rotted: `--mode user` references deleted `ontos_init.py` and errors at fixture setup
**File:** `tests/conftest.py:87` · **Effort:** M · **Owner Q:** 5 · **Verification: CONFIRMED** · merges D5a-repo-redundancy-5

```
        result = subprocess.run(
            [sys.executable, 'ontos_init.py', '--non-interactive'],
            cwd=tmp_path,
```

**Claim.** The `mode_aware_project` user branch runs `ontos_init.py` from the repo root, deleted in commit e3f8f22; `pytest --mode user` errors in fixture setup; CI only ever runs the contributor default. `test_decision_history_path_respects_mode` executes zero assertions in contributor mode and mutates `sys.path`. **Impact.** The advertised user-install simulation has been dead since v3.0.1. **Fix.** Delete the dual-mode option and `test_dual_mode.py`, or rewrite around `ontos init`. **Verification.** `pytest --mode user` → "1 passed, 2 errors" (FileNotFoundError).

### D6b-test-quality-4 — ~44 subprocess-spawned `--help` tests, ~20 near-identical; should be parametrized in-process
**File:** `tests/test_cli_phase4.py:57` · **Effort:** M · **Owner Q:** 7 · **Verification: CONFIRMED** (magnitude corrected)

```
    def test_init_help(self):
        """init --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "init", "--help"],
```

**Claim.** 44 subprocess `--help` invocations; `test_cli_phase4.py` has 9 structurally identical `test_X_help` methods; parity files repeat the pattern. **Corrections.** 18 of the 44 hits are ALREADY a single parametrized test; the cited `query --help` duplication is false; cost is ~4-5s not "tens of seconds." **Impact.** Real but smaller test-hygiene item. **Fix.** Collapse into one `@pytest.mark.parametrize` over `create_parser()` (pattern already used in `test_map_compact.py`), keeping 1-2 subprocess smoke tests. **Verification.** Counts confirmed; single spawn measured 0.084s.

### D6b-test-quality-5 — "Parity" tests in name only: `golden_help` fixtures load golden files that are never compared
**File:** `tests/commands/test_query_parity.py:12` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
def golden_help():
    """Load golden help output."""
    golden_path = Path(__file__).parent / "golden" / "query_help.txt"
    return golden_path.read_text()
```

**Claim.** `test_query_parity.py`, `test_scaffold_parity.py`, `test_verify_parity.py` each inject a `golden_help` fixture that is never referenced (tests only substring-match live output), leaving all 9 files under `tests/commands/golden/` dead. **Impact.** The names promise legacy-parity verification that does not happen. **Fix.** Delete the fixtures and `tests/commands/golden/`; rename the files to what they test. **Verification.** Repo-wide grep finds zero references to 6 of the 9 golden files; introduced in the v3.1 migration commit c9fe1f9.

### D6b-test-quality-6 — Three stub tests with `pass` bodies inflate test counts without testing anything
**File:** `tests/test_validation.py:168` · **Effort:** S · **Owner Q:** 5 · **Verification: CONFIRMED**

```
    def test_t8_orphan_check_skips_draft_proposals(self):
        """T8: Orphan check skips draft proposals."""
        # This is tested in the validate_dependencies function, not validate_v26_status
        # The skip is handled by checking status == 'draft' and 'proposals/' in filepath
        pass  # Covered by existing orphan tests
```

**Claim.** Three collected tests always pass with no assertions: `test_t8_orphan_check_skips_draft_proposals`, `test_cwd_propagation`, `test_clear_cache_works`. **Impact.** Grepping for T8 orphan-skip coverage finds a named green test that verifies nothing — and its "Covered by existing orphan tests" comment is false (the production skip is exercised by no test). **Fix.** Delete or implement the three stubs. **Verification.** All three pass with zero assertions; `test_orphan_detection.py` contains no draft/proposal coverage.

### D6b-test-quality-7 — ~95 lines of MCP test infrastructure duplicated verbatim across write-tool test files, already diverging
**File:** `tests/mcp/test_write_tools.py:38` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED**

```
class RecordingPortfolioIndex:
    def __init__(self) -> None:
        self.rebuild_calls: list[tuple[str, str]] = []
```

**Claim.** `RecordingPortfolioIndex`, `_git_init_clean`, `_build_same_basename_portfolio`, `_call` are copy-pasted between `test_write_tools.py` and `test_rename_document.py` (with `_git_init_clean` also in `test_rename_scope_forced_library.py`), already drifted (rename copy adds `raise_parity_times`, different git email). **Impact.** A fix to the git-init contract must be made in three places. **Fix.** Move the helpers into the existing `tests/mcp/__init__.py`. **Verification.** 12 grep hits across 4 files; the specific drift confirmed by side-by-side reading.

### D6b-test-quality-9 — 320-line `tests/mcp/__init__.py` performs `sys.path` surgery and `sys.modules` purges at import time
**File:** `tests/mcp/__init__.py:59` · **Effort:** M · **Owner Q:** 4 · **Verification: CONFIRMED** (confidence: medium)

```
    for name in list(sys.modules):
        if name == "ontos" or name.startswith("ontos."):
            del sys.modules[name]
```

**Claim.** The MCP helpers live in a package `__init__` that reorders `sys.path`, deletes cached `ontos.*` modules, and force-reloads `mcp` from site-packages — a load-bearing workaround for the `ontos`/`.ontos` name collision from conftest's path injection, coupling every MCP test to import order. **Impact.** Any `import tests.mcp` can invalidate module identity for already-imported ontos modules mid-session (isinstance hazards). **Fix.** Move helpers to `tests/mcp/helpers.py`; convert `_ensure_*` to a session-scoped autouse fixture, or remove the root conftest `sys.path` injection. **Verification.** Reproduced module-identity split across the `tests.mcp` import.

### D7-cli-consistency-5 — `--json` success envelopes ship empty `data:{}` payloads with results flattened into prose, under `command` names that don't match the invoked subcommand path
**File:** `ontos/cli.py:48` · **Effort:** M · **Owner Q:** 2 · **Verification: CONFIRMED**

```
            data=data if data is not None else {},
```

**Claim.** Handlers routed through the `_run_*` layer return `(exit_code, message)` only, so `_emit_handler_result_json` emits every success envelope with `data:{}` and the actual results flattened into the human `message` string; and the `command` field uses ad-hoc hyphenations (`cli.py:1156` `command="mcp-install"`, `cli.py:1355` `command="export-data"`) rather than the subcommand path the parser actually invokes. **Impact.** JSON consumers must regex results out of prose, and cannot key an envelope back to the command that produced it. **Fix.** Change the `_run_*` contract to `Tuple[int,str,Dict]` (as `mcp.py` already does) and thread structured payloads through `_emit_handler_result_json`; standardize the `command` field to the space-joined subcommand path.
**Verification evidence.** `schema-migrate --check --json` → `data:{}` message "34 files need migration..."; `verify docs/alpha.md --json` → `data:{}` "Nothing to verify"; envelopes use `command="mcp-install"`/`"export-data"` while the parser invokes `ontos mcp install`/`ontos export data`.

### D7-cli-consistency-6 — `verify --portfolio --json` emits ad-hoc JSON without the envelope, and its `workspace_id` parameter is unreachable from the CLI
**File:** `ontos/commands/verify.py:470` · **Effort:** S · **Owner Q:** 2 · **Verification: CONFIRMED**

```
        print(json.dumps(payload, ensure_ascii=True))
```

**Claim.** `_emit_verify_portfolio_result` prints a bare object with no `schema_version`/`command`/`status` envelope, while plain `verify --json` uses the standard envelope; and `cli.py:1717` passes `workspace_id=getattr(args,"workspace_id",None)` but no `--workspace-id` flag is registered, so `_scope_projects` is dead from the CLI. **Impact.** One command name yields two incompatible JSON dialects depending on a flag; the dead parameter is an unfinished, untestable feature. **Fix.** Wrap the portfolio payload in `emit_command_success/error(command='verify',...)`; register `--workspace-id` or drop the parameter. **Verification.** `verify --json` → `{schema_version, command, status,...}`; `verify --portfolio --json` → bare `{clean, missing_in_db,...}`; `verify --portfolio --workspace-id alpha` → "unrecognized arguments."

### D7-cli-consistency-7 — `env --json` wraps the human text report in `data.output` instead of the structured `ontos-env-v1` payload
**File:** `ontos/cli.py:1110` · **Effort:** S · **Owner Q:** 2 · **Verification: CONFIRMED**

```
                parsed = {"output": output}
```

**Claim.** `--json` does not force `options.format='json'`, so `env --json` always hits the except branch and emits `data={"output": <prose>}`, even though a structured `$schema: ontos-env-v1` document exists behind `--format json` (which itself bypasses the envelope). **Impact.** The one command with a versioned JSON schema fails to expose it through the standard `--json` surface; consumers need the magic combo `--format json --json`. **Fix.** When `args.json` is set, force `options.format='json'` before `_run_env_command`; document `--format json` as the envelope-free raw dialect. **Verification.** All three behaviors reproduced live.

### D7-cli-consistency-8 — Error messages inconsistently split between stdout and stderr across commands
**File:** `ontos/commands/link_check.py:114` · **Effort:** S · **Owner Q:** 2 · **Verification: CONFIRMED**

```
        print(f"Error: {message}")
```

**Claim.** link-check (114), map (map.py:855/870), and the shared `--limit` validator (cli.py:935) write error text to stdout, while `main()`'s error handlers and `OutputHandler.error/warning` write to stderr — the same failure class lands on different streams. **Impact.** Scripts capturing stderr miss link-check/map/`--limit` errors; pipelines consuming stdout receive error prose; contradicts the project's own #135 discipline. **Fix.** Add `file=sys.stderr` to the non-JSON error prints (or route through `OutputHandler.error`). **Verification.** `link-check --limit 0` → error on stdout, empty stderr; `serve --workspace /nope` → error on stderr — same class, different streams.

### D7-cli-consistency-9 — Stale deprecation and remediation messages ship in v4.7.0: "removed in v3.4" promise and dead `ontos_init.py` hint
**File:** `ontos/cli.py:1447` · **Effort:** S · **Owner Q:** 7 · **Verification: CONFIRMED** · merges D5b-dead-code-4, D8-docs-clarity-9

```
    print("This alias will be removed in v3.4.", file=sys.stderr)
```

**Claim.** Bare `ontos export` still warns "removed in v3.4." thirteen minor versions late, and `paths.py:158` tells users hitting the deprecated `docs/archive/` layout to run `python3 ontos_init.py` (a v2 script absent from installs). (The never-registered `_cmd_export` handler at cli.py:1459, whose message contradicts the live one, is catalogued separately as `D3b-structure-7`.) **Impact.** Users run a nonexistent script; the unfulfilled removal promise erodes trust. **Fix.** Remove the bare-export alias or restate a real target version; replace the `paths.py:158` hint with the actual remediation — create `docs/archive/logs/` and move the archived logs into it. (Verified: `ontos init` only creates the flat `docs/archive/` directory — init.py:251/334 — and `ontos migrate` performs frontmatter-schema migration only, so neither command fixes the layout; `get_archive_logs_dir` at paths.py:332–343 auto-prefers the nested path once it exists.) Dead-handler deletion is tracked under `D3b-structure-7`. **Verification.** `ontos export` prints the v3.4 line; `docs/archive/` project → FutureWarning citing `ontos_init.py`; CHANGELOG dates 3.4.0 to 2026-04-04.

### D7-cli-consistency-10 — `sys.argv` string-scan fallback for `--json`/`--quiet` misfires on positionals after `--`
**File:** `ontos/cli.py:1803` · **Effort:** M · **Owner Q:** 4 · **Verification: CONFIRMED**

```
    if '--json' in sys.argv and not args.json:
        args.json = True
```

**Claim.** The workaround for argparse parent-parser default clobbering scans raw `sys.argv` for `--json`/`-q`/`--quiet`, so any invocation where those literals appear as data (`ontos log --auto -- --json`) silently flips the command into JSON/quiet mode. **Impact.** A fragility magnet for every new global flag added to the parent parser. **Fix.** Give subparser copies `default=None`/`SUPPRESS` so the parent-parsed value survives, or `parse_known_args` before dispatch. **Verification.** `ontos log --auto -- --json` emitted a JSON envelope and created a log slugged `2026-07-02_json` instead of treating `--json` as topic text.

### D3b-structure-7 — Dead duplicate handler `_cmd_export` shadows the live `_cmd_export_deprecated` with contradictory guidance, kept alive only by a test asserting the wrong behavior
**File:** `ontos/cli.py:1459` · **Effort:** S · **Owner Q:** 3 · **Verification: CONFIRMED** · merges D5b-dead-code-5

```
def _cmd_export(args) -> int:
    """Handle export command (deprecated - delegates to agents)."""
```

**Claim.** No parser sets `func=_cmd_export` (bare export routes to `_cmd_export_deprecated`), so the 27-line function is unreachable; it warns "Use 'ontos agents'" and delegates to `_run_agents_command` while the real handler warns "Use 'ontos export claude'/'export data'." Its only reference is `tests/commands/test_agents.py:438`, which green-lights the divergent behavior. **Impact.** The test suite certifies behavior users can never reach. **Fix.** Delete `_cmd_export`, repoint the test at `_cmd_export_deprecated`. **Verification.** `parse_args(['export']).func.__name__ == '_cmd_export_deprecated'`; `_cmd_export` wired to no parser.

### D8-docs-clarity-3 — Manual's consolidation ritual command silently ignores `--days`
**File:** `docs/reference/Ontos_Manual.md:326` · **Effort:** S · **Owner Q:** 1 · **Verification: CONFIRMED**

```
   ontos consolidate --days 30
```

**Claim.** §5 "The Ritual" tells users to run `ontos consolidate --days 30`, but `--days` is only honored with `--by-age`; without it the command runs count-based keep-newest-15 and the 30-day threshold is silently discarded. **Impact.** Users performing monthly consolidation archive a different set of logs than the Manual promises — no error, no warning — on a command that moves files and rewrites decision history. **Fix (two tracks).** (1) Docs: fix the Manual to `ontos consolidate --by-age --days 30` — S, lands in the Release N doc sweep. (2) CLI: make an explicit `--days` imply `--by-age` (or error) — a behavior change on a file-moving command, so it belongs with the Release N+1 CLI work behind a characterization test that pins current flag semantics first. **Verification.** 20 logs >30 days old: `consolidate --days 30 --dry-run --all` → "Found 5 log(s)" (count-based), not 20.

### D8-docs-clarity-6 — No current, discoverable architecture overview of the ontos package for contributors
**File:** `README.md:638` · **Effort:** M · **Owner Q:** 7 · **Verification: CONFIRMED** (claim narrowed)

```
Issues and PRs welcome. If you're planning something substantial, open an issue first so we can align on direction.
```

**Claim (narrowed).** No CONTRIBUTING.md exists and `docs/reference/` is end-user material. The headline "no document anywhere" was overstated — two arch maps exist under `.ontos-internal/analysis/` — but they are v3.0.1/v3.0.2-era (describe `mcp/` as a "1 file stub" vs 14 modules today), not indexed by the checked-in HEAD map (scope: docs), and not linked from README. **Impact.** A new contributor to a ~61-module, 835-commit codebase must reverse-engineer module boundaries; multi-model history rebuilt overlapping areas an arch doc would have anchored. **Fix.** Add a current `docs/reference/Architecture.md`/CONTRIBUTING.md with the module map and frontmatter→graph→validation→map/bundle data flow; register it as an atom so activation surfaces it.

### D8-docs-clarity-7 — Active `docs/logs/` stream can never be pruned by the tool on this repo; Tier-1 shows 63 unpruned no-signal logs (97 map rows)
**File:** `Ontos_Context_Map.md:36` · **Effort:** M · **Owner Q:** 7 · **Verification: CONFIRMED** (inference corrected)

```
| ... and 94 more logs | | |
```

**Claim (corrected).** The central inference "ontos consolidate has never run here / its ledger was never created" is false: this repo runs in CONTRIBUTOR mode, so consolidate targets `.ontos-internal/logs` and the ledger at `.ontos-internal/reference/decision_history.md` (which exists, git-tracked, with 77 archived logs — consolidation demonstrably has run). What survives: `docs/logs/` holds 63 session logs, all "No summary" (the map's 97 log rows additionally count 34 log-typed release/retro/review/tracker documents elsewhere in the docs tree); `docs/strategy/decision_history.md` and `docs/reference/Common_Concepts.md` are absent so the docs-tree Historical Recall path in Agent Instructions dangles; and because `.ontos.toml` sets `logs_dir=docs/logs` while contributor-mode consolidate only touches `.ontos-internal/logs`, the active `docs/logs` stream can never be pruned by the tool on this repo. **Impact.** Tier-1 orientation is dominated by an uninformative unpruned log table; a genuine dogfooding gap, narrower than the finding claimed. **Fix.** Reconcile `logs_dir` vs the contributor-mode store so the dogfood repo's active logs are actually consolidatable — this spans mode-resolution semantics in paths/consolidate plus dogfood-repo config migration (M). A config-only stopgap (point `.ontos.toml` `logs_dir` at the store consolidate actually targets) is S if the semantic reconciliation is deferred.

### D8-docs-clarity-8 — Repo CLAUDE.md prescribes the pre-v4.4 session ritual, contradicting the package's own generated protocol
**File:** `CLAUDE.md:8` · **Effort:** S · **Owner Q:** 7 · **Verification: CONFIRMED**

```
1. Run `ontos map` to generate the context map
```

**Claim.** The root CLAUDE.md tells every session to start with `ontos map` and end with bare `ontos log`, while the v4.7.0 generator and the repo's own AGENTS.md:33 mandate `ontos activate` for start and `ontos log -e "slug"` for end, plus trigger phrases and post-compaction recovery CLAUDE.md lacks. **Impact.** Claude Code sessions (the primary development driver) follow a weaker ritual than the product ships; the two root instruction files disagree about the activation contract; the project is not dogfooding its own `ontos export claude`. **Fix.** Regenerate with `ontos export claude --force`, then re-add the project overview inside the preserved USER CUSTOM block. **Verification.** CLAUDE.md last touched 2026-01-28 (v3.2 era, 21 lines); AGENTS.md generated by v4.7.0 mandates `activate`/`log -e`.

### What is working well

Credit where due, so the register above reads in proportion: the suite is healthy — 1,442 passing tests, 77.76% coverage, zero failures. The JSON-envelope infrastructure (`emit_command_success/error`) already exists, so most of the envelope findings are wiring gaps, not missing architecture. Editable-install discipline (`pip install -e ".[dev,mcp]"` locally and in CI) is exactly what defuses the would-be PYTHONPATH hazard refuted in Appendix A. And the new v4.7 modules land at or near full coverage (`warning_groups.py` at 100%), making the newest slice the cleanest in the attribution map.

---

## 5. Execution roadmap

Ordered so that quick wins land first, characterization tests bracket every refactor, and the structural work follows once the net is in place. Rough sequencing across three releases.

### Release N (immediate — the ship-blocker and the cheapest high-value wins)

**Quick wins (S, low-risk, mostly one-file):**
1. `D2b-roundtrip-3` (P0) — replace `serialize_frontmatter` with `yaml.safe_dump`-backed serialization + a re-parse assertion. This is the keystone: it also resolves `D3b-structure-1` (log corruption) once log.py routes through the shared serializer.
2. `D2b-roundtrip-1` — decode strictly in `_read_decoded_content`; skip non-UTF-8 files with a warning.
3. `D2a-write-safety-7` — `write_text(..., encoding='utf-8')` (one line).
4. `D2a-write-safety-2` — explicit `git ls-files --error-unmatch` trackedness check before unlink.
5. `D3b-structure-2` — swap the dead `ontos_config` import for `get_logs_dir()`.
6. `D1b-counts-1`, `D1b-counts-2`, `D1b-counts-4` — load `known_concepts` in `run_activation`; add `max_dependency_depth` to the snapshot orchestrator + MCP `context_map`; label/rename maintain's `broken_links`.
7. `D7-cli-consistency-1` — route map's load-diagnostics/sync-agents to stderr; emit an error envelope on the fatal-load path.
8. `D4a-config-2` — extend the config type table to `scanning.*`/`paths.*`.
9. `D4b-trust-1` — gate/remove the `ontos doctor` MCP-config probe.
10. Doc/dead-code sweep: `D8-docs-clarity-1/2/3/5/8` (docs-clarity-3: docs half only — the `--days` behavior change moves to Release N+1), `D7-cli-consistency-9`, `D3b-structure-7`, `D5b-dead-code-2/6/7/8/9/10`, `D5a-repo-redundancy-3/6`.

### Release N+1 (characterization tests, THEN the parser/CLI structural work)

**Characterization tests first — pin current behavior before touching it:**
- `D6a-test-gaps-4` (hook strict blocking), `D6a-test-gaps-9` (MCP fail-closed guards), `D6a-test-gaps-8` (TOML round-trip), `D6a-test-gaps-7` (query dispatch), and a promote/migrate rewrite test (`D2b-roundtrip-4` / `D6a-test-gaps-3`).
- A consolidate flag-semantics characterization test, then the CLI half of `D8-docs-clarity-3` (explicit `--days` implies `--by-age`, or errors).
- Recapture or replace the golden-master net (`D6a-test-gaps-6`) so output-format regressions in `map`/`log` are caught during the refactors below.
- Clean the rotted tests that would otherwise give false green during refactors: `D6b-test-quality-1/2/5/6`.

**Then the structural work (with the net in place):**
- **Parser consolidation** — one fence-aware `^---$` splitter for all five readers, delete `_fallback_yaml_parse`, route `history.py` through the canonical loader (`D3a-parsers-3`, `D3a-parsers-2`). The `D1a-graph-link` line-number and fence fixes become tractable in the same pass (`D1a-graph-link-2/3`).
- **Write-path unification** — route promote/migrate/promote_document through `frontmatter_edit` (`D2b-roundtrip-4`, `D2b-roundtrip-5`); fix the body-reference scanner (`D1a-graph-link-1/6`, then `-7` output-neutral pass removal).
- **MCP dispatch unification** — extract `_write_common.py` and one error boundary (`D3b-structure-3/4/5/8`); harden rename locking/rollback (`D2a-write-safety-3/5/6/8/9`).

### Release N+2 (the large, coordinated changes)

- **Exit-code taxonomy + envelope-status unification + structured `data` payloads** — `D7-cli-consistency-3/4/5/6/7`, `D1c-envelope-4/5`, behind a single `schema_version` bump.
- **cli.py declarative command table** — `D3b-structure-6` (fixes the `tree -f`/`validate --portfolio` drift as a byproduct).
- **Pre-commit/CI rewire → then repo slimming** — point hooks/CI at the `ontos` CLI (add `map --check`), port/delete the 11 legacy-coupled tests, then archive `.ontos/scripts/` and its vendored fork (`D5a-repo-redundancy-1/2`); extract the frozen `.ontos-internal/archive/` and `.project-internal/` (`D5a-repo-redundancy-4`); adopt the generated-artifact churn policy (`D5a-repo-redundancy-7`).
- **Graph traversal iterative rewrite** (`D1a-graph-link-4`) and case-insensitive path handling (`D1a-graph-link-5`) as isolated correctness fixes.

---

## 6. Appendix A — Refuted findings (checked and cleared)

| ID | Claim | Why refuted |
|---|---|---|
| **D6b-test-quality-3** | Five subprocess test files set `PYTHONPATH` from `os.getcwd()`/`Path.cwd()`, so pytest run from outside the repo root could silently test the installed site-packages copy instead of the checkout. | Descriptive facts accurate, but the failure mode is guarded and does not reproduce. The project installs `ontos` **editable** (`pip show ontos` → "Editable project location: .../Project-Ontos"; CI runs `pip install -e ".[dev,mcp]"`), so `sys.executable -m ontos` resolves to the checkout regardless of `PYTHONPATH`/cwd. Reproduced the scenario: from a non-repo cwd with `PYTHONPATH=$(pwd)`, `import ontos` resolved to the repo under test and the cited tests passed while exercising the checkout. The only failing scenario requires a NON-editable install (no project workflow produces one) or no install at all (subprocess fails loudly with `ModuleNotFoundError` — `test_b1` even asserts its absence), so the failure could never be silent. Survives only as a cosmetic inconsistency, not the stated wrong-package hazard. |

---

## 7. Appendix B — Measured coverage table

**Suite:** 1,442 passed, 2 skipped, 0 failed in 85.84s (Python 3.14.6). **Overall coverage: 77.76%** over 13,521 statements. The two skipped tests are the disabled golden-master pair (`D6a-test-gaps-6`).

*Note on "claimed-untested" modules: most are in fact well covered; earlier confusion traced to basename collisions with the vendored legacy copies under `.ontos/scripts/ontos/` (see `D5a-repo-redundancy-2`).*

| Module | Coverage | Note |
|---|---:|---|
| `ontos/commands/promote.py` | 33.3% | **Real cold spot** — 213 stmts, 142 missed; entire file-rewrite chain uncovered (`D2b-roundtrip-4`) |
| `ontos/core/tokens.py` | 36.4% | Trivial (11 stmts) |
| `ontos/core/suggestions.py` | 43.9% | 98 stmts, 55 missed (`D6a-test-gaps-2`) |
| `ontos/commands/stub.py` | 53.0% | 117 stmts, 55 missed |
| `ontos/commands/hook.py` | 58.5% | Strict-blocking branch untested (`D6a-test-gaps-4`) |
| `ontos/commands/query.py` | 59.9% | `query_stale` + 4 flag branches uncovered (`D6a-test-gaps-7`) |
| `ontos/core/git.py` | 62.2% | Fail-closed guards uncovered (`D6a-test-gaps-9`) |
| `ontos/commands/verify.py` | 64.1% | 273 stmts, 98 missed |
| `ontos/core/paths.py` | 65.8% | User-mode/back-compat chains untested (`D6a-test-gaps-5`) |
| `ontos/commands/migration_report.py` | 70.9% | 86 stmts, 25 missed |
| `ontos/core/curation.py` | 72.8% | Real coverage despite "claimed-untested" |
| `ontos/commands/migrate.py` | 73.9% | 165 stmts, 43 missed |
| `ontos/mcp/server.py` | 74.1% | MCP entry point; 301 stmts, 78 missed |
| `ontos/commands/maintain.py` | 74.3% | Largest command module (486 stmts) |
| `ontos/commands/migrate_cmd.py` | 75.7% | — |
| `ontos/commands/doctor.py` | 76.0% | 371 stmts, 89 missed |
| `ontos/commands/mcp.py` | 76.2% | 227 stmts, 54 missed |
| `ontos/commands/consolidate.py` | 76.3% | 228 stmts, 54 missed |
| `ontos/commands/init.py` | 76.7% | 270 stmts, 63 missed |
| `ontos/commands/activate.py` | 77.1% | 105 stmts, 24 missed |
| `ontos/core/snapshot.py` | 77.2% | 57 stmts, 13 missed |
| `ontos/core/mcp_shared.py` | 77.8% | Uncovered lines mostly Protocol stubs / probe error branches |
| `ontos/core/history.py` | 84.8% | Well covered |
| `ontos/core/instruction_artifacts.py` | 89.1% | Well covered |
| `ontos/core/frontmatter.py` | 89.8% | Well covered |
| `ontos/mcp/writes.py` | 90.6% | Well covered |
| `ontos/core/staleness.py` | 91.2% | Well covered |
| `ontos/core/errors.py` | 94.1% | Trivial |
| `ontos/core/types.py` | 94.5% | Well covered |
| `ontos/core/graph.py` | 94.9% | Well covered |
| `ontos/core/validation.py` | 96.9% | Dedicated `test_validation.py` (30 tests) |
| `ontos/core/content_hash.py` | 100% | Fully covered |
| `ontos/core/warning_groups.py` | 100% | Fully covered (v4.7 Fable slice) |

**Reachability check (four named "possibly-unreachable" paths):** none are dead. `ontos/mcp/cursor_mcp.py` and `ontos/mcp/antigravity_mcp.py` **do not exist** (the adapters live at `ontos/core/cursor_mcp.py` / `ontos/core/antigravity_mcp.py`). `ontos/core/cursor_mcp.py` is CLI-reachable via `doctor.py:784` and `mcp.py:17` (93.2% covered); `ontos/core/antigravity_mcp.py` via `doctor.py:742` and `mcp.py:9` (82.8% covered). Neither is referenced by `ontos/mcp/server.py`, but both are CLI-reachable and tested.

---

## 8. Appendix C — Model-attribution map

Derived from `Co-Authored-By` trailers across 835 commits (~560 carry no trailer — merges and human-only commits by Jonathan Oh). Per-finding attribution in Q2 is inferred from this file/feature churn map, not per-line `git blame`; cross-slice findings are flagged in-line.

| Slice | Model | Commits / window | Owned surface (churn) | Confirmed findings (inferred) | Worst |
|---|---|---|---|---:|---|
| **A** | **Claude Opus 4.5** | 183 commits, 2025-12-09→2026-01-29 (v2.x→v3.0.0→v3.2.0) | Script→package migration and most of `ontos/core` + `commands`; the CLI; the v2-era Manual/Agent docs; the `.ontos/scripts` legacy layer + vendored fork; `_templates`/`_hooks` packaging | ~54 | **D2b-roundtrip-3 (P0 serializer)** |
| **B** | **Claude Opus 4.6 / 4.6 (1M)** | 37 commits, 2026-02-06→2026-04-15 (v3.3→v4.3.0) | MCP write-tools/portfolio/retrofit/rename expansion (`writes.py`, `rename_tool.py`, `portfolio.py`, `retrofit.py`, `snapshot.py`) | ~14 | **D2a-write-safety-3 (MCP rename scope bypass → duplicate IDs)** |
| — | *unattributed* | 4 commits, v4.3.0→v4.4.0 | One squash ("v4.4 agentic activation resilience", 0260880); model tracked only in `manifests/…v44….yaml` | (folded into C) | — |
| **C** | **Claude Opus 4.7 (1M)** | 33 commits, 2026-05-21→2026-05-23 (v4.4.0→v4.6.0, #115-117/#119 + v4.7-window hygiene #122-130) | `core/graph.py`, `core/body_refs.py`, `core/types.py`, `mcp/tools.py`, `commands/doctor.py`, activation resilience | ~13 | **D4b-trust-1 (RCE via `ontos doctor`)** |
| **D** | **Claude Fable 5** | 13 commits, 2026-06-10→2026-06-24 (v4.7.0 #131-136, docs PR #143) | `core/link_diagnostics.py` (+321), `commands/link_check.py`, `core/warning_groups.py` (new), `core/ontology.py`, shared `graph.py`, ~1,700 test lines, v4.7 client docs | 7 | **D7-cli-consistency-4 / D1b-counts-4 (link-check surface diverges from sibling commands)** |
| — | *one-off* | 1 commit | "Codex Adversarial Reviewer" trailer | — | — |

**Reading of the map for Q2:** 81 of 88 confirmed findings fall in Opus-authored slices; the Fable v4.7 slice is the cleanest (7 findings), and most of those are cross-surface consistency gaps the new link-check surface *exposed* in older commands rather than fresh regressions, plus one provably output-neutral perf pass (`D1a-graph-link-7`). The foundational Opus 4.5 slice carries the lone P0 and the bulk of the structural/legacy debt; the Opus 4.6/4.7 slices carry the write-safety and graph/trust-boundary defects. The recurring cross-slice pattern is a new parallel surface added without reconciling it against the existing ones — the root cause of the count, envelope, and exit-code contradictions catalogued above.