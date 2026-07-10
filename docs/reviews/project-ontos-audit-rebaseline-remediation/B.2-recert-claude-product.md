---
id: project-ontos-audit-rebaseline-remediation-B.2-recert-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: product
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

Reviewer scope note: corrected spec v1.2 at
`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md` (current HEAD
`5e04094`) reviewed against frozen implementation snapshot I0
`b6f89d77e7fb684b8bd9a181a24c773d5777397a`. Per the manifest's
`implementation_sequencing.mode: code-first-user-gated` (`user_gate_ref`
recorded), §2.2 spec-vs-implementation cross-reference is in scope and was run
against I0 bytes read via `git show b6f89d7:<path>` — NOT the current worktree,
which carries an in-progress Phase C. No other verdict was consulted.

## 1. User-value assessment

The user here is an **Ontos adopter/operator** and the **release maintainer**.
The adopter's job-to-be-done is to run Ontos against their documentation repo
and trust that (a) their frontmatter survives edits without silent corruption,
(b) a version-incompatible install fails loudly instead of misbehaving, and (c)
CLI/MCP/JSON outputs are stable enough to script against. The maintainer's job
is to certify a 188-file integration branch without accidentally telling users
"this is released" when Windows, TestPyPI, PyPI, and per-issue GitHub evidence
are still pending.

Spec v1.2 serves both jobs by pinning each user-visible contract to exact copy,
error codes, and exit semantics, and by repeatedly and consistently refusing to
convert an unavailable external into certification (§§2–3, §8, §9). This is the
right thing to build: it is a lifecycle review that makes the user-facing
behavior *testable and honest*, not a release. The problem statement (§1, §8)
reflects the real adopter need — "will my documents survive and will failures be
legible?" — rather than a proxy. The B.2 incorporation note (§1) and the
out-of-scope list (§2) hold the line that approval does not certify Phase C,
D.5, any child lifecycle, or a release. That nonclaim discipline is itself a
user-protecting product decision and it survives from B.1 into v1.2 intact.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | copy/error — `Incompatible Ontos version: running X, but this project requires 'Y'. Use a compatible Ontos installation.` | §4.4, §11 (runtime version row) | `ontos activate` under a `[ontos].required_version` mismatch |
| S-2 | copy/error — `Invalid [ontos].required_version 'X': …` | §4.4 | `ontos activate` with a malformed range clause |
| S-3 | state/JSON — `error.code: E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, shell exit `1` | §4.4 | `ontos activate --json` on any unusable state |
| S-4 | copy/error — `Document id must be a string…` / `Document id must not be empty` / pattern message | §4.2 | Loading or mutating a doc whose `id` is non-string, empty, or off-pattern |
| S-5 | state — batch load `parse_error`; CLI-supplied invalid ID → `E_USER_INPUT` | §4.2 | `ontos map`/CLI mutation against an invalid ID |
| S-6 | copy/error — `Session log already exists: <path>` (`E_LOG_EXISTS`), never overwrites | §4.3 | `ontos log` when the target log path already exists |
| S-7 | JSON envelope — top-level keys `schema_version, command, status, exit_code, message, result, data, warnings, error`; schema `4.0` | §4.4 | Any `--json` command |
| S-8 | exit taxonomy — `0` clean, `1` findings, `2` usage, `3` warnings, `5` internal, `130` interrupted; `4` reserved | §4.4, §7 | Scripting against any command's exit code |
| S-9 | copy — doctor PATH-skew warnings with `Use '<py> -m ontos' as the fallback.` guidance | §4.4 (doctor probes) | `ontos doctor` with a skewed/broken PATH `ontos` |
| S-10 | behavior — read-only MCP omits write tools, refuses persistent graph export, suppresses usage logs | §4.4 | Connecting an MCP client in read-only mode |
| S-11 | doc copy — Migration_v3_to_v4 + Ontos_Manual sections covering version ranges, ID quoting, `parse_error`, `E_USER_INPUT`, `E_LOG_EXISTS`, schema `4.0`, reserved code `4`, exit taxonomy | §7 | Adopter reading migration/reference docs before adopting `required_version` |
| S-12 | external-evidence wording — Windows/TestPyPI/PyPI/GitHub stated as pending/blocking, never certified | §2, §3, §8, §9 | Reader deciding whether this review means "released" |

Copy completeness: S-1…S-9 are declared with exact leading strings and error
codes, and each carries an implementation and test anchor in §11, so the copy is
a checkable contract rather than prose intent. S-11 (docs) is correctly declared
as a Phase C gate whose drift "blocks D.1," and S-12 is stated consistently in
four places. No copy string is left ambiguous or unanchored at spec time.

### 2.2 Spec-vs-implementation cross-reference (code-first; against I0 `b6f89d7`)

| Spec-declared surface (from §2.1) | In implementation? | Implementation surface (I0) | Matches §2.1? |
|-----------------------------------|--------------------|-----------------------------|----------------|
| S-1 | yes | `config.py` `required_version_incompatibility` → `"Incompatible Ontos version: running … requires …. Use a compatible Ontos installation."` | yes |
| S-2 | yes | `config.py` → `f"Invalid [ontos].required_version {required!r}: {exc}"` | yes |
| S-3 | yes | `activate.py` `_not_usable(...)` → `code="E_ACTIVATION_UNUSABLE"`, `"status": "not_usable"`, returns `1` | yes |
| S-4 | yes | `schema.py::validate_document_id` — leading strings match exactly | yes |
| S-6 | yes | `log.py` → `message = f"Session log already exists: {output_path}"`, `code="E_LOG_EXISTS"`, exclusive `open("x")` never overwrites | yes (copy gap, PRD-1) |
| S-7/S-8 | yes | `ui/json_output.py` — `COMMAND_ENVELOPE_SCHEMA_VERSION = "4.0"`; `ExitCode` enum = {0,1,2,3,5,130}; `4` absent → reserved | yes |
| S-9 | yes | `doctor.py::check_cli_availability` — PATH probe with `Use '… -m ontos' as the fallback.` details | yes |
| S-11 | **pending (correctly)** | Migration/Manual copy is a declared Phase C deliverable; not required to exist at I0 | yes — honest deferral |

Every user-visible copy string and error code the spec promises resolves to
matching bytes at I0; there is no spec-declared surface the code fails to reach,
and no I0 user-visible surface in the reviewed set is undocumented by §2.1. The
one honest gap — S-11 migration/reference copy — is a spec-declared Phase C gate,
not a silent omission, and I0's absence of it is expected under code-first
sequencing (implementation preceded the doc pass).

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | Adopter adds `[ontos].required_version` to `pyproject`, then an older Ontos on PATH/CI/hook meets it | A pre-adoption runtime may reject the key or fail activation; the failure surfaces on someone else's machine before the adopter sees a warning | should-fix (mitigated) | §7 requires an explicit upgrade-and-verify warning across repo/PATH/hook/CI — the correct mitigation, static-inspection |
| U-2 | Operator hits `E_LOG_EXISTS` on `ontos log` | Error states the path but not the next step; operator must guess (delete? new slug? where is the old log?) | should-fix | I0 `log.py` copy, static-inspection — see PRD-1 |
| U-3 | Adopter meets S-1/S-2 activation error | Message names the incompatibility but does not point to the Migration/Manual section that explains supported ranges | minor | I0 `config.py` copy, static-inspection — see PRD-2 |

## 4. Copy review

| ID | Surface | Current copy (I0) | Issue | Suggested alternative |
|----|---------|-------------------|-------|-----------------------|
| C-1 | log collision | `Session log already exists: <path>` | No recovery direction in a path a user reaches during normal work | Append actionable next step, e.g. `… ; rerun with a different session slug or remove the existing log to regenerate.` |
| C-2 | activation incompat | `… requires 'Y'. Use a compatible Ontos installation.` | Good direction; does not say how to find the compatible version or that the range itself can be adjusted | Add a pointer to the Migration/Manual `required_version` section (see PRD-2) |
| C-3 | doctor PATH skew | `Use '<py> -m ontos' as the fallback.` | Exemplary — names the failure and a concrete recovery command | Keep as-is (positive) |

Spec-declared copy is honest and non-hedging; the leading-string contracts (S-1,
S-2, S-4) are testable via `startswith`. The two refinements above are UX copy,
not correctness, and belong to this lens.

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| CLI/JSON is the entire user surface; no GUI/contrast/focus concerns apply | static-inspection | n/a | — |
| Machine-readability of failure: every error path carries a stable `code` + `data` in JSON mode (S-3, S-6, S-7), which is the CLI equivalent of a screen-reader hook for automation | I0 `activate.py`/`log.py`/`json_output.py`, static-inspection | positive | — |
| Localization | No i18n hooks; English-only copy | minor/out-of-scope | localization — not a regression this deliverable introduces |

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Version incompatible | S-1 copy + exit `1` + `E_ACTIVATION_UNUSABLE`/`not_usable` (JSON) | Yes — "use a compatible installation"; discoverability of *how* is thin (PRD-2) | I0 `activate.py`, `config.py` — static-inspection |
| Invalid range clause | S-2 copy + exit `1` | Yes — names the offending value | I0 `config.py` — static-inspection |
| Invalid/non-string/empty ID | S-4 copy; batch → `parse_error`; CLI → `E_USER_INPUT` | Yes — message states the rule; §7 doc copy covers YAML date/numeric/null quoting so the *cause* is discoverable | I0 `schema.py` — static-inspection |
| Log collision | S-6 copy + exit `1` + `E_LOG_EXISTS`; existing log never overwritten (data-safe) | Partial — no next-step guidance (PRD-1) | I0 `log.py` — static-inspection |
| Interrupted multi-file write | Best-effort rollback with retained recovery evidence; durable crash recovery explicitly one of the 7 partial areas | Honest partial | §4.3 — static-inspection |
| Doctor PATH skew | S-9 warning + fallback command | Yes — exemplary | I0 `doctor.py` — static-inspection |
| External (Windows/TestPyPI/PyPI/GitHub) unavailable | Explicit pending/blocking state; no synthetic receipt | Correct — no false green | §3, §9 — static-inspection |

The spec's failure-visibility posture is strong: no dead-ends that lose user
data (log collision refuses to overwrite), and every external unavailability
degrades to an explicit blocker rather than a fabricated pass.

## 7. Issues found

### Blocking
None. No user-facing regression, inaccessible surface, failure dead-end, or
misleading error-path copy rises to blocking, and blocking Product findings
require `direct-run` evidence I do not have for a UX regression here.

### Should-fix (Major — degrades UX without blocking ship)
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | The `E_LOG_EXISTS` contract (§4.3, S-6) declares the collision message but neither the spec nor I0 copy gives the user a recovery step. `ontos log` on a day with an existing log lands the operator in a "already exists" state with no guidance, on a normal-work path. | spec §4.3; I0 `ontos/commands/log.py` (`Session log already exists: {output_path}`) | static-inspection | `git show b6f89d7:ontos/commands/log.py` — collision branch emits path only | Have the spec require the `E_LOG_EXISTS` copy to include an actionable next step (different slug / remove existing / where the log is). Keep the no-overwrite guarantee. |
| PRD-2 | The `required_version` adoption story (§7, S-1/S-2/S-11) is data-safe but under-discoverable: the activation/invalid-range errors do not reference the Migration/Manual section §7 mandates, so a user first meeting the new `[ontos].required_version` key at a failure has no in-product pointer to the contract that explains it. | spec §4.4, §7; I0 `ontos/core/config.py` messages | static-inspection | `git show b6f89d7:ontos/core/config.py` — messages carry no doc pointer | Have the spec require the activation-incompatibility / invalid-range copy (or its JSON `data`) to name the Migration/Manual `required_version` section, tying S-1/S-2 to S-11. |

### Minor
| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|
| PRD-3 | Copy is English-only with no localization hook. Not a regression this deliverable introduces; noted for completeness. | I0 error strings | static-inspection | Out of scope; track separately if i18n is ever a goal. |

## 8. Positive observations

- **Nonclaim discipline is a user-protecting product decision, held consistently.**
  §2 out-of-scope, §3 ("No dependency may be converted into a synthetic
  receipt"), §8 risk row "Scope overclaim," and §9 exclusion list all repeat that
  this umbrella review is not a release and not per-issue certification. A reader
  cannot mistake B.2 approval for "shipped."
- **Every user-visible contract is pinned to exact copy + code + exit + a
  test/impl anchor (§11)**, so the contracts are testable by leading-string and
  key-set assertions, not left as intent. I confirmed S-1…S-9 match I0 bytes.
- **Data-safety by construction:** log collision refuses to overwrite (exclusive
  `open("x")`), and interrupted writes are honestly labeled best-effort rollback
  with durable crash-recovery called out as still-partial — no false assurance.
- **Doctor's PATH-skew copy (S-9)** is a model failure message: it names the
  failure and hands the user a concrete fallback command.
- **External unavailability always degrades to an explicit blocker**, never a
  synthesized green — the single most important honesty property for a
  release-adjacent review.

## Verdict
Approve

## Notes

I am confirming the dispatch question: spec v1.2 **does** make the user-visible
contracts in my focus areas — required-version adoption, string/YAML ID
migration, exact error codes and copy, log/MCP failure recovery, JSON/exit
compatibility, documentation discoverability, and external release-evidence
wording — testable and honest, and it does so **without** claiming release
readiness or per-issue certification. All spec-declared user-visible copy and
error codes I sampled (S-1…S-9) resolve to matching bytes at frozen I0
`b6f89d7`; the only deferred surface (S-11 migration/reference docs) is an
explicit Phase C gate whose drift blocks D.1, which is the correct disposition
under code-first sequencing rather than an omission.

The two should-fix findings (PRD-1 recovery copy for `E_LOG_EXISTS`; PRD-2
discoverability pointer from the activation/version errors to the mandated docs)
are UX refinements to already-honest contracts, not blockers; they do not
weaken any nonclaim and can be absorbed as Phase C copy/spec touch-ups. They are
`static-inspection`-only and therefore cannot gate advance on their own (P5).

Lens boundaries respected: I did not perform scope/forbidden-path/cardinality
checks (mechanical gate), did not enumerate spec surfaces for compliance
(Alignment), and did not assess reachability of hostile inputs (Adversarial) —
where a finding touched failure-visibility I framed only "does the user
understand and recover?" Overlap with Adversarial on the log-symlink and
malformed-row hardening (§4.3/§4.1) is left to that lens; I take no position on
reachability. This review consulted no other verdict.

## Final report — project-ontos-audit-rebaseline-remediation / B.2 / product / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/B.2-recert-claude-product.md
- Smoke checks: n/a for review role (no code authored) = not-run (evidence: not-run)
- Cardinality checks: n/a for Product review role = not-run (evidence: not-run)
- Commit: not committed by worker (orchestrator stages Product artifacts per Template 01 commit-split)
- Notes: Verdict Approve with 2 should-fix (PRD-1, PRD-2) + 1 minor (PRD-3), all static-inspection, non-gating. I0 evidence read via `git show b6f89d7:<path>`; current worktree Phase C intentionally not treated as I0.
