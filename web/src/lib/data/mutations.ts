/* The six poison cases (PRD-v3 §6 — the mutation playbook's seed set)
 * and what detects each one in the mock engagement. The headline metric:
 * mutated defects that produce compile-error / UNKNOWN / FAIL ÷ defects
 * introduced. Any silent PASS is a build-stopping bug.
 */

import type { VerdictState } from "@/lib/types/ontology";

export interface MutationPoison {
  id: string;
  poison: string;
  /** What fired: a verdict state or a compile E-code. */
  detector:
    | { kind: "verdict"; state: VerdictState; verdict_id: string; note: string }
    | { kind: "ecode"; code: "E204" | "E117" | "E302"; note: string };
  detected: boolean;
}

export const MUTATION_POISONS: MutationPoison[] = [
  {
    id: "poison-1",
    poison: "Contractor absent from HRIS (in IdP only)",
    detector: {
      kind: "verdict",
      state: "UNKNOWN",
      verdict_id: "vr-iam02-a",
      note: "UNKNOWN_POPULATION · identity_fuzzy — left-only delta d-201, negative space named",
    },
    detected: true,
  },
  {
    id: "poison-2",
    poison: "Dormant GitHub local account",
    detector: {
      kind: "verdict",
      state: "FAIL",
      verdict_id: "vr-am06-c",
      note: "NON_EXISTENCE fail — right-only delta d-202, no removal event in audit log",
    },
    detected: true,
  },
  {
    id: "poison-3",
    poison: "Break-glass cloud account outside IAM",
    detector: {
      kind: "ecode",
      code: "E117",
      note: "pop-prod-modifiers refuses to compile — breakglass.config has no capability entry",
    },
    detected: true,
  },
  {
    id: "poison-4",
    poison: "Failed identity join (unmappable login)",
    detector: {
      kind: "verdict",
      state: "UNKNOWN",
      verdict_id: "vr-iam02-a",
      note: "unresolvable delta d-203 (dev-akira9) keeps the join population fuzzy",
    },
    detected: true,
  },
  {
    id: "poison-5",
    poison: "Delayed revocation (6 business days)",
    detector: {
      kind: "verdict",
      state: "FAIL",
      verdict_id: "vr-am06-b",
      note: "TIMING fail — business-day arithmetic from HRIS effective date to IdP deactivation",
    },
    detected: true,
  },
  {
    id: "poison-6",
    poison: "Legitimate exception (retained access)",
    detector: {
      kind: "verdict",
      state: "EXCEPTION",
      verdict_id: "vr-am06-g",
      note: "EXCEPTION with disposition disp-2026-044 — surfaced and owned, never a silent PASS",
    },
    detected: true,
  },
];

export function detectionRate(): { detected: number; total: number; pct: number } {
  const total = MUTATION_POISONS.length;
  const detected = MUTATION_POISONS.filter((p) => p.detected).length;
  return { detected, total, pct: total ? Math.round((100 * detected) / total) : 0 };
}
