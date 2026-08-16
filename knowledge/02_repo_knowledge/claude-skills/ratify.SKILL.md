---
name: ratify
description: Ratification workflow for baselines, collection specs, approver rosters, and JIT allowlists (F-4 discipline - human-ratified hash, agent may draft but never ratify). Use when the user says "ratify", "freeze this spec", "approve this baseline", or when a draft spec/baseline needs to take effect.
---

# Ratify an artifact

Human-ratified is not human-originated: you (the agent) may draft any judgment artifact, but it takes effect only when the Owner ratifies its hash. This skill prepares the ratification; the Owner performs step 4 himself. If you find yourself executing step 4, stop — that is the exact leak the architecture exists to prevent.

## Procedure

1. **Canonicalize and hash.** Serialize the artifact with `src.evidence.canonical_json` (sorted keys, no whitespace drift) and compute SHA-256 via `src.evidence.sha256_hex`. Print the hash and the artifact side by side.
2. **Diff against the currently ratified version** (if any): show exactly what changes, field by field. A ratification request without a readable diff is not reviewable.
3. **State the consequence in one paragraph:** what the system will start/stop flagging under this artifact. E.g. "lowering required_approving_review_count to 1 means single-review merges stop FAILing CC8.1 across 9 repos."
4. **the Owner ratifies** — he runs the insert as the human path (not the app role):
   `INSERT INTO ratifications (artifact_kind, artifact_id, artifact_hash, ratified_by) VALUES (...)` — and for specs, flips `status` to `ratified` with the `ratification` block filled (`ratified_hash` must equal `spec_hash`; the schema rejects frozen specs without it).
5. **Verify the gate.** Run the run-start assertion (`src.db.assert_baseline_ratified`) against the new hash and confirm the previous hash's records remain intact in the ledger (supersession, never mutation).
6. **Record the decision.** If the artifact embodies a judgment change (tolerance semantics, approver definition, authoritative source, scope-out), append a dated entry to the corpus Decision Ledger (`~/PycharmProjects/aegis-corpus/02_design_decisions/Decision_Ledger.md`) with rationale and alternatives, and re-export the corpus manifest.

## Reminders

- Unratified edits do not "warn" — they fail the run. That is intended; do not soften it.
- The ratification table is append-only in practice: a mistaken ratification is superseded by a new one, never deleted.
- NOT_APPLICABLE verdicts require a ratification ref. Scoping a control out is a ratifiable judgment, not a code comment.
