import type { Metadata } from "next";
import { gaugesSeed, scopeSeed } from "@/data";
import { ScopeWorkbench } from "./ScopeWorkbench";

export const metadata: Metadata = { title: "Scope" };

/**
 * A3 — /scope: the scope-tool prototype's product-first scoping surface
 * merged with workbench stage 1's system registry, plus the scope
 * ledger / regime rail. All data flows from the typed seed layer; the
 * server page hands it to one client component for the interaction.
 */
export default function ScopePage() {
  return <ScopeWorkbench seed={scopeSeed} gauges={gaugesSeed} />;
}
