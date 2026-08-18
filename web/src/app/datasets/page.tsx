import type { Metadata } from "next";
import { controlsSeed, gaugesSeed, scopeSeed } from "@/data";
import { DatasetsRegistry } from "./DatasetsRegistry";

export const metadata: Metadata = { title: "Datasets" };

/**
 * A4 — /datasets: workbench stage 3. The dataset registry is DERIVED
 * in code from the control↔system mappings in the controls seed
 * (deduplicated by system + artifact) — no dataset rows are authored.
 * Dataset gauges ride the rail.
 */
export default function DatasetsPage() {
  return (
    <DatasetsRegistry seed={controlsSeed} scope={scopeSeed} gauges={gaugesSeed} />
  );
}
