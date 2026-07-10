---
id: audit-rb-B1-glm-peer
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: peer
family: glm
evidence_labels_used:
  - direct-run
  - static-inspection
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.1 / glm

## 1. Completeness check

The spec (v1.1) includes every mandatory Template 12 section — Overview,
Scope, Dependencies, Technical Design (§§4.1–4.5), Open Questions, Test
Strategy, Migration/Compatibility, Risk Assessment, Exclusion List,
Diagrams (§10), Contract/Invariant-to-Evidence Matrix (§11),
Helper-Divergence Disclosure (§12), and Self-Review (§13). No section is
a stub, placeholder, or TBD. All four Open Questions (§5) carry Resolved
status with a recommendation.

The §1 evidence baseline and the direct-read citations throughout §4 were
verified against the frozen I0 commit `b6f89d7` (188 files changed,
+9520/-4356), whose parent is `bf91b42` — the immutable SHA pair the
spec pins (direct-run: `git show -s`, `git show --stat`).

Direct-read verification of load-bearing registry/code claims:

- Registry cardinality (direct-run: YAML parse of the registry at `b6f89d7`):
  100 findings = 91 `origin: fable_audit` originals + 9
  `origin: codex_revalidation` R2-* findings. Originals' severity totals are
  exactly P0=1 / P1=27 / P2=63, and the validator hardcodes that expectation
  at `scripts/validate-audit-remediation-registry.py` (the
  `Counter({"P0": 1, "P1": 27, "P2": 63})` assertion). R2-* severity is
  P1=8 / P2=1 (additive across all 100 = P0=1 / P1=35 / P2=64).
- Status decomposition matches the spec's evidence baseline exactly: 41
  `confirmed_open` and 7 `partial_implementation_uncommitted_verification_pending`
  (direct-run). The spec does not overclaim the remaining implemented/finished
  counts.
- `scripts/validate-audit-remediation-registry.py:18-50` —
  `REQUIRED_FINDING_FIELDS` set and `EXPECTED_R2_IDS` (nine entries) present
  (direct-run).
- `ontos/core/schema.py:315-343` — `serialize_frontmatter(fm: Dict[str,
  Any]) -> str` signature and `field_order` list (direct-run).
- `ontos/core/schema.py:83-97` — `validate_document_id` raises
  `ValueError("Document id must be a string…")`, `ValueError("Document id
  must not be empty")`, and a pattern-failure message matching the spec copy
  (direct-run).
- `ontos/core/locking.py:13-81` — `fcntl`/`msvcrt` guarded imports
  (no unconditional Windows-incompatible import) (direct-run).
- `ontos/core/config.py:239-266` — `version_satisfies_requirement` with the
  `"Invalid [ontos].required_version"` and `"Incompatible Ontos version"`
  copy; `:279-345` widens to `_version_clause_matches` /
  `_parse_requirement_base` / `_wildcard_clause_matches`, all raising
  `ConfigError` — confirming the duplicated invalid-clause copy the spec
  flags for Phase C (direct-run).
- `ontos/commands/log.py:115` — `logs_dir = …resolve()` follows symlinks
  (the X-M1 defect); `:336-340` — `output_path.open("x")` exclusive create
  without anchored no-follow parent pin (direct-run).
- `scripts/validate-audit-remediation-registry.py:244` —
  `original = {row["id"]: row …}` indexes `row["id"]` directly, so a finding
  row missing `id` raises an uncaught `KeyError` before the
  collected `missing fields` error reaches the user (the X-M2 defect)
  (direct-run).
- All seven test anchors cited in §§6/11 exist at `b6f89d7`:
  `tests/test_frontmatter_roundtrip_regression.py`,
  `tests/test_document_loading_contract_a1.py`,
  `tests/test_session_context.py`, `tests/commands/test_log.py`,
  `tests/mcp/test_read_only_registration.py`,
  `tests/test_cli_contract_v4.py`, `tests/mcp/test_locking.py`
  (direct-run: `git show b6f89d7:<file>` + line count).

No completeness gaps found. The B.1 incorporation note (§1) converts
Claude adversarial findings X-M1 (symlinked `logs_dir`) and X-M2 (missing
`id`) into explicit Phase C requirements with current-defect citations,
both of which I reproduced at the cited lines.

## 2. Diagram-prose cross-reference

### 10.1 Architecture / Component Diagram

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| A — Audit Registry | §4.1 | §4.1 registry CREATE | Yes |
| V — Validator / Control Plane | §4.1 | §4.1 validator + control plane | Yes |
| L — O4 Ledger + O5 Leases | §1, §4.1 | §4.1 lease integrity | Yes |
| S — Canonical Loader + Serializer | §4.2 | §4.2 serializer | Yes |
| W — Safe Writer + CLI Logging | §4.3 | §4.3 writer + log | Yes |
| C — CLI / MCP Contracts | §4.4 | §4.4 CLI/MCP/activation/doctor | Yes |
| X — Activation + Doctor | §4.4 | §4.4 required_version + doctor | Yes |
| K — Cross-platform Locking | §4.4 | §4.4 CREATE locking.py | Yes |
| P — Release Pipeline | §4.5 | §4.5 CI + publish | Yes |
| T — Tests + Lifecycle Evidence | §6, §4.5 | §6 test strategy + §11 matrix | Yes |
| M — Generated Context Map + AGENTS | §4.5 | §4.5 context-map generation | Yes |
| G — EXTERNAL: GitHub | §3, §4.1 | §3 dependency + parity | Yes |
| R — EXTERNAL: Windows Runner | §3, §6, §8 | §3 dependency + §3 external blocker | Yes |
| Y — EXTERNAL: TestPyPI / PyPI | §3, §4.5 | §3 dependency + §4.5 publish | Yes |

All 14 diagram components appear in prose; all prose components appear in
the diagram. Edges (`A → S`, `A → C`, `K → W`, dashed `G/R/Y →` external
parity/platform/artifact-proof labels) match the dependency relationships in
§§3–4. External nodes are dashed with a distinct `external` class — an honest
representation of boundaries local review cannot certify.

### 10.2 Lifecycle State Machine

The state machine models the code-first lifecycle faithfully: `I0_Frozen →
Phase_A_Spec → B1 → B2_CodeFirst_Review → D1 → D2 → D3_Verdict`, with `D4`
rerun-from-D.5 and loose-falsification loops, and an explicit
`D6_Pending` stop boundary labeled "no release claim." This matches §2
("mandatory code-first B.2 review and independent D.5 verification") and
§1's branch-level-not-release framing.

No blocking diagram-prose mismatches found.

## 3. Quality assessment

The spec is a well-engineered code-first integration document. Its strongest
quality is evidence discipline: every factual claim in §4 carries a
`direct-read` citation with a file:line range at the frozen I0 commit
`b6f89d7`, and I independently verified each load-bearing range. The
registry cardinality (91 originals + 9 R2-* = 100; 41 `confirmed_open`; 7
partial) matches exactly. The validator's hardcoded original-severity totals
(P0=1/P1=27/P2=63) and origin split (fable_audit/codex_revalidation) line up
with the registry contents. The §11 Contract/Invariant-to-Evidence Matrix
maps 11 invariants to both an implementation anchor and a test anchor, with
honest evidence labels — `direct-run` for locally verifiable items, `local
direct-run; external pending` for wheel provenance, and `local direct-run
/static-inspection; Windows external pending` for cross-platform locking.

The concurrency envelope ("single-operator-crash-safe") is scoped honestly:
the writer serializes cooperative writers via advisory locks and attempts
rollback, but the spec states plainly it does not claim a distributed
transaction or immunity to process death at every instruction; durable crash
recovery is named as one of seven partial areas. The §12 Helper-Divergence
table distinguishes "extend internals" from "diverge with registry substrate"
and honestly labels registrar-boilerplate removal as partial ("full
registrar removal remains partial and is not claimed").

The spec distinguishes branch-level integration evidence from
per-issue/release certification across four independent touchpoints with no
contradiction: §1 ("this deliverable itself is a branch-level lifecycle
review, not a release"), §2 out-of-scope ("certifying any child issue
lifecycle, or treating this umbrella review as #146/#147 per-issue
certification"; "D.6 final approval, tagging, publishing, merging"),
§5 ("Does umbrella D.5 certify child issues? No; require each child
manifest's own strict receipts"), and §9 ("Do not claim per-issue strict-P3
certification, D.6 approval, merge, tag, publication, or release readiness
from this deliverable"). External Windows and TestPyPI evidence is honest
throughout: §3 ("No dependency may be converted into a synthetic receipt"),
§8 listing both as P1 risks with CI-based mitigations requiring real runners,
and §11 labeling both `external pending`. No synthetic receipts are claimed.

## 4. UX review

The spec is reader-friendly: the §5 Open Questions table communicates
decisions without burying them; the §9 Exclusion List is scannable;
error-code naming (`E_LOG_EXISTS`, `E_ACTIVATION_UNUSABLE`, `E_USER_INPUT`)
is user-visible and matches the implementation I inspected. The §7 Migration
section frames all user-visible changes as intentional and pairs each change
with where it surfaces (loader `parse_error`, CLI `E_USER_INPUT`, schema
`4.0`, exit taxonomy). The §8 Risk Assessment table pairs each P0/P1 risk
with an observable signal, making it actionable for monitoring.

The rollback guidance in §7 is clear and implementable: revert I0 as one
integration unit, then regenerate map and agent metadata from the reverted
clean snapshot — with explicit prohibitions against selective rollback that
would break paired consumers (serializer without its consumers, writer
without its tests, release provenance without its artifact checker). A
Phase C author can follow this without follow-up questions.

## 5. Issues found

### Blocking (Critical)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | None found. | — | — | — | — |

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | None found. | — | — | — | — |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | §7 Migration references "schema `4.0`" and "the public exit taxonomy" for CLI JSON/exit semantics without cross-referencing the §4.4 citation to `ontos/ui/json_output.py:16-49,202-345,414-472`. A documentation author writing `docs/reference/Migration_v3_to_v4.md` would need to search for the canonical schema location. §4.4 has the citation; §7 just does not point back to it. | spec §7 | static-inspection | `git show b6f89d7:ontos/ui/json_output.py` confirms the schema-v4 envelope and exit-taxonomy enums at the §4.4-cited range. | Add a parenthetical in §7 pointing to the §4.4 anchor: "CLI JSON/exit semantics follow the schema-v4 envelope in `ontos/ui/json_output.py` (§4.4)." |
| P-2 | §4.4 cites `ontos/core/config.py:239-266,279-345` for "duplicated invalid-clause copy" but does not pinpoint which specific branches within the 66-line span contain the redundant copy. The duplication is real (`version_satisfies_requirement` raises `ConfigError("ontos.required_version must be a valid semver range…")` while `_version_clause_matches` / `_wildcard_clause_matches` raise multiple `ConfigError("invalid version clause…")` variants), but a Phase C author must read the whole span to locate the exact messages to unify. | spec §4.4 | static-inspection | `git show b6f89d7:ontos/core/config.py` shows the distinct ConfigError messages in both cited ranges. | Optionally narrow the citation or add a one-line note naming the two messages a Phase C author must collapse into one actionable diagnostics path. |

## 6. Positive observations

- **Direct-read accuracy is excellent.** Every file:line citation verified
  against the frozen I0 commit `b6f89d7` matches the described content.
  This sets a high bar for B.2 reviewers and proves the spec is code-first,
  not aspirational.
- **Registry cardinality is exactly right.** 91 originals (P0=1/P1=27/P2=63)
  + 9 R2-* = 100; 41 `confirmed_open`; 7 partial. The evidence baseline is
  trustworthy, and the validator pins the same totals it asserts.
- **External evidence honesty is consistent.** Windows and TestPyPI are
  labeled external blockers in §3, §6, §8, and §11. The §3 sentence "No
  dependency may be converted into a synthetic receipt" is the right
  guardrail for D.5.
- **Branch-level vs per-issue/release distinction is unambiguous**, stated
  in §1, enforced in §2, resolved in §5, and reinforced in §9 — four
  independent touchpoints with no contradiction.
- **The §11 Contract Matrix** maps 11 invariants to concrete implementation
  and test anchors with honest evidence labels, including `external pending`
  where local proof cannot substitute for external runners.
- **The §12 Helper-Divergence table** correctly distinguishes "extend" from
  "diverge" and honestly labels registrar-boilerplate removal as partial.
- **The §10.2 lifecycle state machine** correctly models the code-first B.2,
  loose-falsification charter, and D.5→D.4 reroll paths, with an explicit
  D.6 stop boundary labeled "no release claim."
- **X-M1/X-M2 incorporation** converts adversarial findings into actionable
  Phase C requirements with current-defect citations (log.py:115;
  validate script:244) that I reproduced immediately.

## Verdict

Approve

The spec is well-designed, complete, clear, implementable, and honest.
All direct-read citations verify against the frozen I0 commit `b6f89d7`
(parent `bf91b42`); the registry cardinality (91 originals + 9 R2-* = 100;
41 `confirmed_open`; 7 partial) is exactly as claimed and matches the
validator's pinned totals; both diagrams match their prose counterparts;
and the test strategy is grounded in real test files at I0. The spec
distinguishes branch-level integration evidence from per-issue/release
certification across four sections (§1, §2, §5, §9) with no contradiction,
and external Windows/TestPyPI evidence is honestly labeled as
pending/blocking throughout (§3, §8, §11) — no synthetic receipts. The two
minor findings are a cross-reference back-pointer and a citation-precision
nit, neither a design defect; they do not block B.2 or downstream phases
and can be resolved in a B.2 spec update.

## 8. Notes

File-existence attestation (per Template 03 v1.3+):

```
git branch --show-current → codex/audit-rebaseline-remediation-lifecycle
git ls-files docs/specs/project-ontos-audit-rebaseline-remediation-spec.md → tracked
git ls-files manifests/project-ontos-audit-remediation-registry.yaml       → tracked
git ls-files scripts/validate-audit-remediation-registry.py                 → tracked
```

Frozen I0 commit `b6f89d7` ("Implement audit rebaseline remediation"; 188
files changed, +9520/-4356) confirmed with parent `bf91b42`. The immutable
SHA pair in spec §1 matches. (Per dispatch instruction, commit identities
are referred to by these short forms only.)

Rule-reachability audit: no gaps found. The registry validator's external
GitHub-parity path (`validate(require_external_parity)`) is locally reachable
by running the script and externally reachable via the parity mode. The
X-M1 symlink-defect fix has a citable test trigger (symlinked `logs_dir`
plus an outside-workspace sentinel that must remain unchanged). The X-M2
missing-`id` defect has a citable trigger (inject a finding row without
`id` → must yield the collected `missing fields` error and non-zero exit,
not an uncaught `KeyError` at validate script:244). Every §11 matrix row
maps to a concrete validator/test input.

Test-blessed divergence audit: skipped — Phase B, no Phase-C code to audit
(per Template 03 § "Test-blessed divergence audit").

Evidence labels: `direct-run` for the `git show`/YAML-parse verifications I
executed this session; `static-inspection` for prose/diagram and
cross-reference reasoning. Blocking findings would require `direct-run`,
but none were found.

Workers write, orchestrator commits: no `git commit` executed per Template
01 commit-split-by-role (v1.3+). Artifacts written to the declared paths only
(the destination guard file and this sibling review); no other files
modified.
