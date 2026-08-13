"use client";

import { useCallback, useMemo, useState } from "react";
import {
  Background,
  BackgroundVariant,
  ReactFlow,
  ReactFlowProvider,
  type NodeTypes,
  type EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { loadEngagement } from "@/lib/data/engagement";
import { detectionRate } from "@/lib/data/mutations";
import { verdictCounts } from "@/lib/data/engagement";
import { buildLaneModel, JUNCTION_ID, LANE_LAYOUT } from "./laneModel";
import { SystemNode, JunctionNode, type SystemFlowNode, type JunctionFlowNode } from "./SystemNode";
import { LaneEdge, type LaneFlowEdge } from "./LaneEdge";
import HeaderStrip from "./HeaderStrip";
import InspectorDrawer from "@/components/inspector/InspectorDrawer";
import type { LaneSelection } from "@/components/inspector/InspectorDrawer";
import styles from "./flow.module.css";

const nodeTypes: NodeTypes = { system: SystemNode, junction: JunctionNode };
const edgeTypes: EdgeTypes = { lane: LaneEdge };

export default function FlowWorkbench() {
  const load = useMemo(() => loadEngagement(), []);
  const model = useMemo(() => buildLaneModel(load), [load]);
  const counts = useMemo(() => verdictCounts(load), [load]);
  const detection = useMemo(() => detectionRate(load), [load]);

  const [selection, setSelection] = useState<LaneSelection>(null);
  const [overlay, setOverlay] = useState(false);

  const onGateClick = useCallback(
    (gateId: string) => setSelection({ kind: "gate", gateId }),
    []
  );

  const nodes = useMemo(() => {
    const sel = selection?.kind === "node" ? selection.systemId : null;
    const systemNodes: SystemFlowNode[] = Object.values(model.systems).map((s) => ({
      id: s.systemId,
      type: "system",
      position: LANE_LAYOUT[s.systemId],
      data: { system: s, selected: sel === s.systemId },
      draggable: false,
      connectable: false,
    }));
    const junction: JunctionFlowNode = {
      id: JUNCTION_ID,
      type: "junction",
      position: LANE_LAYOUT[JUNCTION_ID],
      data: {},
      draggable: false,
      connectable: false,
      selectable: false,
    };
    return [...systemNodes, junction];
  }, [model, selection]);

  const edges = useMemo<LaneFlowEdge[]>(
    () =>
      model.edges.map((e) => ({
        id: e.edgeId,
        type: "lane",
        source: e.source,
        target: e.target,
        data: {
          model: e,
          overlay,
          selectedGateId: selection?.kind === "gate" ? selection.gateId : null,
          onGateClick,
        },
      })),
    [model, overlay, selection, onGateClick]
  );

  return (
    <div className={styles.canvasHost}>
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.1, maxZoom: 1.18 }}
          minZoom={0.45}
          maxZoom={1.75}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable
          proOptions={{ hideAttribution: true }}
          onNodeClick={(_, n) => {
            if (n.type === "system") setSelection({ kind: "node", systemId: n.id });
          }}
          onEdgeClick={(_, e) => setSelection({ kind: "edge", edgeId: e.id })}
          onPaneClick={() => setSelection(null)}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={26}
            size={1.4}
            color="var(--grid-dot)"
          />
        </ReactFlow>
      </ReactFlowProvider>

      <HeaderStrip
        manifest={load.artifacts.manifest}
        counts={counts}
        detection={detection}
        overlay={overlay}
        onToggleOverlay={() => setOverlay((v) => !v)}
      />

      {load.drift.length > 0 && (
        <div className={styles.driftStrip} role="alert">
          artifact schema drift — {load.drift.length} finding(s):{" "}
          {load.drift.slice(0, 3).join(" · ")}
        </div>
      )}

      <div className={styles.canvasHint}>
        click a gate, node, or edge to inspect · drag to pan · scroll to zoom
      </div>

      <InspectorDrawer
        load={load}
        model={model}
        selection={selection}
        onClose={() => setSelection(null)}
        onSelect={setSelection}
      />
    </div>
  );
}
