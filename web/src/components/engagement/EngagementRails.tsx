"use client";

/* Route-specific rails for the engagement detail screens.
 * - Reconciliation detail: the WhyCompletePanel narrative (delta-focused).
 * - Proof detail: the NodeInspector for the clicked lineage node. */

import { usePathname } from "next/navigation";
import {
  loadEngagement,
  populationById,
  proofGraphFor,
  reconciliationFor,
} from "@/lib/data/engagement";
import { useEngagementStore } from "@/lib/state/engagementStore";
import railStyles from "@/components/Rail.module.css";
import AssuranceSection from "./AssuranceSection";
import NodeInspector from "./NodeInspector";
import WhyCompletePanel from "./WhyCompletePanel";

export function ReconciliationDetailRail() {
  const pathname = usePathname();
  const load = loadEngagement();
  const populationId = decodeURIComponent(pathname?.split("/")[2] ?? "");
  const population = populationById(load, populationId);

  if (!population) {
    return <div className={railStyles.empty}>Unknown population.</div>;
  }
  return (
    <div>
      <WhyCompletePanel
        population={population}
        recon={reconciliationFor(load, populationId)}
      />
    </div>
  );
}

export function ProofDetailRail() {
  const pathname = usePathname();
  const load = loadEngagement();
  // Route key = record_hash prefix (see /proof/[verdictId]).
  const verdictId = decodeURIComponent(pathname?.split("/")[2] ?? "");
  const graph = proofGraphFor(load, verdictId);
  const selectedProofNodeId = useEngagementStore((s) => s.selectedProofNodeId);
  const node = graph?.nodes.find((n) => n.node_id === selectedProofNodeId);

  if (!node) {
    return (
      <div>
        <h2 className={railStyles.h2}>Node inspector</h2>
        <p className={railStyles.empty}>
          Click any node in the lineage to expand it — the population node opens
          the same completeness narrative the reconciliation screen shows.
        </p>
        <AssuranceSection />
      </div>
    );
  }
  return <NodeInspector node={node} />;
}
