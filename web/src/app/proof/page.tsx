import type { Metadata } from "next";
import { StubPage } from "@/components/StubPage/StubPage";

export const metadata: Metadata = { title: "Proof" };

export default function ProofPage() {
  return (
    <StubPage
      title="Proof lineage"
      plannedIn="B4"
      description="Per-verdict proof: the ten-stage SVG lineage from capability entry to verdict record, with a node inspector. Lands as /proof/[verdictId]; this index will list verdicts to inspect."
    />
  );
}
