/* Engagement-artifact loader with lightweight runtime guards.
 *
 * The mock JSON is hand-authored; these guards check enum membership and
 * required keys against the mirrored ontology so that artifact drift
 * (backend renames a field, adds an enum value…) surfaces as a visible
 * red "artifact schema drift" banner — never a crash, never a silent
 * mis-render. On mismatch we still return the parseable data.
 */

import manifestJson from "@/data/engagement/manifest.json";
import registryJson from "@/data/engagement/capability_registry.json";
import populationsJson from "@/data/engagement/populations.json";
import reconciliationJson from "@/data/engagement/reconciliation.json";
import verdictsJson from "@/data/engagement/verdicts.json";
import proofGraphJson from "@/data/engagement/proof_graph.json";

import {
  ASSERTION_TYPES,
  ASSURANCE_STATES,
  D7_FAMILIES,
  D7_FAMILY_WHY,
  POPULATION_TYPES,
  SOURCE_ROLES,
  UNKNOWN_WHY_CODES,
  VERDICT_STATES,
} from "@/lib/types/ontology";
import type { Claim, Population, VerdictRecord } from "@/lib/types/ontology";
import {
  ACCESS_MODES,
  DELTA_BUCKETS,
  PROOF_NODE_KINDS,
} from "@/lib/types/artifacts";
import type {
  CapabilityEntry,
  ECode,
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

function checkClaims(claims: unknown[], drift: string[]): void {
  claims.forEach((c, i) => {
    const where = `claims[${i}]`;
    requireKeys(c, ["claim_id", "statement", "population_ref", "assertions"], where, drift);
    if (!isRecord(c) || !Array.isArray(c.assertions)) return;
    c.assertions.forEach((a, j) => {
      const aw = `${where}.assertions[${j}]`;
      requireKeys(
        a,
        ["assertion_id", "claim_ref", "type", "predicate_text", "population_ref"],
        aw,
        drift
      );
      if (isRecord(a)) requireEnum(a.type, ASSERTION_TYPES, `${aw}.type`, drift);
    });
  });
}

function checkVerdicts(verdicts: unknown[], drift: string[]): void {
  verdicts.forEach((v, i) => {
    const where = `verdicts[${i}]`;
    requireKeys(
      v,
      [
        "verdict_id",
        "claim_ref",
        "assertion_ref",
        "population_ref",
        "manifest_version",
        "snapshot_hash",
        "contract_hash",
        "state",
        "evaluated_at",
      ],
      where,
      drift
    );
    if (!isRecord(v)) return;
    requireEnum(v.state, VERDICT_STATES, `${where}.state`, drift);
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

function checkReconciliations(recs: unknown[], drift: string[]): void {
  recs.forEach((r, i) => {
    const where = `reconciliation[${i}]`;
    requireKeys(
      r,
      ["population_ref", "canonical_identity_keys", "source_counts", "deltas"],
      where,
      drift
    );
    if (!isRecord(r) || !Array.isArray(r.deltas)) return;
    r.deltas.forEach((d, j) => {
      const dw = `${where}.deltas[${j}]`;
      requireKeys(
        d,
        ["delta_id", "bucket", "member_key", "sources_present", "sources_absent"],
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
        "temporal",
        "join_keys",
        "auth_scope",
        "pagination",
        "history_caveats",
        "provenance",
      ],
      where,
      drift
    );
    if (!isRecord(e)) return;
    if (Array.isArray(e.access_modes))
      e.access_modes.forEach((m, j) =>
        requireEnum(m, ACCESS_MODES, `${where}.access_modes[${j}]`, drift)
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
    ["manifest_version", "snapshot_hash", "ratified_by", "ratified_at", "engagement", "period"],
    "manifest",
    drift
  );

  const verdictsBundle = verdictsJson as unknown as {
    claims: unknown[];
    verdicts: unknown[];
    compile_errors: unknown[];
  };

  checkPopulations(populationsJson as unknown[], drift);
  checkClaims(verdictsBundle.claims ?? [], drift);
  checkVerdicts(verdictsBundle.verdicts ?? [], drift);
  checkReconciliations(reconciliationJson as unknown[], drift);
  checkRegistry(registryJson as unknown[], drift);
  checkProofGraphs(proofGraphJson as unknown[], drift);
  (verdictsBundle.compile_errors ?? []).forEach((e, i) =>
    requireKeys(e, ["code", "message"], `compile_errors[${i}]`, drift)
  );

  const artifacts: EngagementArtifacts = {
    manifest: manifestJson as EngagementManifest,
    capability_registry: registryJson as unknown as CapabilityEntry[],
    populations: populationsJson as unknown as Population[],
    reconciliations: reconciliationJson as unknown as ReconciliationResult[],
    claims: (verdictsBundle.claims ?? []) as Claim[],
    verdicts: (verdictsBundle.verdicts ?? []) as VerdictRecord[],
    compile_errors: (verdictsBundle.compile_errors ?? []) as ECode[],
    proof_graphs: proofGraphJson as unknown as ProofGraph[],
  };

  cached = { artifacts, drift };
  return cached;
}

/* ---------------- derived helpers (pure, computed, never stored) -------- */

export function populationById(load: EngagementLoad, id: string): Population | undefined {
  return load.artifacts.populations.find((p) => p.population_id === id);
}

export function reconciliationFor(
  load: EngagementLoad,
  populationId: string
): ReconciliationResult | undefined {
  return load.artifacts.reconciliations.find((r) => r.population_ref === populationId);
}

export function verdictById(load: EngagementLoad, id: string): VerdictRecord | undefined {
  return load.artifacts.verdicts.find((v) => v.verdict_id === id);
}

export function proofGraphFor(load: EngagementLoad, verdictId: string): ProofGraph | undefined {
  return load.artifacts.proof_graphs.find((g) => g.verdict_ref === verdictId);
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
