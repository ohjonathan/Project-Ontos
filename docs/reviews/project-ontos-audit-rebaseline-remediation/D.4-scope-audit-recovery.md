---
id: audit-rb-D4-scope-audit-recovery
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.4
role: scope-audit-recovery
family: codex
status: completed
---

# D.4 Scope-Audit Recovery

## Gate failure

The first post-fix invocation of the framework changed-path verifier failed on
exactly one path:

```text
ontos/commands/rename.py (matches no scope.allowed_paths / scope.allowed_path_patterns)
```

Evidence: `direct-run` —
`verify-changed-path-scope.sh --manifest manifests/project-ontos-audit-rebaseline-remediation.yaml --base bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`
returned nonzero after the CAN-ID-1 code commit.

## Authority and adjudication

- Approved spec §4.2 requires every CLI-supplied ID to use the canonical
  validator and places CLI mutation commands in the governed MODIFY surface.
- Strict D.2 Claude Peer P-1 identifies `ontos/commands/rename.py` as the
  concrete divergent consumer.
- Canonical D.3 CAN-ID-1 requires deleting that file's duplicate ID regex and
  validating both operands before the same-ID short circuit.
- Spec §9 does not exclude the path, and the manifest does not forbid it.
- An independent read-only scope adjudication confirmed that all other D.4
  changed paths were already allowlisted.

Disposition: **manifest omission; no spec deviation**. Add exactly
`ontos/commands/rename.py` to `scope.allowed_paths`. Do not add a directory
pattern or widen any other lease.

## Sequencing incident and recovery

The CAN-ID-1 code commit `311b60b` landed before this omission was detected.
That history is preserved without amendment, receipt editing, or reconstruction.
The orchestrator records this recovery, updates the exact manifest path, and
reruns changed-path scope plus manifest conformance before D.5.

## Nonclaims

This recovery does not change the approved behavioral contract, add a new
product surface, certify D.4/D.5, authorize D.6, or widen any child-deliverable
lease.
