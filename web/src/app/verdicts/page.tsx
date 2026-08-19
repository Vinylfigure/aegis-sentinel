import type { Metadata } from "next";
import { engagementPoisons, engagementVerdictRecords, engagementVerdicts } from "@/data";
import { VerdictsBoard } from "./VerdictsBoard";

export const metadata: Metadata = { title: "Verdicts" };

/**
 * B3 — /verdicts: the five verdict states rendered distinctly, UNKNOWN
 * why-code chips, and the mutation scorecard. PRD §6 acceptance: the five
 * states must be visibly distinct and every seeded defect visibly caught.
 */
export default function VerdictsPage() {
  // The combined roster: verdicts.json (walking-skeleton run) plus the
  // poison run's records embedded in poisons.json. engagementVerdicts alone
  // carries one record post-C2 — the five-state spread lives in the runs.
  return (
    <VerdictsBoard
      records={engagementVerdictRecords}
      verdicts={engagementVerdicts}
      poisons={engagementPoisons}
    />
  );
}
