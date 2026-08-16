import type { Metadata } from "next";
import { StubPage } from "@/components/StubPage/StubPage";

export const metadata: Metadata = { title: "Process" };

export default function ProcessPage() {
  return (
    <StubPage
      title="Process graph"
      plannedIn="A5"
      description="Controls on the flow: assets as nodes tinted by data classification, ITGC processes as left-to-right lanes, control points on the edges — with a detail rail expanding each point into nature, function, data element, and evidence type."
    />
  );
}
