/* Engagement-artifact loader with lightweight runtime guards.
 *
 * The JSON under src/data/engagement/ is the REAL pipeline output,
 * synced verbatim from artifacts/demo-engagement/ by
 * scripts/sync-artifacts.mjs (committed should always equal synced —
 * `npm run build`'s prebuild hook re-runs it locally; see that script's
 * own header for the current lack of a CI-side diff check). Six of
 * the seven files (reconciliation, registry, verdicts, snapshot,
 * commitments, contracts) are read directly; `populations` and
 * `proof_graphs` have no producer on the backend at all (issue #162) —
 * they are DERIVED here, at load time, from the other six. No file
 * stands in for either: a committed stand-in would be exactly the
 * silent-staleness failure mode this codebase's evidence-integrity
 * discipline (mutation harness, verify.sh full's no-silent-partial-
 * population rule) exists to catch elsewhere.
 *
 * The guards check enum membership and required keys, on the RAW files,
 * against the mirrored ontology, so that artifact drift (backend renames
 * a field, adds an enum value…) surfaces as a visible red "artifact
 * schema drift" banner — never a crash, never a silent mis-render.
 * `populations`/`proof_graphs` are not separately guarded: they are pure
 * functions of the six checked files, so their shape cannot drift
 * independently of an already-flagged input.
 *
 * Derivation source of truth (per field, for the next backend rename):
 * - Population: reconciliation.json's own population_* fields + ladder
 *   (state = ladder.after_dispositions) + buckets (deltas = every
 *   bucket except intersection, per reconcile/engine.py's own
 *   attachment rule) + boundary_exclusions (exclusions).
 * - ProofGraph: one graph per verdict record, joining
 *   commitments.json (claim_ids → commitment/requirement stage),
 *   reconciliation.json (population/source/reconciliation stages),
 *   contracts.json (contract stage, keyed by spec_hash), snapshot.json
 *   (snapshot stage, when the population is in blocks.populations).
 * On mismatch we still return the parseable data.
 */

import reconciliationJson from "@/data/engagement/reconciliation.json";
import registryJson from "@/data/engagement/registry.json";
import verdictsJson from "@/data/engagement/verdicts.json";
import snapshotJson from "@/data/engagement/snapshot.json";
import commitmentsJson from "@/data/engagement/commitments.json";
import contractsJson from "@/data/engagement/contracts.json";

import {
  ASSURANCE_STATES,
  POPULATION_TYPES,
  SOURCE_ROLES,
  UNKNOWN_WHY_CODES,
  VERDICT_STATES,
} from "@/lib/types/ontology";
import type { Delta, EvidenceQualityContract, Population } from "@/lib/types/ontology";
import {
  ACCESS_MODES,
  DELTA_BUCKETS,
  PAGINATION_METHODS,
  TEMPORAL_KINDS,
} from "@/lib/types/artifacts";
import type {
  Commitment,
  CommitmentsFile,
  DeltaBucket,
  EngagementArtifacts,
  ManifestSnapshot,
  ProofEdge,
  ProofGraph,
  ProofNode,
  ReconciliationReport,
  RegistryFile,
  VerdictRecord,
} from "@/lib/types/artifacts";

export interface EngagementLoad {
  artifacts: EngagementArtifacts;
  /** Human-readable drift findings; non-empty ⇒ render the drift banner. */
  drift: string[];
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function requireKeys(
  obj: unknown,
  keys: string[],
  where: string,
  drift: string[]
): void {
  if (!isRecord(obj)) {
    drift.push(`${where}: expected an object, got ${typeof obj}`);
    return;
  }
  for (const k of keys) {
    if (!(k in obj)) drift.push(`${where}: missing required key "${k}"`);
  }
}

function requireEnum(
  value: unknown,
  allowed: readonly string[],
  where: string,
  drift: string[]
): void {
  if (typeof value !== "string" || !allowed.includes(value)) {
    drift.push(
      `${where}: value ${JSON.stringify(value)} is not in {${allowed.join(" | ")}}`
    );
  }
}

/* ---------------- raw-file guards (the actual drift surface) ---------- */

function checkReconciliationReport(r: unknown, drift: string[]): void {
  const where = "reconciliation";
  requireKeys(
    r,
    [
      "population_id",
      "population_name",
      "population_type",
      "definition",
      "derivation_rule",
      "authoritative_source",
      "period",
      "tenant",
      "sources",
      "canonical_members",
      "buckets",
      "counts",
      "dispositions",
      "ladder",
      "boundary_exclusions",
    ],
    where,
    drift
  );
  if (!isRecord(r)) return;
  requireEnum(r.population_type, POPULATION_TYPES, `${where}.population_type`, drift);
  if (isRecord(r.buckets)) {
    requireKeys(r.buckets, [...DELTA_BUCKETS], `${where}.buckets`, drift);
    for (const bucket of DELTA_BUCKETS) {
      const entries = (r.buckets as Record<string, unknown>)[bucket];
      if (!Array.isArray(entries)) continue;
      entries.forEach((d, i) => {
        const dw = `${where}.buckets.${bucket}[${i}]`;
        requireKeys(d, ["bucket", "member_ref", "owner", "disposition"], dw, drift);
        if (isRecord(d)) requireEnum(d.bucket, DELTA_BUCKETS, `${dw}.bucket`, drift);
      });
    }
  }
  if (isRecord(r.ladder)) {
    requireKeys(
      r.ladder,
      ["at_first_verdict", "after_dispositions", "blocked_by_open_deltas"],
      `${where}.ladder`,
      drift
    );
    if (isRecord(r.ladder)) {
      requireEnum(r.ladder.at_first_verdict, ASSURANCE_STATES, `${where}.ladder.at_first_verdict`, drift);
      requireEnum(
        r.ladder.after_dispositions,
        ASSURANCE_STATES,
        `${where}.ladder.after_dispositions`,
        drift
      );
    }
  }
  if (Array.isArray(r.sources)) {
    r.sources.forEach((s, i) => {
      const sw = `${where}.sources[${i}]`;
      requireKeys(s, ["name", "role", "capability_id", "members"], sw, drift);
      if (isRecord(s)) requireEnum(s.role, SOURCE_ROLES, `${sw}.role`, drift);
    });
  }
}

function checkVerdicts(verdicts: unknown[], drift: string[]): void {
  verdicts.forEach((v, i) => {
    const where = `verdicts[${i}]`;
    requireKeys(
      v,
      [
        "assertion_id",
        "claim_id",
        "control_id",
        "population_id",
        "record_hash",
        "record_id",
        "run_id",
        "spec_hash",
        "spec_id",
        "status",
        "source",
        "source_version",
        "schema_version",
        "test_function_version",
        "collected_at",
        "completeness_ref",
        "evidence_refs",
        "population_count",
        "chain_prev",
      ],
      where,
      drift
    );
    if (!isRecord(v)) return;
    requireEnum(v.status, VERDICT_STATES, `${where}.status`, drift);
    if (typeof v.record_hash !== "string" || v.record_hash.length < 12)
      drift.push(`${where}: record_hash must be a hash string (route identity)`);
    if (v.status === "UNKNOWN") {
      if (v.unknown_cause == null) drift.push(`${where}: UNKNOWN requires unknown_cause`);
      else requireEnum(v.unknown_cause, UNKNOWN_WHY_CODES, `${where}.unknown_cause`, drift);
    }
    if (v.status === "EXCLUDED" && !v.ratification_ref)
      drift.push(`${where}: EXCLUDED requires a ratification_ref`);
    if (v.status === "EXCEPTION" && !v.disposition_ref)
      drift.push(`${where}: EXCEPTION requires a disposition_ref`);
    if (v.status === "FAIL" && !v.message)
      drift.push(`${where}: FAIL requires a message`);
  });
}

function checkCompileErrors(errors: unknown[], drift: string[]): void {
  errors.forEach((e, i) => {
    const where = `registry.compile_errors[${i}]`;
    requireKeys(e, ["code", "claim_id", "message"], where, drift);
  });
}

function checkRegistry(entries: unknown[], drift: string[]): void {
  entries.forEach((e, i) => {
    const where = `registry.entries[${i}]`;
    requireKeys(
      e,
      [
        "id",
        "system",
        "surface",
        "access_modes",
        "populations_yielded",
        "temporal",
        "join_keys",
        "auth_scope",
        "pagination",
        "provenance",
        "rate_limits",
        "ratified_by",
        "lifecycle",
        "history_caveats",
      ],
      where,
      drift
    );
    if (!isRecord(e)) return;
    if (Array.isArray(e.access_modes))
      e.access_modes.forEach((m, j) =>
        requireEnum(m, ACCESS_MODES, `${where}.access_modes[${j}]`, drift)
      );
    if (isRecord(e.temporal))
      requireEnum(e.temporal.kind, TEMPORAL_KINDS, `${where}.temporal.kind`, drift);
    if (isRecord(e.pagination))
      requireEnum(
        e.pagination.method,
        PAGINATION_METHODS,
        `${where}.pagination.method`,
        drift
      );
  });
}

function checkManifest(m: unknown, drift: string[]): void {
  const where = "snapshot";
  requireKeys(m, ["version", "lifecycle", "ratified_by", "ratified_at", "blocks"], where, drift);
  if (!isRecord(m)) return;
  if (isRecord(m.blocks)) {
    requireKeys(
      m.blocks,
      ["boundary", "capabilities", "claims", "collectors", "evidence_contracts", "populations", "tests"],
      `${where}.blocks`,
      drift
    );
  }
}

function checkCommitments(commitments: unknown, drift: string[]): void {
  if (!isRecord(commitments)) {
    drift.push(`commitments: expected an object keyed by id, got ${typeof commitments}`);
    return;
  }
  for (const [key, c] of Object.entries(commitments)) {
    requireKeys(c, ["id", "name", "source", "obligation", "claim_ids"], `commitments.${key}`, drift);
  }
}

function checkContracts(contracts: unknown, drift: string[]): void {
  if (!isRecord(contracts)) {
    drift.push(`contracts: expected an object keyed by contract_hash, got ${typeof contracts}`);
    return;
  }
  for (const [key, c] of Object.entries(contracts)) {
    requireKeys(
      c,
      ["id", "source", "tenant", "population_ref", "endpoint", "contract_hash", "quality"],
      `contracts.${key}`,
      drift
    );
  }
}

/* ---------------- derivation (no data invented — every field traces
 * back to one of the six real files above) ---------------------------- */

function deriveReconciliationReports(): ReconciliationReport[] {
  return [reconciliationJson as unknown as ReconciliationReport];
}

function derivePopulations(reports: ReconciliationReport[]): Population[] {
  return reports.map((r) => {
    const openDeltas: Delta[] = (Object.keys(r.buckets) as DeltaBucket[])
      .filter((bucket) => bucket !== "intersection")
      .flatMap((bucket) => r.buckets[bucket] as unknown as Delta[]);
    return {
      id: r.population_id,
      name: r.population_name,
      type: r.population_type,
      definition: r.definition,
      period: r.period,
      derivation_rule: r.derivation_rule,
      authoritative_source: r.authoritative_source,
      size: r.canonical_members.length,
      exclusions: r.boundary_exclusions.map((b) => b.ref),
      deltas: openDeltas,
      state: r.ladder.after_dispositions,
    };
  });
}

function findCommitment(commitments: CommitmentsFile, claimId: string): Commitment | undefined {
  return Object.values(commitments).find((c) => c.claim_ids.includes(claimId));
}

function buildProofGraph(
  v: VerdictRecord,
  reportsByPopulation: Map<string, ReconciliationReport>,
  contractsByHash: Record<string, EvidenceQualityContract>,
  manifest: ManifestSnapshot,
  commitments: CommitmentsFile
): ProofGraph {
  const nodes: ProofNode[] = [];
  const edges: ProofEdge[] = [];
  const slug = v.record_hash.slice(0, 12);
  const nid = (kind: string, suffix: string) => `${kind}-${slug}-${suffix}`;

  let prevId: string | null = null;
  const addNode = (node: ProofNode, relation: string): void => {
    nodes.push(node);
    if (prevId) edges.push({ from: prevId, to: node.node_id, relation });
    prevId = node.node_id;
  };

  const commitment = findCommitment(commitments, v.claim_id);
  if (commitment) {
    addNode(
      { node_id: nid("commitment", commitment.id), kind: "commitment", label: commitment.name, ref: commitment.id },
      "imposes"
    );
    addNode(
      {
        node_id: nid("requirement", commitment.id),
        kind: "requirement",
        label: commitment.obligation,
        ref: commitment.id,
      },
      "compiled into"
    );
  }

  addNode({ node_id: nid("claim", v.claim_id), kind: "claim", label: v.claim_id, ref: v.claim_id }, "quantifies over");

  const report = reportsByPopulation.get(v.population_id);
  if (report) {
    const popNodeId = nid("population", report.population_id);
    addNode(
      { node_id: popNodeId, kind: "population", label: report.population_name, ref: report.population_id },
      "derived from"
    );

    const sourceIds = report.sources.map((s) => nid("source", s.name));
    report.sources.forEach((s, i) => {
      nodes.push({
        node_id: sourceIds[i],
        kind: "source",
        label: `${s.name} (${s.role})`,
        ref: s.capability_id ?? s.name,
      });
      edges.push({ from: popNodeId, to: sourceIds[i], relation: "derived from" });
    });

    const recNodeId = nid("reconciliation", report.population_id);
    nodes.push({
      node_id: recNodeId,
      kind: "reconciliation",
      label: `${report.ladder.at_first_verdict} → ${report.ladder.after_dispositions}`,
      ref: report.population_id,
    });
    if (sourceIds.length > 0) {
      sourceIds.forEach((sid) => edges.push({ from: sid, to: recNodeId, relation: "reconciled into" }));
    } else {
      edges.push({ from: popNodeId, to: recNodeId, relation: "reconciled into" });
    }
    prevId = recNodeId;
  }

  const contract = contractsByHash[v.spec_hash];
  if (contract) {
    addNode(
      { node_id: nid("contract", contract.id), kind: "contract", label: contract.id, ref: contract.contract_hash },
      "evidence gated by"
    );
  }

  if (report && manifest.blocks.populations.includes(report.population_id)) {
    addNode(
      {
        node_id: nid("snapshot", String(manifest.version)),
        kind: "snapshot",
        label: `v${manifest.version} (${manifest.lifecycle})`,
        ref: String(manifest.version),
      },
      "frozen in"
    );
  }

  addNode(
    { node_id: nid("assertion", v.assertion_id), kind: "assertion", label: v.assertion_id, ref: v.assertion_id },
    "executes"
  );
  addNode({ node_id: nid("verdict", v.record_hash), kind: "verdict", label: v.status, ref: v.record_hash }, "evaluates to");

  return { verdict_ref: v.record_hash, nodes, edges };
}

function deriveProofGraphs(
  verdicts: VerdictRecord[],
  reports: ReconciliationReport[],
  contracts: Record<string, EvidenceQualityContract>,
  manifest: ManifestSnapshot,
  commitments: CommitmentsFile
): ProofGraph[] {
  const reportsByPopulation = new Map(reports.map((r) => [r.population_id, r]));
  return verdicts.map((v) => buildProofGraph(v, reportsByPopulation, contracts, manifest, commitments));
}

let cached: EngagementLoad | null = null;

/** Load, guard, derive, and cache the engagement bundle. Never throws. */
export function loadEngagement(): EngagementLoad {
  if (cached) return cached;
  const drift: string[] = [];

  checkManifest(snapshotJson, drift);
  checkReconciliationReport(reconciliationJson, drift);
  const registryFile = registryJson as unknown as RegistryFile;
  checkRegistry((registryFile.entries ?? []) as unknown[], drift);
  checkCompileErrors((registryFile.compile_errors ?? []) as unknown[], drift);
  checkVerdicts(verdictsJson as unknown[], drift);
  checkCommitments(commitmentsJson, drift);
  checkContracts(contractsJson, drift);

  const reconciliations = deriveReconciliationReports();
  const populations = derivePopulations(reconciliations);
  const verdicts = verdictsJson as unknown as VerdictRecord[];
  const commitments = commitmentsJson as unknown as CommitmentsFile;
  const contracts = contractsJson as unknown as Record<string, EvidenceQualityContract>;
  const manifest = snapshotJson as unknown as ManifestSnapshot;
  const proof_graphs = deriveProofGraphs(verdicts, reconciliations, contracts, manifest, commitments);

  const artifacts: EngagementArtifacts = {
    manifest,
    capability_registry: registryFile.entries ?? [],
    commitments,
    populations,
    reconciliations,
    verdicts,
    compile_errors: registryFile.compile_errors ?? [],
    proof_graphs,
  };

  cached = { artifacts, drift };
  return cached;
}

/* ---------------- derived helpers (pure, computed, never stored) -------- */

/** URL-safe route key for a verdict: a stable prefix of its record_hash. */
export const VERDICT_SLUG_LEN = 12;

export function verdictSlug(v: VerdictRecord): string {
  return v.record_hash.slice(0, VERDICT_SLUG_LEN);
}

/** Resolve a route slug (record_hash prefix) — or a full hash — to its verdict. */
export function verdictBySlug(load: EngagementLoad, slug: string): VerdictRecord | undefined {
  if (slug.length < 8) return undefined; // too short to be unambiguous
  return load.artifacts.verdicts.find((v) => v.record_hash.startsWith(slug));
}

export function populationById(load: EngagementLoad, id: string): Population | undefined {
  return load.artifacts.populations.find((p) => p.id === id);
}

export function reconciliationFor(
  load: EngagementLoad,
  populationId: string
): ReconciliationReport | undefined {
  return load.artifacts.reconciliations.find((r) => r.population_id === populationId);
}

/** Proof lineage for a verdict, keyed by record_hash (prefix accepted). */
export function proofGraphFor(load: EngagementLoad, slug: string): ProofGraph | undefined {
  if (slug.length < 8) return undefined;
  return load.artifacts.proof_graphs.find((g) => g.verdict_ref.startsWith(slug));
}

/** Open (undispositioned) deltas for a population's reconciliation. */
export function openDeltaCount(load: EngagementLoad, populationId: string): number {
  const rec = reconciliationFor(load, populationId);
  if (!rec) return 0;
  return (Object.keys(rec.buckets) as DeltaBucket[])
    .filter((bucket) => bucket !== "intersection")
    .flatMap((bucket) => rec.buckets[bucket])
    .filter((d) => !d.disposition).length;
}

export function ladderCounts(load: EngagementLoad): Record<string, number> {
  const out: Record<string, number> = {};
  ASSURANCE_STATES.forEach((s) => (out[s] = 0));
  load.artifacts.populations.forEach((p) => {
    out[p.state] = (out[p.state] ?? 0) + 1;
  });
  return out;
}

export function verdictCounts(load: EngagementLoad): Record<string, number> {
  const out: Record<string, number> = {};
  VERDICT_STATES.forEach((s) => (out[s] = 0));
  load.artifacts.verdicts.forEach((v) => {
    out[v.status] = (out[v.status] ?? 0) + 1;
  });
  return out;
}
