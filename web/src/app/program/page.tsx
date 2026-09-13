import type { Metadata } from "next";
import ProgramClient from "./ProgramClient";

export const metadata: Metadata = { title: "Program — Aegis" };

export default function ProgramPage() {
  return (
    <main className="page">
      <div className="page-kicker">authoring · secondary</div>
      <h1>Program</h1>
      <p className="page-sub">
        The authoring workbench behind the lane — scope declarations, control
        posture, dataset registry, collector missions. Drafts live here; nothing on
        this page is a verdict.
      </p>
      <ProgramClient />
    </main>
  );
}
