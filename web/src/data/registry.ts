/**
 * B3 — derivations over registry.json.
 *
 * The load-bearing rule here is SCH02's: an unratified entry is
 * *mechanically unusable* — `Registry.usable()` excludes it and a test
 * proves it. So usability is DERIVED from lifecycle + ratifier on this page,
 * never asserted, and a DRAFT entry can never render as available.
 *
 * web/README.md carries this as a hard requirement: a registry page that
 * shows DRAFT entries as usable without their caveats "misrepresents
 * ratification state — that is a demo-correctness bug, not a styling
 * choice." Hence `usability()` and `draftCaveats()` rather than a badge.
 */

import type { CompileError, RegistryArtifact, RegistryEntry } from "@/data/types";

/* ------------------------------------------------------------------ */
/* Usability (SCH02)                                                   */
/* ------------------------------------------------------------------ */

export interface Usability {
  usable: boolean;
  /** Why — rendered, so the badge is an argument rather than a colour. */
  reason: string;
}

/**
 * D-L1 collapsed the lifecycle to `draft → frozen(=ratified) → superseded`,
 * so "frozen" IS "ratified" and a missing ratifier on a frozen entry is a
 * contradiction worth surfacing rather than rounding off.
 */
export function usability(entry: RegistryEntry): Usability {
  // Exhaustive switch (B3 verifier finding): an if-chain would let a new
  // LifecycleState member fall through to "usable" — the one direction this
  // page must never default to. The `never` arm makes it a compile error.
  switch (entry.lifecycle) {
    case "superseded":
      return { usable: false, reason: "superseded — a later version replaced it." };
    case "draft":
      return {
        usable: false,
        reason:
          "DRAFT — not ratified, so the compiler cannot use it (SCH02: unratified entries are mechanically excluded).",
      };
    case "frozen":
      if (!entry.ratified_by) {
        return {
          usable: false,
          reason:
            "frozen but no ratifier recorded — D-L1 makes ratification the freeze, so this entry contradicts itself.",
        };
      }
      return {
        usable: true,
        reason: `ratified by ${entry.ratified_by} (D-L1: ratification is the freeze).`,
      };
    default: {
      const exhaustive: never = entry.lifecycle;
      return exhaustive;
    }
  }
}

export function usableEntries(artifact: RegistryArtifact): RegistryEntry[] {
  return artifact.entries.filter((e) => usability(e).usable);
}

export function unusableEntries(artifact: RegistryArtifact): RegistryEntry[] {
  return artifact.entries.filter((e) => !usability(e).usable);
}

/* ------------------------------------------------------------------ */
/* Caveats                                                             */
/* ------------------------------------------------------------------ */

/** Caveats flagged DRAFT on the wire. Rendered verbatim, never truncated —
 * see the module docstring. */
export function draftCaveats(entry: RegistryEntry): string[] {
  return entry.history_caveats.filter((c) => c.startsWith("DRAFT:"));
}

/** Everything else — real capability limits, e.g. CAP01's Okta 90-day
 * System Log window, which is the E204 trap on a real lane. */
export function historyCaveats(entry: RegistryEntry): string[] {
  return entry.history_caveats.filter((c) => !c.startsWith("DRAFT:"));
}

export function entriesWithDraftCaveats(artifact: RegistryArtifact): RegistryEntry[] {
  return artifact.entries.filter((e) => draftCaveats(e).length > 0);
}

/* ------------------------------------------------------------------ */
/* Compile errors                                                      */
/* ------------------------------------------------------------------ */

export interface CompileErrorMeta {
  code: string;
  title: string;
  /** What the compiler refuses to do — an E-code is a refusal, not a warning. */
  consequence: string;
}

/**
 * E-codes as compiler errors. TYP01's contract is that zero collectors are
 * executable for claims carrying an unresolved E-code, so the page states
 * the refusal rather than styling the message as a warning.
 * Unknown codes degrade to a generic entry rather than throwing — the
 * registry may emit a code this build has never seen.
 */
const CODE_META: Record<string, CompileErrorMeta> = {
  E117: {
    code: "E117",
    title: "missing capability",
    consequence:
      "no ratified capability entry backs a source this population derives from — the claim does not compile, so no collector runs for it.",
  },
  E204: {
    code: "E204",
    title: "temporal insufficiency",
    consequence:
      "the evidence window cannot cover the period asserted — the compiler names a satisfying combination instead of guessing.",
  },
  E302: {
    code: "E302",
    title: "schema drift",
    consequence:
      "the collected shape no longer matches the contract's schema version — the contract is unfit until re-ratified.",
  },
};

export function compileErrorMeta(code: string): CompileErrorMeta {
  return (
    CODE_META[code] ?? {
      code,
      title: "compile error",
      consequence:
        "the claim does not compile; no collector executes for it (TYP01). This code has no description in the frontend's table.",
    }
  );
}

export function groupedCompileErrors(
  artifact: RegistryArtifact,
): { meta: CompileErrorMeta; errors: CompileError[] }[] {
  const groups = new Map<string, CompileError[]>();
  for (const error of artifact.compile_errors) {
    const existing = groups.get(error.code);
    if (existing) existing.push(error);
    else groups.set(error.code, [error]);
  }
  return [...groups.entries()].map(([code, errors]) => ({
    meta: compileErrorMeta(code),
    errors,
  }));
}

/* ------------------------------------------------------------------ */
/* Registry health (PRD §7, Secondary)                                 */
/* ------------------------------------------------------------------ */

export interface RegistryHealth {
  total: number;
  usable: number;
  draft: number;
  withDraftCaveats: number;
  compileErrors: number;
}

export function registryHealth(artifact: RegistryArtifact): RegistryHealth {
  return {
    total: artifact.entries.length,
    usable: usableEntries(artifact).length,
    draft: artifact.entries.filter((e) => e.lifecycle === "draft").length,
    withDraftCaveats: entriesWithDraftCaveats(artifact).length,
    compileErrors: artifact.compile_errors.length,
  };
}
