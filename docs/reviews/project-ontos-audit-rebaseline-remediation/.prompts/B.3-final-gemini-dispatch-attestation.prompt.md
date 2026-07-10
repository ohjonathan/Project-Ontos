You are the independent non-orchestrator verifier for the B.3 canonical
consolidation of `project-ontos-audit-rebaseline-remediation`.

Work read-only in the current repository. Do not edit any file. Independently
run these two commands exactly, preserving combined stdout/stderr for each:

```bash
bash .llm-dev/framework/scripts/verify-family-dispatch.sh --require-complete --intent docs/reviews/project-ontos-audit-rebaseline-remediation/B.1-final-dispatch-intent.yaml --result docs/reviews/project-ontos-audit-rebaseline-remediation/B.1-final-dispatch-result.yaml --adopter-root "$PWD" --manifest manifests/project-ontos-audit-rebaseline-remediation.yaml
bash .llm-dev/framework/scripts/verify-family-dispatch.sh --require-complete --intent docs/reviews/project-ontos-audit-rebaseline-remediation/B.2-final-dispatch-intent.yaml --result docs/reviews/project-ontos-audit-rebaseline-remediation/B.2-final-dispatch-result.yaml --adopter-root "$PWD" --manifest manifests/project-ontos-audit-rebaseline-remediation.yaml
```

For each command, compute SHA-256 over the exact combined output bytes. Return
one terse final line in this exact shape:

`ATTEST PASS B.1=<sha256> B.2=<sha256>`

Return `ATTEST FAIL ...` instead if either command exits nonzero or is not 4/4
complete. Do not trust or repeat hashes from existing B.3 artifacts; derive them
from your own executions.
