import type { Metadata } from "next";
import { StubPage } from "@/components/StubPage/StubPage";

export const metadata: Metadata = { title: "Scope" };

export default function ScopePage() {
  return (
    <StubPage
      title="Scope determination"
      plannedIn="A3"
      description="Product-first scope: products carrying a commitment, the data classes they hold, and the asset stack resolved in / unknown / out — with the ledger and regime rail. Merges the scope-tool prototype with workbench stage 1."
    />
  );
}
