"use client";

import { BaseEdge, EdgeLabelRenderer, type Edge, type EdgeProps } from "@xyflow/react";
import type { LaneEdgeModel, LaneGate } from "./laneModel";
import styles from "./flow.module.css";

export type LaneFlowEdge = Edge<
  {
    model: LaneEdgeModel;
    overlay: boolean;
    selectedGateId: string | null;
    onGateClick: (gateId: string) => void;
  },
  "lane"
>;

/** Cubic bezier point at t — we own the path, so we can place things ON it. */
function bez(t: number, p0: number, p1: number, p2: number, p3: number): number {
  const u = 1 - t;
  return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3;
}

function gateStateOf(gate: LaneGate): string {
  if (gate.kind === "compile-error") return "E117";
  return gate.verdict?.state ?? "";
}

const LAMP_GLYPH: Record<string, string> = {
  PASS: "✓", // ✓
  FAIL: "×", // ×
  UNKNOWN: "?",
  EXCEPTION: "◇", // ◇
  EXCLUDED: "−", // −
};

export function LaneEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
}: EdgeProps<LaneFlowEdge>) {
  if (!data) return null;
  const { model, overlay, selectedGateId, onGateClick } = data;

  const dx = Math.max(Math.abs(targetX - sourceX) * 0.42, 36);
  const c1x = sourceX + dx;
  const c2x = targetX - dx;
  const path = `M ${sourceX},${sourceY} C ${c1x},${sourceY} ${c2x},${targetY} ${targetX},${targetY}`;
  const at = (t: number) => ({
    x: bez(t, sourceX, c1x, c2x, targetX),
    y: bez(t, sourceY, sourceY, targetY, targetY),
  });

  const isFanOut = model.eventKind === "fan-out" || model.excluded;
  const gatePos = at(0.5);
  const kindPos = at(isFanOut ? 0.32 : 0.22);
  // Fan-out edges are long — hang the quantity on the path; the two trunk
  // edges are short, so stack the quantity above their gate instead.
  const pillPos = isFanOut
    ? (() => {
        const p = at(0.68);
        return { x: p.x, y: p.y - 16 };
      })()
    : { x: gatePos.x + (model.edgeId === "okta-fanout" ? 58 : 0), y: gatePos.y - 58 };

  const gate = model.gate;
  const state = gate ? gateStateOf(gate) : "";
  const broken = gate?.kind === "compile-error";
  const gateColorClass = broken
    ? styles.gateFAIL
    : gate
      ? styles[`gate${state}`] ?? ""
      : "";

  const stateVar = gate
    ? broken
      ? "--v-fail"
      : state === "PASS"
        ? "--v-pass"
        : state === "FAIL"
          ? "--v-fail"
          : state === "UNKNOWN"
            ? "--v-unknown"
            : state === "EXCEPTION"
              ? "--v-exception"
              : "--v-excluded"
    : null;
  const tint = stateVar
    ? (mix: number) =>
        `color-mix(in srgb, var(${stateVar}) ${Math.round(mix * 100)}%, #3a4059)`
    : null;

  const weight = overlay && model.cohort.weight != null
    ? 2 + model.cohort.weight * 0.09
    : 1.6;

  return (
    <>
      {model.excluded ? (
        <BaseEdge
          id={id}
          path={path}
          className={styles.edgeExcluded}
          style={{ strokeWidth: weight }}
          interactionWidth={18}
        />
      ) : (
        <>
          <BaseEdge
            id={`${id}-base`}
            path={path}
            className={styles.edgeBase}
            style={{ strokeWidth: weight, ...(tint ? { stroke: tint(0.35) } : {}) }}
            interactionWidth={18}
          />
          <path
            d={path}
            className={styles.edgeDash}
            style={{ strokeWidth: Math.min(weight, 2.4), ...(tint ? { stroke: tint(0.7) } : {}) }}
          />
        </>
      )}
      <EdgeLabelRenderer>
        {/* event-kind label, on the path near the source */}
        <span
          className={styles.edgeKind}
          style={{ left: kindPos.x, top: kindPos.y }}
        >
          {model.eventKind}
        </span>

        {/* cohort-conservation overlay quantity, on the path near the target */}
        {overlay && (
          <span
            className={styles.cohortPill}
            style={{ left: pillPos.x, top: pillPos.y }}
          >
            {model.cohort.label}
          </span>
        )}

        {/* the gate — a control point interrupting the flow */}
        {gate && (
          <button
            type="button"
            className={[
              styles.gate,
              gateColorClass,
              broken ? styles.gateBroken : "",
              selectedGateId === gate.gateId ? styles.gateSelected : "",
            ].join(" ")}
            style={{
              left: gatePos.x,
              top: gatePos.y,
              position: "absolute",
              transform: "translate(-50%, -50%)",
            }}
            onClick={(ev) => {
              ev.stopPropagation();
              onGateClick(gate.gateId);
            }}
            aria-label={`Gate ${gate.label} — ${broken ? "E117 did not compile" : state}`}
          >
            <span className={styles.gateBar}>
              <span className={styles.gateLamp}>
                {broken ? "!" : LAMP_GLYPH[state] ?? ""}
              </span>
            </span>
            <span className={styles.gateLabel}>
              {broken ? (
                <span className={styles.ecodeTag}>E117</span>
              ) : (
                <>
                  <span className={styles.gateId}>
                    {gate.label} · {gate.verdict?.assertion_ref}
                  </span>
                  <span className={styles.gateState}>{state}</span>
                </>
              )}
            </span>
            <span className={styles.gateTip} role="tooltip">
              <span className={styles.gateTipHead}>
                {broken
                  ? `E117 · ${gate.error?.claim_ref}`
                  : `${gate.verdict?.assertion_ref} · ${state}`}
              </span>
              {gate.summary}
            </span>
          </button>
        )}
      </EdgeLabelRenderer>
    </>
  );
}
