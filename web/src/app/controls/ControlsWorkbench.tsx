"use client";

import { useState } from "react";
import Link from "next/link";
import {
  GaugeList,
  sectionsFromSeed,
} from "@/components/GaugesRail/GaugesRail";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import { StageTabs } from "@/components/StageTabs/StageTabs";
import type {
  ControlFunction,
  ControlNature,
  ControlsSeed,
  GaugesSeed,
  ScopeSeed,
  SeedControl,
  SeedSystem,
} from "@/data";
import styles from "./controls.module.css";

/* ------------------------------------------------------------------ */
/* State                                                               */
/* ------------------------------------------------------------------ */

interface ControlUiState {
  nature: ControlNature;
  fn: ControlFunction;
  compensating: boolean;
  /** SeedSystem ids the control is mapped over. */
  systems: string[];
}

type ControlsState = Record<string, ControlUiState>;

function initialControls(controls: SeedControl[]): ControlsState {
  const state: ControlsState = {};
  for (const control of controls) {
    state[control.id] = {
      nature: control.nature,
      fn: control.function,
      compensating: control.compensating,
      systems: [...control.systems],
    };
  }
  return state;
}

/** Domain order = first appearance in the seed. All domains start open
 * (diverging from the prototype's first-two) so every seeded control
 * renders in the built page; collapsing stays available per domain. */
function initialOpenDomains(domains: string[]): Record<string, boolean> {
  const state: Record<string, boolean> = {};
  for (const domain of domains) state[domain] = true;
  return state;
}

/* ------------------------------------------------------------------ */
/* Segmented classification controls                                   */
/* ------------------------------------------------------------------ */

const NATURE_OPTIONS: { value: ControlNature; text: string }[] = [
  { value: "cfg", text: "CONFIGURABLE" },
  { value: "auto", text: "AUTOMATED" },
  { value: "manual", text: "MANUAL" },
];

const FUNCTION_OPTIONS: { value: ControlFunction; text: string }[] = [
  { value: "prev", text: "PREVENTATIVE" },
  { value: "det", text: "DETECTIVE" },
];

const NATURE_SEL: Record<ControlNature, string> = {
  cfg: styles.selCfg ?? "",
  auto: styles.selAuto ?? "",
  manual: styles.selManual ?? "",
};

const FUNCTION_SEL: Record<ControlFunction, string> = {
  prev: styles.selPrev ?? "",
  det: styles.selDet ?? "",
};

function Seg<T extends string>({
  options,
  value,
  selClasses,
  label,
  onChange,
}: {
  options: { value: T; text: string }[];
  value: T;
  selClasses: Record<T, string>;
  label: string;
  onChange: (value: T) => void;
}) {
  return (
    <div className={styles.seg} role="group" aria-label={label}>
      {options.map((option) => {
        const selected = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            className={
              selected
                ? `${styles.segBtn} ${selClasses[option.value]}`
                : styles.segBtn
            }
            aria-pressed={selected}
            onClick={() => onChange(option.value)}
          >
            {option.text}
          </button>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* One control card                                                    */
/* ------------------------------------------------------------------ */

function ControlCard({
  control,
  state,
  systems,
  onNature,
  onFunction,
  onCompensating,
  onToggleSystem,
}: {
  control: SeedControl;
  state: ControlUiState;
  systems: SeedSystem[];
  onNature: (value: ControlNature) => void;
  onFunction: (value: ControlFunction) => void;
  onCompensating: () => void;
  onToggleSystem: (systemId: string) => void;
}) {
  const datasetCount = control.datasets.length;
  return (
    <div className={styles.ctl}>
      <div className={styles.ctlHead}>
        <span className={styles.code}>{control.id}</span>
        <b className={styles.ctlName}>{control.name}</b>
        {state.compensating ? (
          <span className={styles.compBadge}>COMPENSATING</span>
        ) : null}
      </div>
      <p className={styles.ctlDesc}>{control.description}</p>
      <div className={styles.ctlRow}>
        <Seg
          options={NATURE_OPTIONS}
          value={state.nature}
          selClasses={NATURE_SEL}
          label={`Nature — ${control.id}`}
          onChange={onNature}
        />
        <Seg
          options={FUNCTION_OPTIONS}
          value={state.fn}
          selClasses={FUNCTION_SEL}
          label={`Function — ${control.id}`}
          onChange={onFunction}
        />
        <button
          type="button"
          className={
            state.compensating ? `${styles.comp} ${styles.compOn}` : styles.comp
          }
          aria-pressed={state.compensating}
          aria-label={`Compensating control — ${control.id}`}
          onClick={onCompensating}
        >
          COMP
        </button>
      </div>
      <div
        className={styles.chips}
        role="group"
        aria-label={`Systems mapped — ${control.id}`}
      >
        {systems.map((system) => {
          const on = state.systems.includes(system.id);
          const outOfScope = system.scope !== "in";
          const className = [
            styles.chip,
            on ? styles.chipOn : "",
            outOfScope ? styles.chipDis : "",
          ]
            .filter(Boolean)
            .join(" ");
          return (
            <button
              key={system.id}
              type="button"
              className={className}
              aria-pressed={on}
              disabled={outOfScope}
              title={outOfScope ? "not in scope" : undefined}
              onClick={() => onToggleSystem(system.id)}
            >
              {system.name}
              {outOfScope && on ? " ⚠" : ""}
            </button>
          );
        })}
      </div>
      <p className={styles.dsLink}>
        {datasetCount > 0 ? (
          <Link href="/datasets">
            {datasetCount} dataset{datasetCount > 1 ? "s" : ""} →
          </Link>
        ) : (
          <span className={styles.noDs}>
            no dataset defined — untestable as designed
          </span>
        )}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Stage 2 — the control library                                       */
/* ------------------------------------------------------------------ */

export function ControlsWorkbench({
  seed,
  scope,
  gauges,
}: {
  seed: ControlsSeed;
  scope: ScopeSeed;
  gauges: GaugesSeed;
}) {
  const domains: string[] = [];
  for (const control of seed.controls) {
    if (!domains.includes(control.domain)) domains.push(control.domain);
  }

  const [controls, setControls] = useState<ControlsState>(() =>
    initialControls(seed.controls),
  );
  const [openDomains, setOpenDomains] = useState<Record<string, boolean>>(() =>
    initialOpenDomains(domains),
  );

  const setControl = (
    id: string,
    update: (c: ControlUiState) => ControlUiState,
  ) =>
    setControls((prev) => {
      const current = prev[id];
      return current ? { ...prev, [id]: update(current) } : prev;
    });

  const toggleDomain = (domain: string) =>
    setOpenDomains((prev) => ({ ...prev, [domain]: !(prev[domain] ?? false) }));

  const toggleSystem = (id: string, systemId: string) =>
    setControl(id, (c) => ({
      ...c,
      systems: c.systems.includes(systemId)
        ? c.systems.filter((s) => s !== systemId)
        : [...c.systems, systemId],
    }));

  /* -- posture gauges (live from classification state) -------------- */

  const stateOf = (control: SeedControl): ControlUiState =>
    controls[control.id] ?? {
      nature: control.nature,
      fn: control.function,
      compensating: control.compensating,
      systems: control.systems,
    };

  const total = seed.controls.length;
  const cfgPreventative = seed.controls.filter((control) => {
    const state = stateOf(control);
    return state.nature === "cfg" && state.fn === "prev";
  }).length;
  const manualCount = seed.controls.filter(
    (control) => stateOf(control).nature === "manual",
  ).length;
  const withoutDataset = seed.controls.filter(
    (control) => control.datasets.length === 0,
  ).length;

  const gaugeSections = sectionsFromSeed(gauges, {
    "controls.cfgPreventativeShare":
      total > 0 ? Math.round((100 * cfgPreventative) / total) : 0,
    "controls.manualCount": manualCount,
    "controls.withoutDataset": withoutDataset,
  });

  /* -- render ------------------------------------------------------- */

  const rail = (
    <>
      <GaugeList sections={gaugeSections} />
      <p className={styles.railNote}>
        Posture responds live to classification. Manual controls are the
        automation backlog; a control with no dataset is untestable as
        designed.
      </p>
    </>
  );

  return (
    <RailLayout rail={rail} railLabel="Control posture">
      <div className={styles.main}>
        <StageTabs current={2} />
        <h1 className={styles.h1}>
          Control library <span className={styles.h1Dot}>·</span> classify and
          map
        </h1>
        <p className={styles.sub}>
          Seeded from the Aegis testing matrix. Classify each control&apos;s
          nature (configurable · automated · manual) and function
          (preventative · detective), flag compensating controls, and map the
          in-scope systems it operates over. The posture gauges on the right
          respond live.
        </p>
        <p className={styles.hint}>
          Out-of-scope and unresolved systems are disabled for mapping — an
          unknown system taints every control mapped to it.
        </p>
        {domains.map((domain) => {
          const domainControls = seed.controls.filter(
            (control) => control.domain === domain,
          );
          const cfg = domainControls.filter(
            (control) => stateOf(control).nature === "cfg",
          ).length;
          const manual = domainControls.filter(
            (control) => stateOf(control).nature === "manual",
          ).length;
          const auto = domainControls.length - cfg - manual;
          const open = openDomains[domain] ?? false;
          return (
            <section key={domain} className={styles.dom}>
              <button
                type="button"
                className={styles.domHead}
                aria-expanded={open}
                onClick={() => toggleDomain(domain)}
              >
                <b className={styles.domName}>{domain}</b>
                <span className={styles.domStats}>
                  <i className={styles.statCfg}>{cfg} cfg</i> · {auto} auto ·{" "}
                  <i className={styles.statMan}>{manual} manual</i>
                </span>
              </button>
              {open ? (
                <div className={styles.domBody}>
                  {domainControls.map((control) => (
                    <ControlCard
                      key={control.id}
                      control={control}
                      state={stateOf(control)}
                      systems={scope.systems}
                      onNature={(value) =>
                        setControl(control.id, (c) => ({ ...c, nature: value }))
                      }
                      onFunction={(value) =>
                        setControl(control.id, (c) => ({ ...c, fn: value }))
                      }
                      onCompensating={() =>
                        setControl(control.id, (c) => ({
                          ...c,
                          compensating: !c.compensating,
                        }))
                      }
                      onToggleSystem={(systemId) =>
                        toggleSystem(control.id, systemId)
                      }
                    />
                  ))}
                </div>
              ) : null}
            </section>
          );
        })}
      </div>
    </RailLayout>
  );
}
