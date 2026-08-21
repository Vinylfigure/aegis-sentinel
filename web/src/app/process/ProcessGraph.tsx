"use client";

import { useState } from "react";
import Link from "next/link";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import {
  compileErrorMeta,
  engagementRegistry,
  engagementVerdictRecords,
  verdictStateMeta,
} from "@/data";
import type {
  CompileError,
  ControlsSeed,
  ProcessControlPoint,
  ProcessLane,
  ProcessSeed,
  ProcessStep,
  ProcessTier,
  ScopeSeed,
  SeedControl,
  VerdictRecord,
  VerdictState,
} from "@/data";
import styles from "./process.module.css";
import {
  pointCompileErrors,
  pointVerdictRecords,
  worstOfStates,
  worstVerdictState,
} from "./verdictFusion";

/* ------------------------------------------------------------------ */
/* Derivations                                                         */
/* ------------------------------------------------------------------ */

interface PointOnFlow {
  lane: ProcessLane;
  point: ProcessControlPoint;
  /** Registry system ids flanking this point on the flow (either side
   * of the diamond), where the neighboring node resolves to one. */
  flankSystems: string[];
  /** Issue #43 — live engagement verdict records joined via the point's
   * explicit `verdictSpecIds`. Empty when the point has none wired. */
  verdictRecords: VerdictRecord[];
  /** Worst state among `verdictRecords`; null when there are none. */
  worstState: VerdictState | null;
  /** Compile-refusal errors gating this point, joined via
   * `compileErrorClaimIds`. Empty when the point has none wired. */
  compileErrors: CompileError[];
}

/** A process node key resolves to a scope-registry system when its base
 * (trailing disambiguation digits stripped — the seed reuses systems
 * across lanes as `okta`/`okta2`) is a registered system id. Actor
 * nodes (requester, developer, bot) resolve to nothing. */
function resolveSystem(
  nodeKey: string,
  systemIds: ReadonlySet<string>,
): string | null {
  const base = nodeKey.replace(/\d+$/, "");
  return systemIds.has(base) ? base : null;
}

function nearestFlank(
  sequence: ProcessStep[],
  from: number,
  dir: -1 | 1,
  systemIds: ReadonlySet<string>,
): string | null {
  for (let i = from + dir; i >= 0 && i < sequence.length; i += dir) {
    const step = sequence[i];
    if (step && step.kind === "node")
      return resolveSystem(step.node.key, systemIds);
  }
  return null;
}

/** Every control point in seed order, with its lane, flanking systems, and
 * (#43) the live verdict records / compile errors it's wired to. */
function pointsOnFlow(
  seed: ProcessSeed,
  systemIds: ReadonlySet<string>,
  verdictRecords: readonly VerdictRecord[],
  compileErrors: readonly CompileError[],
): PointOnFlow[] {
  const points: PointOnFlow[] = [];
  for (const lane of seed.lanes) {
    lane.sequence.forEach((step, index) => {
      if (step.kind !== "controlPoint") return;
      const flanks = [
        nearestFlank(lane.sequence, index, -1, systemIds),
        nearestFlank(lane.sequence, index, 1, systemIds),
      ].filter((s): s is string => s !== null);
      const records = pointVerdictRecords(step.controlPoint, verdictRecords);
      points.push({
        lane,
        point: step.controlPoint,
        flankSystems: [...new Set(flanks)],
        verdictRecords: records,
        worstState: worstVerdictState(records),
        compileErrors: pointCompileErrors(step.controlPoint, compileErrors),
      });
    });
  }
  return points;
}

/** Worst verdict state among the control points immediately flanking a
 * node in its own lane's sequence (#43) — a system's live health is the
 * worst outcome among the gates that touch it, not a property of its own. */
function nodeWorstState(
  lane: ProcessLane,
  nodeIndex: number,
  pointsById: ReadonlyMap<string, PointOnFlow>,
): VerdictState | null {
  const neighborStates: VerdictState[] = [];
  for (const dir of [-1, 1] as const) {
    const step = lane.sequence[nodeIndex + dir];
    if (step?.kind === "controlPoint") {
      const state = pointsById.get(step.controlPoint.id)?.worstState;
      if (state) neighborStates.push(state);
    }
  }
  return worstOfStates(neighborStates);
}

/** Library controls operating over every system flanking the point —
 * derived by system adjacency; the seed carries no explicit
 * point→control mapping (see the rail's derivation note). */
function relatedControls(
  flankSystems: string[],
  controls: SeedControl[],
): SeedControl[] {
  if (flankSystems.length === 0) return [];
  return controls.filter((control) =>
    flankSystems.every((system) => control.systems.includes(system)),
  );
}

/* ------------------------------------------------------------------ */
/* Class + badge maps                                                  */
/* ------------------------------------------------------------------ */

const TIER_CHIP: Record<ProcessTier, string> = {
  1: styles.chipT1 ?? "",
  2: styles.chipT2 ?? "",
  3: "",
};

const TIER_NODE: Record<ProcessTier, string> = {
  1: styles.nodeT1 ?? "",
  2: styles.nodeT2 ?? "",
  3: "",
};

/** Prototype rule: manual wins the marker color; otherwise function. */
function markerClass(point: ProcessControlPoint): string {
  if (point.nature === "manual") return styles.cpMan ?? "";
  return point.function === "prev" ? (styles.cpPrev ?? "") : (styles.cpDet ?? "");
}

const NATURE_BADGE: Record<
  ProcessControlPoint["nature"],
  { text: string; className: string }
> = {
  cfg: { text: "CONFIGURABLE", className: styles.bdCfg ?? "" },
  auto: { text: "AUTOMATED", className: styles.bdAuto ?? "" },
  manual: { text: "MANUAL", className: styles.bdMan ?? "" },
};

const FUNCTION_BADGE: Record<
  ProcessControlPoint["function"],
  { text: string; className: string }
> = {
  prev: { text: "PREVENTATIVE", className: styles.bdPrev ?? "" },
  det: { text: "DETECTIVE", className: styles.bdDet ?? "" },
};

/** #43 — verdict-state ring color, keyed by the same `tone` as
 * `verdictStateMeta` (verdicts.ts) and `/verdicts`'s section borders, so a
 * FAIL means the same red everywhere in the app. Exhaustive `Record` so a
 * sixth `VerdictState` fails `tsc` here rather than silently un-ringed. */
const VERDICT_RING: Record<VerdictState, string> = {
  FAIL: styles.ringFail ?? "",
  UNKNOWN: styles.ringUnknown ?? "",
  EXCEPTION: styles.ringException ?? "",
  EXCLUDED: styles.ringExcluded ?? "",
  PASS: styles.ringOk ?? "",
};

/* ------------------------------------------------------------------ */
/* Detail rail                                                         */
/* ------------------------------------------------------------------ */

function PointDetail({
  entry,
  controls,
}: {
  entry: PointOnFlow;
  controls: ControlsSeed;
}) {
  const { lane, point, flankSystems, verdictRecords, worstState, compileErrors } = entry;
  const nature = NATURE_BADGE[point.nature];
  const fn = FUNCTION_BADGE[point.function];
  const related = relatedControls(flankSystems, controls.controls);
  return (
    <div>
      <span className={styles.code}>{point.id}</span>
      <h3 className={styles.dtName}>{point.name}</h3>
      <p className={styles.dtLane}>
        on <b>{lane.name}</b>
      </p>
      <div className={styles.badges}>
        <span className={`${styles.bd} ${nature.className}`}>{nature.text}</span>
        <span className={`${styles.bd} ${fn.className}`}>{fn.text}</span>
      </div>
      <div className={styles.frow}>
        <span className={styles.frowLabel}>What it enforces</span>
        <div className={styles.frowBody}>{point.enforces}</div>
      </div>
      <div className={styles.frow}>
        <span className={styles.frowLabel}>Data element</span>
        <div className={styles.frowBody}>
          <b className={styles.frowStrong}>{point.dataElement}</b>
          <br />
          <code className={styles.api}>{point.api}</code>
        </div>
      </div>
      <div className={styles.frow}>
        <span className={styles.frowLabel}>Type of evidence</span>
        <div className={styles.frowBody}>{point.evidence}</div>
      </div>
      <div className={styles.frow}>
        <span className={styles.frowLabel}>Completeness &amp; accuracy</span>
        <div className={styles.frowBody}>{point.completenessAccuracy}</div>
      </div>
      {point.gap ? (
        <div className={styles.gap}>
          <b className={styles.gapTitle}>Watch</b>
          <p className={styles.gapBody}>{point.gap}</p>
        </div>
      ) : null}

      {compileErrors.length > 0 ? (
        <div className={styles.refusal}>
          <span className={styles.frowLabel}>Compile refusal on this gate</span>
          {compileErrors.map((error) => {
            const meta = compileErrorMeta(error.code);
            return (
              <div key={`${error.claim_id}:${error.code}`} className={styles.refusalBody}>
                <span className={styles.refusalCode}>{meta.code}</span>{" "}
                <b>{meta.title}</b>
                <p className={styles.refusalMsg}>{error.message}</p>
                <p className={styles.refusalConsequence}>{meta.consequence}</p>
                <code className={styles.api}>{error.claim_id}</code>
              </div>
            );
          })}
        </div>
      ) : null}

      <div className={styles.rel}>
        <span className={styles.frowLabel}>Live verdict state</span>
        {worstState ? (
          <>
            <span className={`${styles.stateChip} ${VERDICT_RING[worstState] ?? ""}`}>
              worst: {worstState}
            </span>
            {verdictRecords.map((record) => (
              <div key={record.record_id} className={styles.relCtl}>
                <span className={`${styles.stateChip} ${VERDICT_RING[record.status] ?? ""}`}>
                  {record.status}
                </span>{" "}
                <Link
                  className={styles.onwardLink}
                  href={`/proof/${encodeURIComponent(record.record_id)}`}
                >
                  {record.record_id}
                </Link>
                {record.message ? (
                  <div className={styles.relDs}>{record.message}</div>
                ) : null}
              </div>
            ))}
          </>
        ) : (
          <p className={styles.relEmpty}>
            No live verdict records are wired to this point yet.
          </p>
        )}
      </div>

      <div className={styles.rel}>
        <span className={styles.frowLabel}>
          Library controls on the flanked systems
        </span>
        {related.length > 0 ? (
          related.map((control) => {
            const datasets = control.datasets.filter((dataset) =>
              flankSystems.includes(dataset.system),
            );
            return (
              <div key={control.id} className={styles.relCtl}>
                <span className={styles.code}>{control.id}</span>{" "}
                <b className={styles.relName}>{control.name}</b>
                {datasets.map((dataset) => (
                  <div
                    key={`${dataset.system}:${dataset.artifact}`}
                    className={styles.relDs}
                  >
                    {dataset.artifact} · {controls.retrievalChannels[dataset.retrieval]}{" "}
                    · {controls.caMethods[dataset.caMethod]}
                  </div>
                ))}
              </div>
            );
          })
        ) : (
          <p className={styles.relEmpty}>
            No library control operates over the systems flanking this point.
          </p>
        )}
        <p className={styles.relNote}>
          Derived by system adjacency — the seed carries no explicit
          point→control mapping.
        </p>
      </div>

      <div className={styles.onward}>
        <span className={styles.frowLabel}>Explore</span>
        {point.links && point.links.length > 0 ? (
          point.links.map((link) => (
            <Link key={link.href} className={styles.onwardLink} href={link.href}>
              {link.label} →
            </Link>
          ))
        ) : (
          /* Honest empty state (C2): only points whose engagement artifacts
           * exist carry links in the seed — the TA lane today. */
          <span className={styles.onwardEmpty}>
            No engagement surface is wired to this point yet.
          </span>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* The graph                                                           */
/* ------------------------------------------------------------------ */

export function ProcessGraph({
  seed,
  controls,
  scope,
}: {
  seed: ProcessSeed;
  controls: ControlsSeed;
  scope: ScopeSeed;
}) {
  const systemIds: ReadonlySet<string> = new Set(
    scope.systems.map((system) => system.id),
  );
  const points = pointsOnFlow(
    seed,
    systemIds,
    engagementVerdictRecords,
    engagementRegistry.compile_errors,
  );
  const pointsById = new Map(points.map((entry) => [entry.point.id, entry]));

  /* Default selection = first control point on the flow (seed order);
   * pages built from a seed without points render the empty rail. */
  const [selectedId, setSelectedId] = useState<string | null>(
    () => points[0]?.point.id ?? null,
  );
  const selected = points.find((entry) => entry.point.id === selectedId) ?? null;

  const laneCount = seed.lanes.length;
  const stepCount = seed.lanes.reduce(
    (sum, lane) =>
      sum + lane.sequence.filter((step) => step.kind === "node").length,
    0,
  );

  const rail = (
    <>
      <h2 className={styles.railTitle}>Control point</h2>
      <div aria-live="polite">
        {selected ? (
          <PointDetail entry={selected} controls={controls} />
        ) : (
          <p className={styles.empty}>Select a diamond on any flow.</p>
        )}
      </div>
    </>
  );

  return (
    <RailLayout rail={rail} railLabel="Control point detail">
      <div className={styles.main}>
        <h1 className={styles.h1}>
          Process graph <span className={styles.h1Dot}>·</span> controls on the
          flow
        </h1>
        <p className={styles.sub}>
          Assets as nodes tinted by the data classification they carry, ITGC
          processes as left-to-right chains, and control points sitting on the
          flow between systems. Select any diamond — the rail expands it into
          nature, function, the exact data element collected, and the evidence
          type. The graph is the scope; the diamonds are the program.
        </p>

        <div className={styles.ctx}>
          <span className={styles.chip}>
            <b className={styles.chipStrong}>Product:</b> {seed.context.product}
          </span>
          {seed.context.tiers.map((tier) => (
            <span
              key={tier.id}
              className={`${styles.chip} ${TIER_CHIP[tier.id]}`}
            >
              {tier.label}
            </span>
          ))}
          <span className={styles.chip}>
            {laneCount} lanes · {stepCount} steps · {points.length} control
            points
          </span>
        </div>

        <div className={styles.legend}>
          <span className={styles.legendItem}>
            <span className={`${styles.legendSq} ${styles.legendSqP}`} />{" "}
            preventative control point
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.legendSq} ${styles.legendSqD}`} />{" "}
            detective control point
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.legendSq} ${styles.legendSqM}`} /> manual
            control point
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.legendCi} ${styles.legendCiR}`} /> node
            carries T1 data
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.legendCi} ${styles.legendCiA}`} /> T2
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.legendRing} ${styles.ringFail}`} /> live
            verdict state (worst of associated records)
          </span>
          <span className={styles.legendItem}>
            <span className={styles.legendGate}>⛔</span> claim on this gate
            doesn&apos;t compile
          </span>
        </div>

        {seed.lanes.map((lane) => (
          <section key={lane.id} className={styles.lane}>
            <div className={styles.laneHead}>
              <span className={styles.laneId}>{lane.id}</span>
              <b className={styles.laneName}>{lane.name}</b>
              <span className={styles.laneSub}>{lane.subtitle}</span>
            </div>
            <div className={styles.flow}>
              <div className={styles.chain}>
                {lane.sequence.map((step, index) => {
                  if (step.kind === "node") {
                    const liveState = nodeWorstState(lane, index, pointsById);
                    return (
                      <div
                        key={`n-${step.node.key}`}
                        className={`${styles.node} ${TIER_NODE[step.node.tier]}`}
                      >
                        <div
                          className={`${styles.bubble} ${
                            liveState ? (styles.bubbleLive ?? "") : ""
                          } ${liveState ? (VERDICT_RING[liveState] ?? "") : ""}`}
                        >
                          {step.node.label}
                          {step.node.tier < 3 ? (
                            <span className={styles.tierBadge}>
                              T{step.node.tier}
                            </span>
                          ) : null}
                        </div>
                        <div className={styles.nodeLabel}>{step.node.sublabel}</div>
                      </div>
                    );
                  }
                  const cpEntry = pointsById.get(step.controlPoint.id);
                  const hasRefusal = (cpEntry?.compileErrors.length ?? 0) > 0;
                  const worst = cpEntry?.worstState ?? null;
                  return (
                    <div key={`cp-${step.controlPoint.id}`} className={styles.edge}>
                      <span className={styles.wire} />
                      <button
                        type="button"
                        className={`${styles.cp} ${markerClass(step.controlPoint)} ${
                          selectedId === step.controlPoint.id
                            ? (styles.cpSel ?? "")
                            : ""
                        } ${worst ? (styles.cpLive ?? "") : ""} ${
                          worst ? (VERDICT_RING[worst] ?? "") : ""
                        }`}
                        aria-pressed={selectedId === step.controlPoint.id}
                        aria-label={`${step.controlPoint.id} — ${step.controlPoint.name}${
                          worst ? ` — live state ${worst}` : ""
                        }${hasRefusal ? " — compile refusal on this gate" : ""}`}
                        onClick={() => setSelectedId(step.controlPoint.id)}
                      >
                        <i className={styles.cpId}>{step.controlPoint.id}</i>
                        {hasRefusal ? (
                          <span className={styles.cpGate} aria-hidden="true">
                            ⛔
                          </span>
                        ) : null}
                      </button>
                      <span className={styles.wire} />
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        ))}
      </div>
    </RailLayout>
  );
}
