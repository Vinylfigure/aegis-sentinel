import type { Metadata } from "next";
import { engagementPoisons, engagementVerdicts } from "@/data";
import { VerdictsBoard } from "./VerdictsBoard";

export const metadata: Metadata = { title: "Verdicts" };

/**
 * B3 — /verdicts: the five verdict states rendered distinctly, UNKNOWN
 * why-code chips, and the mutation scorecard. PRD §6 acceptance: the five
 * states must be visibly distinct and every seeded defect visibly caught.
 */
export default function VerdictsPage() {
  return <VerdictsBoard records={engagementVerdicts} poisons={engagementPoisons} />;
}
