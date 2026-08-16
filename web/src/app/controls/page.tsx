import type { Metadata } from "next";
import { StubPage } from "@/components/StubPage/StubPage";

export const metadata: Metadata = { title: "Controls" };

export default function ControlsPage() {
  return (
    <StubPage
      title="Control library"
      plannedIn="A4"
      description="The control library by domain: nature (configurable · automated · manual), function (preventative · detective), compensating flags, and system mappings — feeding the derived dataset registry and posture gauges."
    />
  );
}
