"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import type { LaneSystem } from "./laneModel";
import styles from "./flow.module.css";

export type SystemFlowNode = Node<{ system: LaneSystem; selected: boolean }, "system">;
export type JunctionFlowNode = Node<Record<string, never>, "junction">;

const GLYPHS: Record<string, React.ReactNode> = {
  hris: (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden>
      <circle cx="6" cy="5.5" r="2.6" stroke="currentColor" strokeWidth="1.4" />
      <path d="M1.8 14.2c.5-2.8 2.2-4.3 4.2-4.3s3.7 1.5 4.2 4.3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M11.5 8.2c1.7.2 3.2 1.6 3.7 4.1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M10.7 3.2a2.6 2.6 0 0 1 0 4.7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  ),
  okta: (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden>
      <circle cx="8.5" cy="8.5" r="6.2" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="8.5" cy="8.5" r="2.6" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  ),
  github: (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden>
      <circle cx="4.5" cy="3.8" r="2" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="4.5" cy="13.2" r="2" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="12.5" cy="6" r="2" stroke="currentColor" strokeWidth="1.4" />
      <path d="M4.5 5.8v5.4M12.5 8c0 2.6-2.5 3.4-6 3.7" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  ),
  gcp: (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden>
      <path d="M5 12.8a3.2 3.2 0 0 1-.4-6.4 4.4 4.4 0 0 1 8.5 1.1 2.8 2.8 0 0 1-.6 5.3H5Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  ),
  slack: (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden>
      <path d="M6 2.5v5M11 2.5v5M6 9.5v5M11 9.5v5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M2.5 6h5M9.5 6h5M2.5 11h5M9.5 11h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  ),
  "corp-it": (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden>
      <rect x="2.5" y="3" width="12" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M5.5 14h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  ),
};

export function SystemNode({ data }: NodeProps<SystemFlowNode>) {
  const { system, selected } = data;
  const pop = system.population;
  const tintClass = system.tint ? styles[`tint${system.tint}`] : "";
  const blocked = system.tint === "UNCOMPILED";

  return (
    <div
      className={[
        styles.node,
        tintClass,
        system.ghost ? styles.nodeGhost : "",
        selected ? styles.nodeSelected : "",
      ].join(" ")}
      role="button"
      aria-label={`${system.name} — ${system.descriptor}`}
    >
      <Handle type="target" position={Position.Left} className={styles.handle} />
      <div className={styles.nodeHead}>
        <span className={styles.nodeGlyph}>{GLYPHS[system.systemId]}</span>
        <div>
          <div className={styles.nodeName}>{system.name}</div>
          <div className={styles.nodeDescriptor}>{system.descriptor}</div>
        </div>
      </div>

      {pop && (
        <div className={styles.nodeBody}>
          <div className={styles.nodeRow}>
            <span>
              {pop.size != null ? (
                <span className={styles.nodeCount}>{pop.size}</span>
              ) : (
                <span className={styles.nodeCountNull}>size unknown</span>
              )}{" "}
              {pop.size != null && (pop.type === "EVENT" ? "events" : pop.type === "RELATIONSHIP" ? "joined" : "accounts")}
            </span>
            <span
              className={`${styles.ladderChip} ${blocked ? styles.ladderChipBlocked : ""}`}
            >
              {blocked ? `${pop.state} · E117` : pop.state}
            </span>
          </div>
          <div className={`${styles.nodeRow} ${styles.capRow}`}>
            {system.capabilities.length > 0 ? (
              <span className={styles.capOk}>
                {system.capabilities.length}{" "}
                {system.capabilities.length === 1 ? "capability" : "capabilities"} ·{" "}
                {system.capabilities[0].temporal.kind.toLowerCase().replace(/_/g, " ")}
                {system.capabilities[0].temporal.window_days != null &&
                  ` ${system.capabilities[0].temporal.window_days}d`}
              </span>
            ) : blocked ? (
              <span className={styles.capMissing}>capability missing: breakglass.config</span>
            ) : (
              <span>no capability entries</span>
            )}
          </div>
        </div>
      )}
      {!pop && system.ghost && (
        <div className={styles.nodeBody}>
          <div className={`${styles.nodeRow} ${styles.capRow}`}>
            <span>out of lane scope · RAT-2026-031</span>
          </div>
        </div>
      )}
      <Handle type="source" position={Position.Right} className={styles.handle} />
    </div>
  );
}

export function JunctionNode() {
  return (
    <div className={styles.junction} aria-hidden>
      <Handle type="target" position={Position.Left} className={styles.handle} />
      <Handle type="source" position={Position.Right} className={styles.handle} />
    </div>
  );
}
