"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import NavTabs from "@/components/NavTabs";
import GaugesRail from "@/components/GaugesRail";
import ProcessRail from "@/components/ProcessRail";
import {
  ProofDetailRail,
  ReconciliationDetailRail,
} from "@/components/engagement/EngagementRails";
import { useProgramStore } from "@/lib/state/programStore";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // zustand persist hydration guard: render seed state on server + first
  // client paint, then rehydrate from localStorage after mount.
  useEffect(() => {
    void useProgramStore.persist.rehydrate();
  }, []);

  return (
    <div className="wrap">
      <div className="main">
        <h1>
          Aegis Workbench <span>·</span> program design as pipeline
        </h1>
        <p className="sub">
          Scope determines the program; the program determines the datasets;
          the datasets determine what the Sentinels do. Each stage feeds the
          next — the Overlord console at the end is generated, not authored.
        </p>
        <NavTabs />
        {children}
      </div>
      <div className="rail">
        {pathname?.startsWith("/process") ? (
          <ProcessRail />
        ) : /^\/reconciliation\/[^/]+/.test(pathname ?? "") ? (
          <ReconciliationDetailRail />
        ) : /^\/proof\/[^/]+/.test(pathname ?? "") ? (
          <ProofDetailRail />
        ) : (
          <GaugesRail />
        )}
      </div>
    </div>
  );
}
