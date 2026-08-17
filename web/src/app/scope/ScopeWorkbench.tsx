"use client";

import { useState } from "react";
import {
  GaugeList,
  toneFromSeed,
  type GaugeSection,
} from "@/components/GaugesRail/GaugesRail";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import { StageTabs } from "@/components/StageTabs/StageTabs";
import type {
  GaugesSeed,
  ScopeResolution,
  ScopeSeed,
  SeedAssetLayer,
  SeedDataClass,
  SeedProduct,
  SeedSystem,
} from "@/data";
import styles from "./scope.module.css";

/* ------------------------------------------------------------------ */
/* State                                                               */
/* ------------------------------------------------------------------ */

interface ProductUiState {
  /** Product carries a commitment (checkbox in the prototype). */
  on: boolean;
  /** Card expanded to show data classes + asset inventory. */
  open: boolean;
  /** Selected data-class ids. */
  classes: string[];
  /** `${layerIndex}:${itemIndex}` → resolution; absent = "unknown". */
  items: Record<string, ScopeResolution>;
  /** Expanded asset layers, by layer index. */
  layersOpen: Record<number, boolean>;
}

type ProductsState = Record<string, ProductUiState>;
type SystemsState = Record<string, ScopeResolution>;

function initialProducts(products: SeedProduct[]): ProductsState {
  const state: ProductsState = {};
  for (const product of products) {
    state[product.id] = {
      on: product.inScope,
      open: false,
      classes: [...product.dataClasses],
      items: {},
      layersOpen: {},
    };
  }
  return state;
}

function initialSystems(systems: SeedSystem[]): SystemsState {
  const state: SystemsState = {};
  for (const system of systems) state[system.id] = system.scope;
  return state;
}

/* ------------------------------------------------------------------ */
/* Tri-state control (IN / ? / OUT) — buttons, not the prototype divs  */
/* ------------------------------------------------------------------ */

const TRI_OPTIONS: { value: ScopeResolution; text: string; label: string }[] = [
  { value: "in", text: "IN", label: "In scope" },
  { value: "unknown", text: "?", label: "Unknown" },
  { value: "out", text: "OUT", label: "Out of scope" },
];

function selClass(value: ScopeResolution) {
  if (value === "in") return styles.selIn;
  if (value === "unknown") return styles.selUnknown;
  return styles.selOut;
}

function TriControl({
  value,
  label,
  small,
  onChange,
}: {
  value: ScopeResolution;
  label: string;
  small?: boolean;
  onChange: (value: ScopeResolution) => void;
}) {
  return (
    <div
      className={small ? `${styles.tri} ${styles.triSm}` : styles.tri}
      role="group"
      aria-label={label}
    >
      {TRI_OPTIONS.map((option) => {
        const selected = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            className={
              selected ? `${styles.triBtn} ${selClass(option.value)}` : styles.triBtn
            }
            aria-pressed={selected}
            aria-label={option.label}
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
/* Product card: data classes + asset inventory (scope-tool)           */
/* ------------------------------------------------------------------ */

function ProductCard({
  product,
  state,
  dataClasses,
  layers,
  onToggleOn,
  onToggleOpen,
  onToggleClass,
  onToggleLayer,
  onSetItem,
}: {
  product: SeedProduct;
  state: ProductUiState;
  dataClasses: SeedDataClass[];
  layers: SeedAssetLayer[];
  onToggleOn: () => void;
  onToggleOpen: () => void;
  onToggleClass: (classId: string) => void;
  onToggleLayer: (layerIndex: number) => void;
  onSetItem: (key: string, value: ScopeResolution) => void;
}) {
  const expanded = state.on && state.open;
  return (
    <div className={state.on ? `${styles.prod} ${styles.prodOn}` : styles.prod}>
      <div className={styles.phead}>
        <button
          type="button"
          className={state.on ? `${styles.box} ${styles.boxOn}` : styles.box}
          aria-pressed={state.on}
          aria-label={`${product.name} carries a commitment`}
          onClick={onToggleOn}
        >
          {state.on ? "✓" : ""}
        </button>
        <button
          type="button"
          className={styles.pheadBtn}
          aria-expanded={expanded}
          onClick={onToggleOpen}
        >
          <span className={styles.ptext}>
            <span className={styles.pname}>{product.name}</span>
            <span className={styles.pdesc}>{product.description}</span>
          </span>
          <span
            className={expanded ? `${styles.chev} ${styles.chevOpen}` : styles.chev}
            aria-hidden="true"
          >
            ▶
          </span>
        </button>
      </div>
      {expanded ? (
        <div className={styles.pbody}>
          <h3 className={`${styles.step} ${styles.substep}`}>
            Data classes this product carries
          </h3>
          <div className={styles.dcGrid}>
            {dataClasses.map((dataClass) => {
              const on = state.classes.includes(dataClass.id);
              return (
                <button
                  key={dataClass.id}
                  type="button"
                  className={on ? `${styles.dc} ${styles.dcOn}` : styles.dc}
                  aria-pressed={on}
                  onClick={() => onToggleClass(dataClass.id)}
                >
                  <span className={styles.dcName}>{dataClass.name}</span>
                  <span className={styles.dcNote}>{dataClass.note}</span>
                  <span className={styles.dcTier}>{dataClass.tier}</span>
                </button>
              );
            })}
          </div>
          <h3 className={`${styles.step} ${styles.substep}`}>Asset inventory</h3>
          {layers.map((layer, layerIndex) => {
            const open = state.layersOpen[layerIndex] ?? false;
            const counts = { in: 0, unknown: 0, out: 0 };
            layer.items.forEach((_, itemIndex) => {
              counts[state.items[`${layerIndex}:${itemIndex}`] ?? "unknown"] += 1;
            });
            return (
              <div key={layer.name} className={styles.layer}>
                <button
                  type="button"
                  className={styles.lhead}
                  aria-expanded={open}
                  onClick={() => onToggleLayer(layerIndex)}
                >
                  <span className={styles.lnum}>
                    {String(layerIndex + 1).padStart(2, "0")}
                  </span>
                  <span className={styles.lname}>{layer.name}</span>
                  <span className={styles.lcount}>
                    {counts.in} in · <b>{counts.unknown} unknown</b> · {counts.out} out
                  </span>
                </button>
                {open ? (
                  <div className={styles.lbody}>
                    {layer.items.map((item, itemIndex) => {
                      const key = `${layerIndex}:${itemIndex}`;
                      return (
                        <div key={item.name} className={styles.item}>
                          <TriControl
                            value={state.items[key] ?? "unknown"}
                            label={`Scope resolution — ${item.name}`}
                            onChange={(value) => onSetItem(key, value)}
                          />
                          <div>
                            <b className={styles.itemName}>{item.name}</b>
                            <span className={styles.itemPrompt}>{item.prompt}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* The merged workbench                                                */
/* ------------------------------------------------------------------ */

export function ScopeWorkbench({
  seed,
  gauges,
}: {
  seed: ScopeSeed;
  gauges: GaugesSeed;
}) {
  const [products, setProducts] = useState<ProductsState>(() =>
    initialProducts(seed.products),
  );
  const [systems, setSystems] = useState<SystemsState>(() =>
    initialSystems(seed.systems),
  );
  const [summary, setSummary] = useState<string | null>(null);

  /* -- state updates ------------------------------------------------ */

  const setProduct = (id: string, update: (p: ProductUiState) => ProductUiState) =>
    setProducts((prev) => {
      const current = prev[id];
      return current ? { ...prev, [id]: update(current) } : prev;
    });

  const toggleOn = (id: string) =>
    setProduct(id, (p) => (p.on ? { ...p, on: false } : { ...p, on: true, open: true }));

  const toggleOpen = (id: string) =>
    setProduct(id, (p) =>
      p.on ? { ...p, open: !p.open } : { ...p, on: true, open: true },
    );

  const toggleClass = (id: string, classId: string) =>
    setProduct(id, (p) => ({
      ...p,
      classes: p.classes.includes(classId)
        ? p.classes.filter((c) => c !== classId)
        : [...p.classes, classId],
    }));

  const toggleLayer = (id: string, layerIndex: number) =>
    setProduct(id, (p) => ({
      ...p,
      layersOpen: { ...p.layersOpen, [layerIndex]: !(p.layersOpen[layerIndex] ?? false) },
    }));

  const setItem = (id: string, key: string, value: ScopeResolution) =>
    setProduct(id, (p) => ({ ...p, items: { ...p.items, [key]: value } }));

  const setSystem = (id: string, value: ScopeResolution) =>
    setSystems((prev) => ({ ...prev, [id]: value }));

  const reset = () => {
    setProducts(initialProducts(seed.products));
    setSystems(initialSystems(seed.systems));
    setSummary(null);
  };

  /* -- derived (every count computed from data + state) ------------- */

  const itemsPerProduct = seed.assetLayers.reduce(
    (total, layer) => total + layer.items.length,
    0,
  );
  const activeProducts = seed.products.filter((p) => products[p.id]?.on);

  let assetsIn = 0;
  let assetsUnknown = 0;
  let assetsOut = 0;
  for (const product of activeProducts) {
    const state = products[product.id];
    if (!state) continue;
    seed.assetLayers.forEach((layer, layerIndex) => {
      layer.items.forEach((_, itemIndex) => {
        const value = state.items[`${layerIndex}:${itemIndex}`] ?? "unknown";
        if (value === "in") assetsIn += 1;
        else if (value === "out") assetsOut += 1;
        else assetsUnknown += 1;
      });
    });
  }
  const assetsTotal = activeProducts.length * itemsPerProduct;

  const activeClasses = new Set<string>();
  for (const product of activeProducts) {
    for (const classId of products[product.id]?.classes ?? []) {
      activeClasses.add(classId);
    }
  }

  const resolutionOf = (system: SeedSystem) => systems[system.id] ?? system.scope;
  const systemCounts = { in: 0, unknown: 0, out: 0 };
  for (const system of seed.systems) systemCounts[resolutionOf(system)] += 1;

  /* -- assertion: unknown assets OR unresolved systems block it ----- */

  let assertClear = false;
  let verdict: string;
  let note: string;
  if (activeProducts.length === 0) {
    verdict = "Not started";
    note = "Select at least one product to begin.";
  } else if (assetsUnknown > 0 || systemCounts.unknown > 0) {
    verdict = "Assertion blocked";
    const parts: string[] = [];
    if (assetsUnknown > 0) {
      parts.push(
        `${assetsUnknown} of ${assetsTotal} assets unresolved across ${activeProducts.length} product${activeProducts.length > 1 ? "s" : ""}`,
      );
    }
    if (systemCounts.unknown > 0) {
      parts.push(
        `${systemCounts.unknown} system${systemCounts.unknown > 1 ? "s" : ""} unresolved in the registry`,
      );
    }
    note = `${parts.join("; ")}. Scope cannot be asserted while anything is unknown — resolve or explicitly exclude each one, with the reason.`;
  } else {
    assertClear = true;
    verdict = "Scope assertable";
    note = `${assetsIn} assets in boundary, ${assetsOut} excluded with rationale, ${systemCounts.in} systems in scope, zero unresolved. Document the exclusions — the auditor will re-litigate them annually.`;
  }

  /* -- rail gauges: seed-declared, live-computed values ------------- */

  const metricValues: Record<string, number> = {
    "scope.systems.in": systemCounts.in,
    "scope.systems.unknown": systemCounts.unknown,
  };
  const gaugeSections: GaugeSection[] = gauges.sections
    .map((section) => ({
      title: section.title,
      gauges: section.gauges.flatMap((gauge) => {
        const value = metricValues[gauge.metric];
        return value === undefined
          ? []
          : [{ label: gauge.label, value: String(value), tone: toneFromSeed(gauge.tone) }];
      }),
    }))
    .filter((section) => section.gauges.length > 0);

  /* -- scope summary (prototype export, plus the system registry) --- */

  const buildSummary = () => {
    const lines: string[] = [`SCOPE DETERMINATION — ${seed.company.name}`, ""];
    for (const product of activeProducts) {
      const state = products[product.id];
      if (!state) continue;
      lines.push(`▸ ${product.name}`);
      const classNames = state.classes.map(
        (classId) => seed.dataClasses.find((d) => d.id === classId)?.name ?? classId,
      );
      lines.push(
        `  data: ${classNames.length ? classNames.join(", ") : "— none declared —"}`,
      );
      seed.assetLayers.forEach((layer, layerIndex) => {
        const ins: string[] = [];
        const unknowns: string[] = [];
        layer.items.forEach((item, itemIndex) => {
          const value = state.items[`${layerIndex}:${itemIndex}`] ?? "unknown";
          if (value === "in") ins.push(item.name);
          if (value === "unknown") unknowns.push(item.name);
        });
        if (ins.length) lines.push(`  ${layer.name} — IN: ${ins.join("; ")}`);
        if (unknowns.length)
          lines.push(`  ${layer.name} — UNRESOLVED: ${unknowns.join("; ")}`);
      });
      lines.push("");
    }
    lines.push("SYSTEM REGISTRY");
    for (const resolution of ["in", "unknown", "out"] as const) {
      const names = seed.systems
        .filter((system) => resolutionOf(system) === resolution)
        .map((system) => system.name);
      if (names.length) {
        const heading = resolution === "unknown" ? "UNRESOLVED" : resolution.toUpperCase();
        lines.push(`  ${heading}: ${names.join("; ")}`);
      }
    }
    lines.push("", "REGIMES TRIGGERED");
    for (const regime of seed.regimes) {
      if (regime.triggeredBy.some((classId) => activeClasses.has(classId))) {
        lines.push(`  • ${regime.name} — ${regime.why}`);
      }
    }
    setSummary(lines.join("\n"));
  };

  /* -- render ------------------------------------------------------- */

  const systemCategories: string[] = [];
  for (const system of seed.systems) {
    if (!systemCategories.includes(system.category)) {
      systemCategories.push(system.category);
    }
  }

  const rail = (
    <>
      <h2 className={styles.railTitle}>Scope ledger</h2>
      <div className={styles.assert} aria-live="polite">
        <div
          className={`${styles.verdict} ${assertClear ? styles.verdictClear : styles.verdictBlocked}`}
        >
          {verdict}
        </div>
        <p className={styles.assertNote}>{note}</p>
      </div>
      <div className={styles.tallies}>
        <div className={`${styles.tally} ${styles.tallyIn}`}>
          <b className={styles.tallyValue}>{assetsIn}</b>
          <span className={styles.tallyLabel}>In</span>
        </div>
        <div className={`${styles.tally} ${styles.tallyUnknown}`}>
          <b className={styles.tallyValue}>{assetsUnknown}</b>
          <span className={styles.tallyLabel}>Unknown</span>
        </div>
        <div className={`${styles.tally} ${styles.tallyOut}`}>
          <b className={styles.tallyValue}>{assetsOut}</b>
          <span className={styles.tallyLabel}>Out</span>
        </div>
      </div>
      <GaugeList sections={gaugeSections} />
      <h2 className={styles.railTitle}>Regimes triggered</h2>
      <ul className={styles.regimes}>
        {seed.regimes.map((regime) => {
          const lit = regime.triggeredBy.some((classId) => activeClasses.has(classId));
          return (
            <li
              key={regime.id}
              className={lit ? `${styles.reg} ${styles.regLit}` : styles.reg}
            >
              <span className={styles.dot} aria-hidden="true" />
              <span>
                <b className={styles.regName}>{regime.name}</b>
                <span className={styles.regWhy}>{regime.why}</span>
              </span>
            </li>
          );
        })}
      </ul>
      <button type="button" className={styles.btn} onClick={buildSummary}>
        Build scope summary
      </button>
      <button
        type="button"
        className={`${styles.btn} ${styles.btnGhost}`}
        onClick={reset}
      >
        Reset
      </button>
      {summary !== null ? (
        <textarea
          className={styles.out}
          readOnly
          value={summary}
          aria-label="Scope summary"
        />
      ) : null}
    </>
  );

  return (
    <RailLayout rail={rail} railLabel="Scope ledger">
      <div className={styles.main}>
        <StageTabs current={1} />
        <h1 className={styles.h1}>
          Scope determination <span className={styles.h1Dot}>·</span> product-first
        </h1>
        <p className={styles.sub}>
          {seed.company.name}: scope is decided by product and by the data that
          product carries — not by framework. Select the products that carry a
          commitment, declare the data classes each one handles, then walk the
          asset stack and the system registry. Every asset and system is{" "}
          <b>in</b>, <b>unknown</b>, or <b>out</b>; unknowns block the scope
          assertion rather than defaulting into it.
        </p>

        <section aria-labelledby="step-products">
          <h2 id="step-products" className={styles.step}>
            1 · Products carrying a commitment
          </h2>
          {seed.products.map((product) => {
            const state = products[product.id];
            if (!state) return null;
            return (
              <ProductCard
                key={product.id}
                product={product}
                state={state}
                dataClasses={seed.dataClasses}
                layers={seed.assetLayers}
                onToggleOn={() => toggleOn(product.id)}
                onToggleOpen={() => toggleOpen(product.id)}
                onToggleClass={(classId) => toggleClass(product.id, classId)}
                onToggleLayer={(layerIndex) => toggleLayer(product.id, layerIndex)}
                onSetItem={(key, value) => setItem(product.id, key, value)}
              />
            );
          })}
        </section>

        <section aria-labelledby="step-systems">
          <h2 id="step-systems" className={styles.step}>
            2 · System registry
          </h2>
          <p className={styles.hint}>
            Only in-scope systems become available for control mapping
            downstream — an unknown system blocks nothing here but taints every
            control mapped to it.
          </p>
          {systemCategories.map((category) => (
            <div key={category} className={styles.syscat}>
              <h3 className={styles.syscatName}>{category}</h3>
              <div className={styles.sysgrid}>
                {seed.systems
                  .filter((system) => system.category === category)
                  .map((system) => (
                    <div key={system.id} className={styles.sys}>
                      <b className={styles.sysName}>{system.name}</b>
                      <TriControl
                        small
                        value={resolutionOf(system)}
                        label={`Scope resolution — ${system.name}`}
                        onChange={(value) => setSystem(system.id, value)}
                      />
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </section>

        <section aria-labelledby="step-ledger">
          <h2 id="step-ledger" className={styles.step}>
            3 · What the ledger says
          </h2>
          <p className={styles.subTight}>
            The regime panel on the right lights up from the data classes you
            declared, not from a framework wishlist. The assertion stays blocked
            until every asset and system is resolved — an unresolved entry is a
            gap in the population, not an absence of risk.
          </p>
        </section>
      </div>
    </RailLayout>
  );
}
