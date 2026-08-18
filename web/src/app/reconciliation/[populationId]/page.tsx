import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { engagementReconciliations } from "@/data";
import { ReconciliationDetail } from "./ReconciliationDetail";

/** Unknown ids 404 at the route level rather than rendering an empty shell. */
export const dynamicParams = false;

export function generateStaticParams() {
  return engagementReconciliations.map((report) => ({
    populationId: report.population_id,
  }));
}

function findReport(populationId: string) {
  return engagementReconciliations.find((r) => r.population_id === populationId);
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ populationId: string }>;
}): Promise<Metadata> {
  const { populationId } = await params;
  const report = findReport(populationId);
  return { title: report ? `Reconciliation · ${report.population_id}` : "Reconciliation" };
}

/**
 * B2 — /reconciliation/[populationId]: the set-reconciliation screen PRD §6
 * names as the acceptance test ("now I know why the population is
 * complete"). Server route; the interaction lives in ReconciliationDetail.
 */
export default async function ReconciliationDetailPage({
  params,
}: {
  params: Promise<{ populationId: string }>;
}) {
  const { populationId } = await params;
  const report = findReport(populationId);
  if (!report) notFound();
  return <ReconciliationDetail report={report} />;
}
