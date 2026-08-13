/* Engagement-artifact loader with lightweight runtime guards.
 *
 * The JSON under src/data/engagement/ is the REAL pipeline output,
 * synced verbatim from artifacts/demo-engagement/ by
 * scripts/sync-artifacts.mjs (committed == synced, CI-enforced). The
 * guards check enum membership and required keys against the mirrored
 * ontology so that artifact drift (backend renames a field, adds an
 * enum value…) surfaces as a visible red "artifact schema drift"
 * banner — never a crash, never a silent mis-render. On mismatch we
 * still return the parseable data.
 */

import manifestJson from "@/data/engagement/manifest.json";
import registryJson from "@/data/engagement/capability_registry.json";
import populationsJson from "@/data/engagement/populations.json";
import reconciliationJson from "@/data/engagement/reconciliation.json";
import verdictsJson from "@/data/engagement/verdicts.json";
import proofGraphJson from "@/data/engagement/proof_graph.json";

import {
  ASSURANCE_STATES,
  D7_FAMILIES,
  D7_FAMILY_WHY,
  POPULATION_TYPES,
  SOURCE_ROLES,
  UNKNOWN_WHY_CODES,
  VERDICT_STATES,
} from "@/lib/types/ontology";
import type { Population, VerdictRecord } from "@/lib/types/ontology";
import {
  ACCESS_MODES,
  DELTA_BUCKETS,
  PAGINATION_METHODS,
  PROOF_NODE_KINDS,
  TEMPORAL_SHAPE_KINDS,
} from "@/lib/types/artifacts";
import type {
  CapabilityEntry,
  CompileError,
  EngagementArtifacts,
  EngagementManifest,
  ProofGraph,
  ReconciliationResult,
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

function checkPopulations(pops: unknown[], drift: string[]): void {
  pops.forEach((p, i) => {
    const where = `populations[${i}]`;
    requireKeys(
      p,
      [
        "population_id",
        "name",
        "type",
        "definition",
        "derivation_rule",
        "sources",
        "period",
        "size",
        "exclusions",
        "open_deltas",
        "state",
      ],
      where,
      drift
    );
    if (!isRecord(p)) return;
    requireEnum(p.type, POPULATION_TYPES, `${where}.type`, drift);
    requireEnum(p.state, ASSURANCE_STATES, `${where}.state`, drift);
    if (Array.isArray(p.sources)) {
      p.sources.forEach((s, j) => {
        requireKeys(s, ["source_id", "role"], `${where}.sources[${j}]`, drift);
        if (isRecord(s))
          requireEnum(s.role, SOURCE_ROLES, `${where}.sources[${j}].role`, drift);
      });
    }
    if (isRecord(p.derivation_rule)) {
      requireKeys(
        p.derivation_rule,
        ["rule_text", "source_refs"],
        `${where}.derivation_rule`,
        drift
      );
    }
  });
}

function checkVerdicts(verdicts: unknown[], drift: string[]): void {
  verdicts.forEach((v, i) => {
    const where = `verdicts[${i}]`;
    requireKeys(
      v,
      [
        "claim_ref",
        "assertion_ref",
        "population_ref",
        "manifest_version",
        "snapshot_hash",
        "contract_hash",
        "state",
        "evaluated_at",
        "record_hash",
        "evidence_refs",
      ],
      where,
      drift
    );
    if (!isRecord(v)) return;
    requireEnum(v.state, VERDICT_STATES, `${where}.state`, drift);
    if (typeof v.record_hash !== "string" || v.record_hash.length < 12)
      drift.push(`${where}: record_hash must be a hash string (route identity)`);
    if (v.state === "UNKNOWN") {
      if (v.why_code == null) drift.push(`${where}: UNKNOWN requires a why_code`);
      else requireEnum(v.why_code, UNKNOWN_WHY_CODES, `${where}.why_code`, drift);
      if (v.d7_family != null) {
        requireEnum(v.d7_family, D7_FAMILIES, `${where}.d7_family`, drift);
        const mapped = D7_FAMILY_WHY[v.d7_family as keyof typeof D7_FAMILY_WHY];
        if (mapped && mapped !== v.why_code)
          drift.push(
            `${where}: d7_family "${String(v.d7_family)}" maps to ${mapped}, not ${String(v.why_code)}`
          );
      }
    }
    if (v.state === "EXCLUDED" && !v.ratification_ref)
      drift.push(`${where}: EXCLUDED requires a ratification_ref`);
    if (v.state === "EXCEPTION" && !v.disposition_ref)
      drift.push(`${where}: EXCEPTION requires a disposition_ref`);
    if (v.state === "FAIL" && !v.message)
      drift.push(`${where}: FAIL requires a message`);
  });
}

function checkCompileErrors(errors: unknown[], drift: string[]): void {
  errors.forEach((e, i) => {
    const where = `compile_errors[${i}]`;
    requireKeys(e, ["code", "message", "rendered", "claim_ref", "assertion_ref"], where, drift);
  });
}

function checkReconciliations(recs: unknown[], drift: string[]): void {
  recs.forEach((r, i) => {
    const where = `reconciliation[${i}]`;
    requireKeys(
      r,
      [
        "population_ref",
        "canonical_identity_keys",
        "source_counts",
        "deltas",
        "buckets",
        "members",
        "basis_complete",
        "basis_notes",
        "diagnostics",
        "ladder_state",
      ],
      where,
      drift
    );
    if (!isRecord(r)) return;
    requireEnum(r.ladder_state, ASSURANCE_STATES, `${where}.ladder_state`, drift);
    if (isRecord(r.buckets)) {
      requireKeys(r.buckets, [...DELTA_BUCKETS], `${where}.buckets`, drift);
    }
    if (!Array.isArray(r.deltas)) return;
    r.deltas.forEach((d, j) => {
      const dw = `${where}.deltas[${j}]`;
      requireKeys(
        d,
        [
          "delta_id",
          "bucket",
          "member_key",
          "display_name",
          "sources_present",
          "sources_absent",
          "owner",
          "disposition",
          "disposition_ref",
        ],
        dw,
        drift
      );
      if (isRecord(d)) requireEnum(d.bucket, DELTA_BUCKETS, `${dw}.bucket`, drift);
    });
  });
}

function checkRegistry(entries: unknown[], drift: string[]): void {
  entries.forEach((e, i) => {
    const where = `capability_registry[${i}]`;
    requireKeys(
      e,
      [
        "entry_id",
        "system",
        "surface",
        "access_modes",
        "populations_yielded",
        "attributes",
        "temporal",
        "join_keys",
        "auth_scope",
        "pagination",
        "rate_limits",
        "history_caveats",
        "provenance",
        "schema_version",
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
      requireEnum(e.temporal.kind, TEMPORAL_SHAPE_KINDS, `${where}.temporal.kind`, drift);
    if (isRecord(e.pagination))
      requireEnum(
        e.pagination.method,
        PAGINATION_METHODS,
        `${where}.pagination.method`,
        drift
      );
  });
}

function checkProofGraphs(graphs: unknown[], drift: string[]): void {
  graphs.forEach((g, i) => {
    const where = `proof_graph[${i}]`;
    requireKeys(g, ["verdict_ref", "nodes", "edges"], where, drift);
    if (!isRecord(g)) return;
    const ids = new Set<string>();
    if (Array.isArray(g.nodes)) {
      g.nodes.forEach((n, j) => {
        requireKeys(n, ["node_id", "kind", "label", "ref"], `${where}.nodes[${j}]`, drift);
        if (isRecord(n)) {
          requireEnum(n.kind, PROOF_NODE_KINDS, `${where}.nodes[${j}].kind`, drift);
          if (typeof n.node_id === "string") ids.add(n.node_id);
        }
      });
    }
    if (Array.isArray(g.edges)) {
      g.edges.forEach((ed, j) => {
        requireKeys(ed, ["from", "to", "relation"], `${where}.edges[${j}]`, drift);
        if (isRecord(ed)) {
          if (typeof ed.from === "string" && !ids.has(ed.from))
            drift.push(`${where}.edges[${j}]: "from" names unknown node "${ed.from}"`);
          if (typeof ed.to === "string" && !ids.has(ed.to))
            drift.push(`${where}.edges[${j}]: "to" names unknown node "${ed.to}"`);
        }
      });
    }
  });
}

let cached: EngagementLoad | null = null;

/** Load, guard, and cache the engagement bundle. Never throws. */
export function loadEngagement(): EngagementLoad {
  if (cached) return cached;
  const drift: string[] = [];

  requireKeys(
    manifestJson,
    [
      "manifest_version",
      "snapshot_hash",
      "ratified_by",
      "ratified_at",
      "engagement",
      "period",
      "boundary",
      "summary",
    ],
    "manifest",
    drift
  );

  const populationsFile = populationsJson as unknown as { populations?: unknown[] };
  const registryFile = registryJson as unknown as { entries?: unknown[] };
  const reconciliationFile = reconciliationJson as unknown as {
    reconciliations?: unknown[];
  };
  const verdictsFile = verdictsJson as unknown as {
    verdicts?: unknown[];
    compile_errors?: unknown[];
  };

  if (!Array.isArray(populationsFile.populations))
    drift.push('populations.json: missing top-level "populations" array');
  if (!Array.isArray(registryFile.entries))
    drift.push('capability_registry.json: missing top-level "entries" array');
  if (!Array.isArray(reconciliationFile.reconciliations))
    drift.push('reconciliation.json: missing top-level "reconciliations" array');

  checkPopulations(populationsFile.populations ?? [], drift);
  checkVerdicts(verdictsFile.verdicts ?? [], drift);
  checkCompileErrors(verdictsFile.compile_errors ?? [], drift);
  checkReconciliations(reconciliationFile.reconciliations ?? [], drift);
  checkRegistry(registryFile.entries ?? [], drift);
  checkProofGraphs(proofGraphJson as unknown[], drift);

  const artifacts: EngagementArtifacts = {
    manifest: manifestJson as unknown as EngagementManifest,
    capability_registry: (registryFile.entries ?? []) as CapabilityEntry[],
    populations: (populationsFile.populations ?? []) as unknown as Population[],
    reconciliations: (reconciliationFile.reconciliations ??
      []) as unknown as ReconciliationResult[],
    verdicts: (verdictsFile.verdicts ?? []) as unknown as VerdictRecord[],
    compile_errors: (verdictsFile.compile_errors ?? []) as unknown as CompileError[],
    proof_graphs: proofGraphJson as unknown as ProofGraph[],
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
  return load.artifacts.populations.find((p) => p.population_id === id);
}

export function reconciliationFor(
  load: EngagementLoad,
  populationId: string
): ReconciliationResult | undefined {
  return load.artifacts.reconciliations.find((r) => r.population_ref === populationId);
}

/** Proof lineage for a verdict, keyed by record_hash (prefix accepted). */
export function proofGraphFor(load: EngagementLoad, slug: string): ProofGraph | undefined {
  if (slug.length < 8) return undefined;
  return load.artifacts.proof_graphs.find((g) => g.verdict_ref.startsWith(slug));
}

/** An E117 that blocks this population from compiling (missing capability
 *  for one of its derivation sources) — the DEFINED-behind-E117 state. */
export function blockingCompileError(
  load: EngagementLoad,
  population: Population
): CompileError | undefined {
  return load.artifacts.compile_errors.find(
    (e) =>
      e.code === "E117" &&
      e.missing_source != null &&
      population.derivation_rule.source_refs.includes(e.missing_source)
  );
}

/** Open (undispositioned) deltas for a population's reconciliation. */
export function openDeltaCount(load: EngagementLoad, populationId: string): number {
  const rec = reconciliationFor(load, populationId);
  if (!rec) return 0;
  return rec.deltas.filter(
    (d) => d.bucket !== "intersection" && !d.disposition
  ).length;
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
    out[v.state] = (out[v.state] ?? 0) + 1;
  });
  return out;
}
