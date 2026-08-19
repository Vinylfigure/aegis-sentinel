import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  engagementPoisons,
  engagementReconciliations,
  engagementRegistry,
  engagementVerdictRecords,
} from "@/data";
import { ProofLineage } from "./ProofLineage";

/** Unknown verdict ids 404 at the route level. */
export const dynamicParams = false;

export function generateStaticParams() {
  // Raw record ids — Next percent-encodes when emitting routes; `@` and `.`
  // are legal pchars. Links elsewhere use encodeURIComponent; findRecord
  // below tolerates either form.
  return engagementVerdictRecords.map((record) => ({
    verdictId: record.record_id,
  }));
}

function findRecord(param: string) {
  const decoded = (() => {
    try {
      return decodeURIComponent(param);
    } catch {
      return param;
    }
  })();
  return engagementVerdictRecords.find(
    (r) => r.record_id === decoded || r.record_id === param,
  );
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ verdictId: string }>;
}): Promise<Metadata> {
  const { verdictId } = await params;
  const record = findRecord(verdictId);
  return { title: record ? `Proof · ${record.record_id}` : "Proof" };
}

/**
 * B4 — /proof/[verdictId]: UI01's proof-graph lineage view. Ten stages,
 * typed arrows, node inspector; the population node links into the
 * why-complete rail.
 */
export default async function ProofDetailPage({
  params,
}: {
  params: Promise<{ verdictId: string }>;
}) {
  const { verdictId } = await params;
  const record = findRecord(verdictId);
  if (!record) notFound();
  return (
    <ProofLineage
      record={record}
      reconciliations={engagementReconciliations}
      registry={engagementRegistry}
      poisons={engagementPoisons}
    />
  );
}
