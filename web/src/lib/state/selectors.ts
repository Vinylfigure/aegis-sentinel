/* Pure selectors — ported from the prototype functions (registry, ledger,
 * rRail, rOV, exportManifest, summarize). Derived, never stored. */

import type {
  CollectorMission,
  Control,
  DatasetEntry,
  LlmTask,
  ProductState,
  Regime,
  SystemEntry,
  Tri,
} from "@/lib/types/authoring";
import { ART_RET, CA, DATA_CLASSES, LAYERS, PRODUCTS, REGIMES } from "@/data/seed";

/** Dataset registry: dedupe control↔system dataset refs by system|artifact. */
export function datasetRegistry(controls: Control[]): DatasetEntry[] {
  const map: Record<string, DatasetEntry> = {};
  controls.forEach((ctl) =>
    ctl.ds.forEach((d) => {
      const key = d.sys + "|" + d.art;
      if (!map[key]) map[key] = { sys: d.sys, art: d.art, ret: d.ret, ca: d.ca, ctls: [] };
      map[key].ctls.push(ctl.c);
    })
  );
  return Object.values(map);
}

/** Data classes carried by active products. */
export function activeClasses(products: Record<string, ProductState>): Set<string> {
  const set = new Set<string>();
  PRODUCTS.forEach((p) => {
    const s = products[p.id];
    if (s?.on) s.cls.forEach((c) => set.add(c));
  });
  return set;
}

/** Regimes lit from the declared data classes. */
export function triggeredRegimes(
  products: Record<string, ProductState>
): { regime: Regime; lit: boolean }[] {
  const cls = activeClasses(products);
  return REGIMES.map((regime) => ({
    regime,
    lit: regime.on.some((c) => cls.has(c)),
  }));
}

export interface ScopeTally {
  tIn: number;
  tUnk: number;
  tOut: number;
  activeProducts: number;
  totalItems: number;
}

/** Asset-inventory tally across active products (unresolved defaults to unk). */
export function scopeTally(products: Record<string, ProductState>): ScopeTally {
  let tIn = 0,
    tUnk = 0,
    tOut = 0,
    activeProducts = 0,
    totalItems = 0;
  PRODUCTS.forEach((p) => {
    const s = products[p.id];
    if (!s?.on) return;
    activeProducts++;
    LAYERS.forEach((L, li) =>
      L.items.forEach((_, ii) => {
        totalItems++;
        const v: Tri = s.items[`${li}:${ii}`] || "unk";
        if (v === "in") tIn++;
        else if (v === "out") tOut++;
        else tUnk++;
      })
    );
  });
  return { tIn, tUnk, tOut, activeProducts, totalItems };
}

export interface ScopeVerdict {
  state: "notstarted" | "blocked" | "clear";
  verdict: string;
  note: string;
}

/** Scope ledger assertion — blocked until zero unknowns (scope-tool copy). */
export function scopeVerdict(t: ScopeTally): ScopeVerdict {
  if (!t.activeProducts)
    return {
      state: "notstarted",
      verdict: "Not started",
      note: "Select at least one product to begin.",
    };
  if (t.tUnk > 0)
    return {
      state: "blocked",
      verdict: "Assertion blocked",
      note: `${t.tUnk} of ${t.totalItems} assets unresolved across ${t.activeProducts} product${t.activeProducts > 1 ? "s" : ""}. Scope cannot be asserted while any asset is unknown — resolve or explicitly exclude each one, with the reason.`,
    };
  return {
    state: "clear",
    verdict: "Scope assertable",
    note: `${t.tIn} assets in boundary, ${t.tOut} excluded with rationale, zero unresolved. Document the exclusions — the auditor will re-litigate them annually.`,
  };
}

export interface ControlPosture {
  cfgPrevPct: number;
  manualCount: number;
  noDatasetCount: number;
}

export function controlPosture(controls: Control[]): ControlPosture {
  const cfgPrev = controls.filter((c) => c.nat === "cfg" && c.fn === "prev").length;
  return {
    cfgPrevPct: controls.length ? Math.round((100 * cfgPrev) / controls.length) : 0,
    manualCount: controls.filter((c) => c.nat === "manual").length,
    noDatasetCount: controls.filter((c) => !c.ds.length).length,
  };
}

export function avgReuse(controls: Control[], registry: DatasetEntry[]): string {
  if (!registry.length) return "—";
  const total = controls.reduce((a, c) => a + c.ds.length, 0);
  return (total / registry.length).toFixed(1);
}

export function systemScopeCounts(systems: SystemEntry[]): { inS: number; unk: number } {
  return {
    inS: systems.filter((s) => s.v === "in").length,
    unk: systems.filter((s) => s.v === "unk").length,
  };
}

/** LLM-lane Sentinel tasks — advisory only, never verdicts. */
export const LLM_TASKS: LlmTask[] = [
  {
    id: "A-01",
    name: "Triage unresolved / UNKNOWN results",
    boundary:
      "reads collector output, drafts investigation plan, routes to owner — never records a verdict",
    task: "triage-unknowns",
  },
  {
    id: "A-02",
    name: "Draft exception narratives",
    boundary: "grounds every claim in a named evidence record; human sign-off required",
    task: "exception-narratives",
  },
  {
    id: "A-03",
    name: "Map new risks to existing datasets",
    boundary:
      "buckets incoming risks into domains; flags where an existing tested dataset already covers them",
    task: "risk-to-dataset-mapping",
  },
];

/** Deterministic collector missions — one per unique dataset. */
export function missions(controls: Control[], systems: SystemEntry[]): CollectorMission[] {
  return datasetRegistry(controls).map((d, i) => {
    const s = systems.find((x) => x.id === d.sys);
    const cadence = d.art.toLowerCase().includes("config")
      ? "daily · +event-driven on change"
      : d.ret === "shot"
        ? "weekly"
        : "daily";
    return {
      id: "C-" + String(i + 1).padStart(2, "0"),
      art: d.art,
      sysId: d.sys,
      sysName: s ? s.name : d.sys,
      scopeUnresolved: !!s && s.v !== "in",
      surface: ART_RET[d.ret],
      ca: CA[d.ca],
      cadence,
      ctls: d.ctls,
    };
  });
}

/** Mission manifest JSON — same shape as the prototype exportManifest(). */
export function buildManifest(
  products: Record<string, ProductState>,
  systems: SystemEntry[],
  controls: Control[]
): string {
  const reg = datasetRegistry(controls);
  const m = {
    generated: new Date().toISOString(),
    scope: {
      products: PRODUCTS.filter((p) => products[p.id]?.on).map((p) => p.name),
      systems_in: systems.filter((s) => s.v === "in").map((s) => s.name),
      unresolved: systems.filter((s) => s.v === "unk").map((s) => s.name),
    },
    collectors: reg.map((d, i) => ({
      id: "C-" + String(i + 1).padStart(2, "0"),
      target: (systems.find((x) => x.id === d.sys) || { name: undefined }).name,
      artifact: d.art,
      surface: ART_RET[d.ret],
      ca: CA[d.ca],
      controls: d.ctls,
      lane: "deterministic-verdict",
    })),
    llm_lane: LLM_TASKS.map((t) => ({
      id: t.id,
      task: t.task,
      verdict_authority: false,
    })),
  };
  return JSON.stringify(m, null, 1);
}

/** Scope summary text — ported from scope-tool summarize(). */
export function scopeSummary(products: Record<string, ProductState>): string {
  const cls = activeClasses(products);
  const lines: string[] = ["SCOPE DETERMINATION", ""];
  PRODUCTS.filter((p) => products[p.id]?.on).forEach((p) => {
    const s = products[p.id];
    lines.push(`▸ ${p.name}`);
    const cnames = s.cls.map((c) => DATA_CLASSES.find((d) => d.id === c)?.name ?? c);
    lines.push(`  data: ${cnames.length ? cnames.join(", ") : "— none declared —"}`);
    LAYERS.forEach((L, li) => {
      const ins: string[] = [],
        unks: string[] = [];
      L.items.forEach((it, ii) => {
        const v: Tri = s.items[`${li}:${ii}`] || "unk";
        if (v === "in") ins.push(it.name);
        if (v === "unk") unks.push(it.name);
      });
      if (ins.length) lines.push(`  ${L.n} — IN: ${ins.join("; ")}`);
      if (unks.length) lines.push(`  ${L.n} — UNRESOLVED: ${unks.join("; ")}`);
    });
    lines.push("");
  });
  lines.push("REGIMES TRIGGERED");
  REGIMES.filter((r) => r.on.some((c) => cls.has(c))).forEach((r) =>
    lines.push(`  • ${r.name} — ${r.why}`)
  );
  return lines.join("\n");
}
