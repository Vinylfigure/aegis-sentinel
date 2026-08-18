import type { Metadata } from "next";
import { controlsSeed, gaugesSeed, scopeSeed } from "@/data";
import { ControlsWorkbench } from "./ControlsWorkbench";

export const metadata: Metadata = { title: "Controls" };

/**
 * A4 — /controls: workbench stage 2. The control library by domain,
 * classification segments, system mapping against the scope registry,
 * and the live posture gauges in the rail. All data flows from the
 * typed seed layer; the server page hands it to one client component.
 */
export default function ControlsPage() {
  return (
    <ControlsWorkbench seed={controlsSeed} scope={scopeSeed} gauges={gaugesSeed} />
  );
}
