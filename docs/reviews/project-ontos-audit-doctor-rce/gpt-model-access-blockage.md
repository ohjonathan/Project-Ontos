---
id: project-ontos-audit-doctor-rce-gpt-model-access-blockage
type: review
status: active
deliverable_id: project-ontos-audit-doctor-rce
phase: B.1
role: dispatch-blockage-evidence
family: codex
---

# GPT-Family Dispatch Blockage Evidence

Observed on 2026-07-03 while preparing strict-P3 B.1 dispatch for `project-ontos-audit-doctor-rce`.

The framework routes `family: gpt` through the Codex CLI substrate with a literal `gpt-*` model. The local `codex` CLI is present, but the account rejects every probed `gpt-*` model.

Command shape used:

```bash
codex exec --dangerously-bypass-approvals-and-sandbox --sandbox read-only --skip-git-repo-check --model "$MODEL" 'Respond with exactly: ok'
```

Rejected model IDs:

- `gpt-5`
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-5-codex`
- `gpt-4.1`
- `gpt-4.1-mini`
- `gpt-4.1-nano`
- `gpt-4o-mini`

Representative stderr:

```text
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error","message":"The 'gpt-5' model is not supported when using Codex with a ChatGPT account."}}
```

This blocks strict-P3 `gpt` family dispatch for B.1, D.2, and D.5 unless the maintainer supplies a working `gpt-*` model or authorizes `provider-limited-review-exception`.
