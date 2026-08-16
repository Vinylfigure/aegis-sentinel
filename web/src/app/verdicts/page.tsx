import type { Metadata } from "next";
import { StubPage } from "@/components/StubPage/StubPage";

export const metadata: Metadata = { title: "Verdicts" };

export default function VerdictsPage() {
  return (
    <StubPage
      title="Verdicts"
      plannedIn="B3"
      description="Verdict records with the five states visibly distinct, why-code chips, and the mutation scorecard. Consumes artifacts/demo-engagement/verdicts.json and poisons.json."
    />
  );
}
