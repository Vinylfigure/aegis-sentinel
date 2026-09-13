"use client";

/* Proof-lineage canvas — the SAME visual system as the lane canvas
 * (one node/edge language across the app), laid out as a serpentine:
 * commitment → … → population → sources ↓ reconciliation ← … ← verdict. */

import { useMemo } from "react";
import {
  Background,
  BackgroundVariant,
  BaseEdge,
  EdgeLabelRenderer,
  Handle,
  Position,
  ReactFlow,
  ReactFlowProvider,
  getBezierPath,
  type Edge,
  type EdgeProps,
  type EdgeTypes,
  type Node,
  type NodeProps,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { ProofGraph, ProofNode as ProofNodeModel } from "@/lib/types/artifacts";
import styles from "./flow.module.css";

type ProofFlowNode = Node<{ model: ProofNodeModel }, "proof">;
type ProofFlowEdge = Edge<{ relation: string }, "proofEdge">;

function ProofNodeComponent({ data }: NodeProps<ProofFlowNode>) {
  const { model } = data;
  const isVerdict = model.kind === "verdict";
  return (
    <div className={`${styles.proofNode} ${isVerdict ? styles.proofVerdictNode : ""}`}>
      <Handle id="l" type="target" position={Position.Left} className={styles.handle} />
      <Handle id="t" type="target" position={Position.Top} className={styles.handle} />
      <Handle id="r2" type="target" position={Position.Right} className={styles.handle} />
      <div className={styles.proofKind}>{model.kind}</div>
      <div className={styles.proofLabel}>{model.label}</div>
      <div className={styles.proofRef}>{model.ref}</div>
      <Handle id="r" type="source" position={Position.Right} className={styles.handle} />
      <Handle id="b" type="source" position={Position.Bottom} className={styles.handle} />
      <Handle id="l2" type="source" position={Position.Left} className={styles.handle} />
    </div>
  );
}

function ProofEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps<ProofFlowEdge>) {
  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    curvature: 0.3,
  });
  return (
    <>
      <BaseEdge id={`${id}-base`} path={path} className={styles.edgeBase} style={{ strokeWidth: 1.6 }} />
      <path d={path} className={styles.edgeDash} style={{ strokeWidth: 1.8 }} />
      <EdgeLabelRenderer>
        <span className={styles.relationLabel} style={{ left: labelX, top: labelY }}>
          {data?.relation}
        </span>
      </EdgeLabelRenderer>
    </>
  );
}

const nodeTypes: NodeTypes = { proof: ProofNodeComponent };
const edgeTypes: EdgeTypes = { proofEdge: ProofEdgeComponent };

/* Hand-tuned serpentine slots by node kind (the lineage is small). */
const SLOTS: Record<string, { x: number; y: number }> = {
  commitment: { x: 0, y: 0 },
  requirement: { x: 340, y: 0 },
  claim: { x: 680, y: 0 },
  population: { x: 1020, y: 0 },
  source: { x: 1370, y: -60 }, // stacked by index (+150 each)
  reconciliation: { x: 1370, y: 350 },
  contract: { x: 1000, y: 350 },
  snapshot: { x: 660, y: 350 },
  assertion: { x: 330, y: 350 },
  verdict: { x: 0, y: 350 },
};

/** Pick handles so the serpentine flows visually L→R, down, R→L. */
function handlesFor(
  fromKind: string,
  toKind: string
): { sourceHandle: "r" | "b"; targetHandle: "l" | "t" } {
  const topRow = ["commitment", "requirement", "claim", "population"];
  const bottomRow = ["reconciliation", "contract", "snapshot", "assertion", "verdict"];
  if (fromKind === "source" && toKind === "reconciliation")
    return { sourceHandle: "b", targetHandle: "t" };
  if (topRow.includes(fromKind) && toKind === "source")
    return { sourceHandle: "r", targetHandle: "l" };
  if (topRow.includes(fromKind) && bottomRow.includes(toKind))
    return { sourceHandle: "b", targetHandle: "t" };
  if (bottomRow.includes(fromKind) && bottomRow.includes(toKind))
    return { sourceHandle: "b", targetHandle: "t" }; // unused fallback
  return { sourceHandle: "r", targetHandle: "l" };
}

export default function ProofCanvas({ graph }: { graph: ProofGraph }) {
  const { nodes, edges } = useMemo(() => {
    const kindCount: Record<string, number> = {};
    const kindOf: Record<string, string> = {};
    const nodes: ProofFlowNode[] = graph.nodes.map((n) => {
      const idx = kindCount[n.kind] ?? 0;
      kindCount[n.kind] = idx + 1;
      kindOf[n.node_id] = n.kind;
      const slot = SLOTS[n.kind] ?? { x: 0, y: 700 };
      return {
        id: n.node_id,
        type: "proof",
        position: { x: slot.x, y: slot.y + (n.kind === "source" ? idx * 165 : 0) },
        data: { model: n },
        draggable: false,
        connectable: false,
        selectable: false,
      };
    });

    /* bottom row flows right→left: rec → eqc → snap → assert → verdict.
     * Those edges connect left side of source to right side of target. */
    const bottomRow = ["reconciliation", "contract", "snapshot", "assertion", "verdict"];
    const edges: ProofFlowEdge[] = graph.edges.map((e) => {
      const fromKind = kindOf[e.from];
      const toKind = kindOf[e.to];
      let sourceHandle: string;
      let targetHandle: string;
      if (bottomRow.includes(fromKind) && bottomRow.includes(toKind)) {
        // right-to-left leg — leave from the left, arrive at the right
        sourceHandle = "l2";
        targetHandle = "r2";
      } else {
        const h = handlesFor(fromKind, toKind);
        sourceHandle = h.sourceHandle;
        targetHandle = h.targetHandle;
      }
      return {
        id: `${e.from}-${e.to}`,
        type: "proofEdge",
        source: e.from,
        target: e.to,
        sourceHandle,
        targetHandle,
        data: { relation: e.relation },
      };
    });
    return { nodes, edges };
  }, [graph]);

  return (
    <div style={{ height: "62vh", minHeight: 520 }} className="card">
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.1, maxZoom: 1 }}
          minZoom={0.35}
          maxZoom={1.6}
          nodesDraggable={false}
          nodesConnectable={false}
          proOptions={{ hideAttribution: true }}
          style={{ background: "var(--bg0)", borderRadius: "var(--radius-m)" }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={26}
            size={1.4}
            color="var(--grid-dot)"
          />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}
