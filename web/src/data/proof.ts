/**
 * B4 — the ten-stage proof lineage over the engagement artifacts.
 *
 * UI01's chain is commitment → requirement → claim → population → sources →
 * reconciliation → contract → snapshot → assertion → verdict, with typed
 * arrows. "Requirement" names the compiled-into relationship between a
 * commitment and the claims that cite it, not a standalone ontology object
 * (Q16 ruling, issue #100, docs/DECISIONS.md D-Q16) — PRD-v3 has no defining
 * prose for a `Requirement` model, and none is needed for the stage to
 * render honestly. Only part of the chain exists on the wire today, and
 * this module is honest about which part: every stage resolves to a
 * `StageEvidence` whose kind says whether the stage is emitted,
 * identity-only, trace-only, or not emitted at all (README Q14–Q16).
 * Rendering a missing stage as if it were backed by data would be exactly
 * the misrepresentation the registry page refuses for DRAFT entries.
 *
 * House discipline: artifacts are passed explicitly, so the falsifier
 * probes bite; the stage table and evidence kinds are exhaustive Records,
 * so an eleventh stage or a new kind fails `tsc` rather than silently not
 * rendering (the B2 STALE lesson, L-056).
 */

import {
  derivationBasis,
  openBlockers,
  reconciledClaimHolds,
} from "@/data/reconciliation";
import type {
  CommitmentsArtifact,
  ContractsArtifact,
  ManifestSnapshotArtifact,
  PoisonVerdictGroup,
  PoisonsArtifact,
  ReconciliationReport,
  VerdictRecord,
} from "@/data/types";

/* ------------------------------------------------------------------ */
/* Stages                                                              */
/* ------------------------------------------------------------------ */

export type LineageStageId =
  | "commitment"
  | "requirement"
  | "claim"
  | "population"
  | "sources"
  | "reconciliation"
  | "contract"
  | "snapshot"
  | "assertion"
  | "verdict";

export interface LineageStageMeta {
  id: LineageStageId;
  /** 1-based position in the chain. */
  ordinal: number;
  title: string;
  /** The typed-arrow label INTO the next stage; null on the last. */
  arrowToNext: string | null;
}

/**
 * Exhaustive by construction: an eleventh `LineageStageId` member fails
 * `tsc` here rather than silently truncating the chain.
 */
export const LINEAGE_STAGES: Record<LineageStageId, LineageStageMeta> = {
  commitment: { id: "commitment", ordinal: 1, title: "Commitment", arrowToNext: "imposes" },
  requirement: { id: "requirement", ordinal: 2, title: "Requirement", arrowToNext: "compiled into" },
  claim: { id: "claim", ordinal: 3, title: "Claim", arrowToNext: "quantifies over" },
  population: { id: "population", ordinal: 4, title: "Population", arrowToNext: "derived from" },
  sources: { id: "sources", ordinal: 5, title: "Sources", arrowToNext: "reconciled into" },
  reconciliation: {
    id: "reconciliation",
    ordinal: 6,
    title: "Reconciliation",
    arrowToNext: "evidence gated by",
  },
  contract: { id: "contract", ordinal: 7, title: "Contract (EQC)", arrowToNext: "frozen in" },
  snapshot: { id: "snapshot", ordinal: 8, title: "Snapshot", arrowToNext: "executes" },
  assertion: { id: "assertion", ordinal: 9, title: "Assertion", arrowToNext: "evaluates to" },
  verdict: { id: "verdict", ordinal: 10, title: "Verdict", arrowToNext: null },
};

/** The ten stages in UI01 order. The `Record` lookup keeps this list
 * honest: a stage named here but absent from LINEAGE_STAGES (or vice versa
 * via the length check) fails at compile or render time, never silently. */
export const STAGE_ORDER: readonly LineageStageId[] = [
  "commitment",
  "requirement",
  "claim",
  "population",
  "sources",
  "reconciliation",
  "contract",
  "snapshot",
  "assertion",
  "verdict",
];

/* ------------------------------------------------------------------ */
/* Evidence                                                            */
/* ------------------------------------------------------------------ */

/** One key/value line in a stage's inspector payload. */
export interface EvidenceField {
  label: string;
  value: string;
  /** Mono rendering for refs/hashes. */
  mono?: boolean;
  /** Marks a count as a diagnostic, never evidence (HANDOFF §2). */
  diagnostic?: boolean;
}

export type StageEvidence =
  | {
      /** The stage is real on the wire — fields read straight from data. */
      kind: "emitted";
      fields: EvidenceField[];
    }
  | {
      /** Only an identity travels: something names the stage, its content
       * does not (the EQC via `spec_hash` == `contract_hash`). */
      kind: "identity-only";
      fields: EvidenceField[];
      note: string;
    }
  | {
      /** A trace exists in another artifact's prose or grouping, inferred
       * rather than carried as a field. */
      kind: "trace-only";
      fields: EvidenceField[];
      note: string;
    }
  | {
      /** Nothing on the wire at all. */
      kind: "not-emitted";
      note: string;
    };

export interface LineageNode {
  meta: LineageStageMeta;
  evidence: StageEvidence;
}

/** Short on-diagram wording per evidence kind — text-first, never
 * colour-alone. Exhaustive: a new kind fails tsc here. */
export const EVIDENCE_KIND_LABEL: Record<StageEvidence["kind"], string> = {
  emitted: "emitted",
  "identity-only": "identity only",
  "trace-only": "trace only",
  "not-emitted": "not yet emitted",
};

/* ------------------------------------------------------------------ */
/* Assertion-family inference (Q4b)                                    */
/* ------------------------------------------------------------------ */

export const POISON_GROUPS: readonly PoisonVerdictGroup[] = [
  "EXISTENCE",
  "NON-EXISTENCE",
  "TIMING",
];

/** Which verdict_records family carries this record, if any. */
export function assertionFamilyOf(
  poisons: PoisonsArtifact,
  recordId: string,
): PoisonVerdictGroup | null {
  for (const group of POISON_GROUPS) {
    if (poisons.verdict_records[group].some((r) => r.record_id === recordId)) {
      return group;
    }
  }
  return null;
}

/* ------------------------------------------------------------------ */
/* The lineage                                                         */
/* ------------------------------------------------------------------ */

/**
 * Resolve every stage's evidence for one verdict record. Pure; artifacts
 * are inputs. A failed population join renders as a visible evidence state,
 * never a throw — the proof view's job is to show what the wire supports,
 * including "nothing".
 */
export function lineage(
  record: VerdictRecord,
  reconciliations: readonly ReconciliationReport[],
  poisons: PoisonsArtifact,
  contracts: ContractsArtifact = {},
  snapshot: ManifestSnapshotArtifact | null = null,
  commitments: CommitmentsArtifact = {},
): LineageNode[] {
  const report =
    reconciliations.find((r) => r.population_id === record.population_id) ?? null;
  const family = assertionFamilyOf(poisons, record.record_id);

  const evidenceFor = (id: LineageStageId): StageEvidence => {
    switch (id) {
      case "commitment": {
        const commitment = Object.values(commitments).find((c) =>
          c.claim_ids.includes(record.claim_id),
        );
        if (!commitment) {
          return {
            kind: "not-emitted",
            note: `No commitment cites ${record.claim_id} (Q16, issue #97) — commitments.json only covers claims built inside build_poison_artifacts().`,
          };
        }
        return {
          kind: "emitted",
          fields: [
            { label: "name", value: commitment.name },
            { label: "source", value: commitment.source },
            { label: "obligation", value: commitment.obligation },
            { label: "claim_ids", value: commitment.claim_ids.join(", "), mono: true },
          ],
        };
      }
      case "requirement": {
        // Q16 ruling (issue #100, docs/DECISIONS.md D-Q16): Requirement is
        // not a distinct ontology object in V1 — the "compiled into" arrow
        // is Commitment.claim_ids tracing which claims cite this
        // Commitment's framework_ref (Claim.framework_refs). Same lookup as
        // the commitment stage above; trace-only, no new field on the wire.
        const commitment = Object.values(commitments).find((c) =>
          c.claim_ids.includes(record.claim_id),
        );
        if (!commitment) {
          return {
            kind: "not-emitted",
            note: "No commitment cites this claim (see the commitment stage above), so there is nothing to trace a compiled-into relationship from.",
          };
        }
        return {
          kind: "trace-only",
          fields: [
            { label: "framework_ref", value: commitment.name, mono: true },
            { label: "claim_ids", value: commitment.claim_ids.join(", "), mono: true },
          ],
          note: "Requirement is not a standalone modeled object (Q16, issue #100, docs/DECISIONS.md D-Q16); this is Commitment.claim_ids tracing which claims (Claim.framework_refs) compile from this commitment's obligation, inferred rather than carried as its own field.",
        };
      }
      case "claim":
        return {
          kind: "emitted",
          fields: [{ label: "claim_id", value: record.claim_id, mono: true }],
        };
      case "population": {
        if (!report) {
          return {
            kind: "trace-only",
            fields: [
              { label: "population_id", value: record.population_id, mono: true },
              {
                label: "population_count",
                value: String(record.population_count),
                diagnostic: true,
              },
            ],
            note: `No reconciliation report on the wire for ${record.population_id} — the population is named by the record but not resolvable.`,
          };
        }
        return {
          kind: "emitted",
          fields: [
            { label: "name", value: report.population_name },
            { label: "type", value: report.population_type },
            { label: "definition", value: report.definition },
            {
              label: "ladder",
              value: `${report.ladder.at_first_verdict} at first verdict → ${report.ladder.after_dispositions} after dispositions`,
            },
            {
              label: "members",
              value: `${report.canonical_members.length} canonical (record says ${record.population_count})`,
              diagnostic: true,
            },
          ],
        };
      }
      case "sources": {
        if (!report) {
          return {
            kind: "not-emitted",
            note: "Sources travel inside the reconciliation report, which did not resolve for this population.",
          };
        }
        const basis = derivationBasis(report);
        return {
          kind: "emitted",
          fields: [
            { label: "derivation basis", value: basis.description },
            ...report.sources.map((s) => ({
              label: s.role,
              value: `${s.name} (${s.members.length} members)`,
              diagnostic: true,
            })),
          ],
        };
      }
      case "reconciliation": {
        if (!report) {
          return {
            kind: "not-emitted",
            note: "No reconciliation report resolved for this population.",
          };
        }
        const blockers = openBlockers(report);
        const holds = reconciledClaimHolds(report);
        return {
          kind: "emitted",
          fields: [
            {
              label: "blockers",
              value:
                blockers.length === 0
                  ? "no deltas blocked the ladder"
                  : `${blockers.filter((b) => b.answer !== null).length} of ${blockers.length} answered by a named human`,
            },
            {
              label: "RECONCILED claim",
              value: holds
                ? "supported by the dispositions"
                : "CONTRADICTED — an open delta has no disposition",
            },
            {
              label: "completeness_ref (on the record)",
              value: record.completeness_ref,
              mono: true,
            },
          ],
        };
      }
      case "contract": {
        const contract = contracts[record.spec_hash];
        if (!contract) {
          return {
            kind: "identity-only",
            fields: [
              { label: "spec_id", value: record.spec_id, mono: true },
              { label: "spec_hash", value: record.spec_hash, mono: true },
            ],
            note: "No emitted contract resolves for this spec_hash — only the identity travels (Q14).",
          };
        }
        return {
          kind: "emitted",
          fields: [
            { label: "spec_id", value: record.spec_id, mono: true },
            { label: "contract_hash", value: contract.contract_hash, mono: true },
            { label: "source", value: `${contract.source} (${contract.tenant})` },
            {
              label: "supported_assertion_types",
              value: contract.supported_assertion_types.join(", "),
              mono: true,
            },
            { label: "provenance", value: contract.quality.provenance.method },
            { label: "integrity", value: contract.quality.integrity.method },
            { label: "population", value: contract.quality.population.method },
            { label: "semantics", value: contract.quality.semantics.method },
            { label: "temporal_validity", value: contract.quality.temporal_validity.method },
          ],
        };
      }
      case "snapshot": {
        if (snapshot === null || !snapshot.blocks.populations.includes(record.population_id)) {
          return {
            kind: "not-emitted",
            note: `No manifest snapshot is emitted for ${record.population_id} (Q16). Nearest wire trace: schema ${record.schema_version}, source ${record.source_version}, test fn ${record.test_function_version} live on the record itself, not in a ratified snapshot.`,
          };
        }
        return {
          kind: "emitted",
          fields: [
            { label: "version", value: String(snapshot.version) },
            { label: "lifecycle", value: snapshot.lifecycle },
            // The DEMO-ONLY caveat travels inside this string itself
            // (web/README.md) — the strict schema has no sibling note field.
            { label: "ratified_by", value: snapshot.ratified_by ?? "(none)" },
            { label: "ratified_at", value: snapshot.ratified_at ?? "(none)", mono: true },
            {
              label: "populations frozen",
              value: snapshot.blocks.populations.join(", "),
              mono: true,
            },
            { label: "claims frozen", value: snapshot.blocks.claims.join(", "), mono: true },
            {
              label: "capabilities in scope",
              value: `${snapshot.blocks.capabilities.length} entries`,
              diagnostic: true,
            },
            {
              label: "collectors granted",
              value: snapshot.blocks.collectors.map((c) => c.id).join(", "),
              mono: true,
            },
          ],
        };
      }
      case "assertion": {
        const fields: EvidenceField[] = [
          { label: "assertion_id", value: record.assertion_id, mono: true },
        ];
        if (family !== null) {
          fields.push({
            label: "poisons group",
            value: family,
            mono: true,
            diagnostic: true,
          });
        }
        fields.push({ label: "message", value: record.message ?? "(no message on the record)" });
        return { kind: "emitted", fields };
      }
      case "verdict":
        return {
          kind: "emitted",
          fields: [
            { label: "status", value: record.status },
            { label: "record_id", value: record.record_id, mono: true },
            { label: "record_hash", value: record.record_hash, mono: true },
            {
              label: "chain_prev",
              value: record.chain_prev ?? "none — first in chain",
              mono: true,
            },
          ],
        };
      default: {
        const exhaustive: never = id;
        return exhaustive;
      }
    }
  };

  return STAGE_ORDER.map((id) => ({
    meta: LINEAGE_STAGES[id],
    evidence: evidenceFor(id),
  }));
}
