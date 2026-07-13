# Ontos 5.0.0 lifecycle rerun receipt

- Product head: `5678e910ce11ed7a3546822cf3e34d50c5741681`.
- Framework: llm-dev v2.0.1 (`8baacbdbbcf14fa448bf4fe56dc5a64229ceb580`).
- Canary: the exact Claude Code 2.1.207 / Opus / bypass-permissions route
  produced a genuine worker file. The first canary correctly failed F35 shape;
  the tightened second canary passed lint and complete family verification.
- B.1 GLM peer: two genuine attested Neuralwatt/OpenCode runs completed with
  `Approve`. The first exposed a v2.0.1 incompatibility: the scaffolded schema-4
  inventory is accepted by the lifecycle verifier but rejected by the receipt
  appender. The inventory was normalized to the verifier-documented adopter
  schema 2 and a second real dispatch appended the receipt.
- B.1 Claude adversarial: the canary-proven route completed, appended a genuine
  receipt, and returned `Request changes` with independently reproducible
  product blockers. Exit 0 can emit `result.exit_category: findings`, and graph
  path lookup unconditionally casefolds despite the filesystem-sensitive spec.
- Halt: no Gemini/product B.1 seats and no B.2/D phases were dispatched after a
  blocking verdict. Continuing would spend providers against a head that cannot
  be certified and would not make the current product head releasable.
- Strict family verification: exit 1. Besides the intentionally pending seats,
  v2.0.1 rejects the GLM receipt because its own wrapper recorded
  `artifact_source: worker_file` for an attested OpenCode route.
- Strict lifecycle verification: exit 1 with 10 issues and
  `status=review_pending`.
- Provider-limited verification: exit 1 with 11 issues and
  `status=provider_limited_fallback_incomplete`; no exception or fallback
  receipt was invented.
- Disposition: strict P3 is not certified and D.6 remains `WITHHELD`. Correct
  the product blockers on a new head, repair/route around the framework
  wrapper-verifier mismatch without weakening evidence, and restart lifecycle.
