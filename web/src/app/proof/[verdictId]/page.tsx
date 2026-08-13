"use client";

/* The proof graph: ten-stage left-to-right lineage — commitment →
 * requirement → claim → population → source → reconciliation → contract
 * → snapshot → assertion → verdict — every arrow typed. CSS grid of
 * stage columns with an absolutely-positioned SVG overlay drawing the
 * edges (relation labels in 9px mono on the path); node positions
 * measured via ResizeObserver. Clicking a node opens the NodeInspector
 * in the rail; the population node embeds the shared WhyCompletePanel. */

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { PROOF_NODE_KINDS } from "@/lib/types/artifacts";
import type { ProofNode } from "@/lib/types/artifacts";
import { loadEngagement, proofGraphFor, verdictById } from "@/lib/data/engagement";
import { useEngagementStore } from "@/lib/state/engagementStore";
import { VerdictBadge } from "@/components/engagement/Badges";
import SchemaDriftBanner from "@/components/engagement/SchemaDriftBanner";
import styles from "./Proof.module.css";

interface EdgeLine {
  key: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  relation: string;
}

const KIND_CLASS: Record<string, string> = {
  commitment: styles.kCommitment,
  requirement: styles.kRequirement,
  claim: styles.kClaim,
  population: styles.kPopulation,
  source: styles.kSource,
  reconciliation: styles.kReconciliation,
  contract: styles.kContract,
  snapshot: styles.kSnapshot,
};

function shortText(node: ProofNode): string {
  const head = node.label.split("—")[0].trim();
  return head.length > 26 ? head.slice(0, 24) + "…" : head;
}

export default function ProofPage() {
  const params = useParams<{ verdictId: string }>();
  const verdictId = decodeURIComponent(params?.verdictId ?? "");
  const load = loadEngagement();
  const graph = proofGraphFor(load, verdictId);
  const verdict = verdictById(load, verdictId);

  const selectedNodeId = useEngagementStore((s) => s.selectedProofNodeId);
  const selectProofNode = useEngagementStore((s) => s.selectProofNode);

  const contentRef = useRef<HTMLDivElement | null>(null);
  const nodeEls = useRef<Map<string, HTMLElement>>(new Map());
  const [lines, setLines] = useState<EdgeLine[]>([]);
  const [svgSize, setSvgSize] = useState({ w: 0, h: 0 });

  // Reset inspector focus when landing on a new verdict's lineage.
  useEffect(() => {
    selectProofNode(null);
  }, [verdictId, selectProofNode]);

  const measure = useCallback(() => {
    const content = contentRef.current;
    if (!content || !graph) return;
    const cRect = content.getBoundingClientRect();
    const next: EdgeLine[] = [];
    for (const e of graph.edges) {
      const a = nodeEls.current.get(e.from);
      const b = nodeEls.current.get(e.to);
      if (!a || !b) continue;
      const ra = a.getBoundingClientRect();
      const rb = b.getBoundingClientRect();
      next.push({
        key: `${e.from}→${e.to}`,
        x1: ra.right - cRect.left,
        y1: ra.top + ra.height / 2 - cRect.top,
        x2: rb.left - cRect.left,
        y2: rb.top + rb.height / 2 - cRect.top,
        relation: e.relation,
      });
    }
    setLines(next);
    setSvgSize({ w: content.scrollWidth, h: content.scrollHeight });
  }, [graph]);

  useLayoutEffect(() => {
    measure();
    const ro = new ResizeObserver(() => measure());
    if (contentRef.current) ro.observe(contentRef.current);
    nodeEls.current.forEach((el) => ro.observe(el));
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [measure]);

  const setNodeRef = (id: string) => (el: HTMLButtonElement | null) => {
    if (el) nodeEls.current.set(id, el);
    else nodeEls.current.delete(id);
  };

  if (!graph) {
    return (
      <div>
        <SchemaDriftBanner drift={load.drift} />
        <p className="sub">
          {verdict ? (
            <>
              Verdict <code>{verdictId}</code> ({verdict.state} on{" "}
              {verdict.assertion_ref}) has no lineage artifact in the mock
              bundle — the full ten-stage proof graph ships for the TIMING FAIL
              (<Link href="/proof/vr-am06-b">vr-am06-b</Link>).
            </>
          ) : (
            <>
              No verdict <code>{verdictId}</code> in the engagement bundle.{" "}
              <Link href="/verdicts">Back to verdicts.</Link>
            </>
          )}
        </p>
      </div>
    );
  }

  return (
    <div>
      <SchemaDriftBanner drift={load.drift} />
      <div className={styles.head}>
        <div>
          <h2 className={styles.title}>
            Proof lineage <span>·</span> {verdictId}
          </h2>
          <p className={styles.sub}>
            Every arrow is typed. Read left to right: the commitment imposes an
            obligation, mechanized as a claim over a derived population;
            reconciled sources ground a quality contract; the WORM snapshot
            supports a typed assertion; the evaluator emits the verdict. Click
            any node to expand it in the rail.
          </p>
        </div>
        <Link href="/verdicts" className={styles.back}>
          ← verdicts
        </Link>
      </div>

      <div className={styles.scroll}>
        <div className={styles.content} ref={contentRef}>
          <svg
            className={styles.overlay}
            width={svgSize.w}
            height={svgSize.h}
            aria-hidden="true"
          >
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 8 8"
                refX="7"
                refY="4"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M0,0.5 L7.5,4 L0,7.5" fill="none" stroke="#63667c" strokeWidth="1.2" />
              </marker>
            </defs>
            {lines.map((l) => {
              const long = l.x2 - l.x1 > 300;
              const bow = long ? 74 : 0;
              const c1x = l.x1 + Math.min(56, (l.x2 - l.x1) / 2);
              const c2x = l.x2 - Math.min(56, (l.x2 - l.x1) / 2);
              const d = `M ${l.x1} ${l.y1} C ${c1x} ${l.y1 + bow}, ${c2x} ${l.y2 + bow}, ${l.x2} ${l.y2}`;
              const mx = (l.x1 + l.x2) / 2;
              const my = (l.y1 + l.y2) / 2 + bow * 0.72;
              return (
                <g key={l.key}>
                  <path d={d} className={styles.edge} markerEnd="url(#arrow)" />
                  <text x={mx} y={my - 5} className={styles.edgeLabel} textAnchor="middle">
                    {l.relation}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className={styles.grid}>
            {PROOF_NODE_KINDS.map((kind) => {
              const nodes = graph.nodes.filter((n) => n.kind === kind);
              return (
                <div key={kind} className={styles.col}>
                  <div className={styles.colHead}>{kind}</div>
                  <div className={styles.colNodes}>
                    {nodes.map((n) => {
                      const sel = selectedNodeId === n.node_id;
                      if (n.kind === "verdict" && verdict) {
                        return (
                          <button
                            key={n.node_id}
                            ref={setNodeRef(n.node_id)}
                            className={`${styles.verdictNode} ${sel ? styles.sel : ""}`}
                            onClick={() => selectProofNode(sel ? null : n.node_id)}
                            data-node={n.node_id}
                          >
                            <VerdictBadge state={verdict.state} size="lg" />
                            <span className={styles.nl}>{n.label}</span>
                          </button>
                        );
                      }
                      if (n.kind === "assertion") {
                        return (
                          <button
                            key={n.node_id}
                            ref={setNodeRef(n.node_id)}
                            className={`${styles.diamondWrap} ${sel ? styles.sel : ""}`}
                            onClick={() => selectProofNode(sel ? null : n.node_id)}
                            data-node={n.node_id}
                          >
                            <span className={styles.diamond}>
                              <i>{n.ref}</i>
                            </span>
                            <span className={styles.nl}>{n.label}</span>
                          </button>
                        );
                      }
                      return (
                        <button
                          key={n.node_id}
                          ref={setNodeRef(n.node_id)}
                          className={`${styles.node} ${KIND_CLASS[n.kind] ?? ""} ${sel ? styles.sel : ""}`}
                          onClick={() => selectProofNode(sel ? null : n.node_id)}
                          data-node={n.node_id}
                        >
                          <span className={styles.bubble}>{shortText(n)}</span>
                          <span className={styles.nl}>{n.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
