import type { Metadata } from "next";
import { controlsSeed, processSeed, scopeSeed } from "@/data";
import { ProcessGraph } from "./ProcessGraph";

export const metadata: Metadata = { title: "Process" };

/**
 * A5 — /process: the process-graph prototype as a route. ITGC processes
 * as left-to-right lanes, systems as nodes tinted by data tier, control
 * points as diamonds on the flow, and a detail rail that expands the
 * selected point into nature, function, data element, and evidence.
 * All data flows from the typed seed layer; the server page hands it to
 * one client component that owns only the selection interaction.
 */
export default function ProcessPage() {
  return (
    <ProcessGraph seed={processSeed} controls={controlsSeed} scope={scopeSeed} />
  );
}
