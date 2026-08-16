import type { Metadata } from "next";
import { StubPage } from "@/components/StubPage/StubPage";

export const metadata: Metadata = { title: "Reconciliation" };

export default function ReconciliationPage() {
  return (
    <StubPage
      title="Reconciliation"
      plannedIn="B2"
      description="Population reconciliation: assurance-ladder stepper, canonical identity join panel, the six delta buckets as first-class objects with owner and disposition, and the why-complete rail. Consumes artifacts/demo-engagement/reconciliation.json."
    />
  );
}
