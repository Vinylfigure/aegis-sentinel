import type { Metadata } from "next";
import { controlsSeed, gaugesSeed, scopeSeed } from "@/data";
import { OverlordConsole } from "./OverlordConsole";

export const metadata: Metadata = { title: "Overlord" };

/**
 * A4 — /overlord: workbench stage 4. Missions are GENERATED — one
 * deterministic collector per derived dataset plus the seed's LLM-lane
 * tasks (non-verdict) — and the mission manifest is exported as text
 * client-side. Agent gauges ride the rail.
 */
export default function OverlordPage() {
  return (
    <OverlordConsole seed={controlsSeed} scope={scopeSeed} gauges={gaugesSeed} />
  );
}
