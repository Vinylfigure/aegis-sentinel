"use client";

import { useEffect, useState } from "react";
import { useProgramStore } from "@/lib/state/programStore";
import {
  datasetRegistry,
  missions,
  scopeTally,
  scopeVerdict,
  triggeredRegimes,
} from "@/lib/state/selectors";
import { ART_RET, CA, DATA_CLASSES, PRODUCTS } from "@/data/seed";
import type { CaMethod, Nature, Retrieval, ControlFn } from "@/lib/types/authoring";
import styles from "./Program.module.css";

const TABS = ["Scope", "Controls", "Datasets", "Missions"] as const;
type Tab = (typeof TABS)[number];

function ScopeSection() {
  const products = useProgramStore((s) => s.products);
  const toggleProduct = useProgramStore((s) => s.toggleProduct);
  const toggleClass = useProgramStore((s) => s.toggleClass);

  const tally = scopeTally(products);
  const verdict = scopeVerdict(tally);
  const regimes = triggeredRegimes(products);

  return (
    <div className={styles.section}>
      <div className={styles.tally}>
        <span>
          <b>{tally.activeProducts}</b> products active
        </span>
        <span>
          <b>{tally.tIn}</b> assets in
        </span>
        <span>
          <b className={tally.tUnk ? styles.tallyBlocked : undefined}>{tally.tUnk}</b>{" "}
          unresolved
        </span>
        <span>
          <b>{tally.tOut}</b> excluded
        </span>
        <span className={verdict.state === "clear" ? styles.tallyClear : styles.tallyBlocked}>
          {verdict.verdict}
        </span>
        <span className={styles.tallyNote}>{verdict.note}</span>
      </div>

      {PRODUCTS.map((p) => {
        const st = products[p.id];
        return (
          <div key={p.id} className={styles.quietCard}>
            <label className={styles.rowHead}>
              <input
                type="checkbox"
                className={styles.check}
                checked={!!st?.on}
                onChange={() => toggleProduct(p.id)}
              />
              <span>
                <span className={styles.rowTitle}>{p.name}</span>
                <span className={styles.rowSub}>{p.desc}</span>
              </span>
            </label>
            {st?.on && (
              <div className={styles.chipRow}>
                {DATA_CLASSES.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    className={`${styles.chip} ${st.cls.includes(c.id) ? styles.chipOn : ""}`}
                    onClick={() => toggleClass(p.id, c.id)}
                    title={c.note}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}

      <div className="section-label">regimes triggered by declared data</div>
      <div className={styles.quietCard}>
        {regimes.map(({ regime, lit }) => (
          <div key={regime.id} className={styles.regime}>
            <span className={`${styles.regimeDot} ${lit ? styles.regimeDotLit : ""}`} />
            <span className={`${styles.regimeName} ${lit ? styles.regimeLit : ""}`}>
              {regime.name}
            </span>
            <span className={styles.regimeWhy}>{regime.why}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ControlsSection() {
  const controls = useProgramStore((s) => s.controls);
  const openDoms = useProgramStore((s) => s.openDoms);
  const toggleDom = useProgramStore((s) => s.toggleDom);
  const setNature = useProgramStore((s) => s.setNature);
  const setFn = useProgramStore((s) => s.setFn);

  const doms = [...new Set(controls.map((c) => c.dom))];

  return (
    <div className={styles.section}>
      {doms.map((dom) => {
        const list = controls.filter((c) => c.dom === dom);
        const open = openDoms[dom];
        return (
          <div key={dom}>
            <button type="button" className={styles.domHead} onClick={() => toggleDom(dom)}>
              <span>{open ? "▾" : "▸"}</span>
              {dom}
              <span className={styles.domCount}>{list.length} controls</span>
            </button>
            {open &&
              list.map((c) => (
                <div key={c.c} className={styles.ctl}>
                  <span className={styles.ctlCode}>{c.c}</span>
                  <span className={styles.ctlName} title={c.d}>
                    {c.n}
                  </span>
                  <select
                    className={styles.select}
                    value={c.nat}
                    onChange={(e) => setNature(c.c, e.target.value as Nature)}
                    aria-label={`${c.c} nature`}
                  >
                    <option value="cfg">config-enforced</option>
                    <option value="auto">automated</option>
                    <option value="manual">manual</option>
                  </select>
                  <select
                    className={styles.select}
                    value={c.fn}
                    onChange={(e) => setFn(c.c, e.target.value as ControlFn)}
                    aria-label={`${c.c} function`}
                  >
                    <option value="prev">preventive</option>
                    <option value="det">detective</option>
                  </select>
                </div>
              ))}
          </div>
        );
      })}
    </div>
  );
}

function DatasetsSection() {
  const controls = useProgramStore((s) => s.controls);
  const setDatasetRet = useProgramStore((s) => s.setDatasetRet);
  const setDatasetCa = useProgramStore((s) => s.setDatasetCa);
  const registry = datasetRegistry(controls);

  return (
    <div className={styles.section}>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>System</th>
              <th>Artifact</th>
              <th>Retrieval</th>
              <th>Continuous assurance</th>
              <th>Controls served</th>
            </tr>
          </thead>
          <tbody>
            {registry.map((d) => (
              <tr key={d.sys + d.art}>
                <td className="mono">{d.sys}</td>
                <td>{d.art}</td>
                <td>
                  <select
                    className={styles.select}
                    value={d.ret}
                    onChange={(e) => setDatasetRet(d.sys, d.art, e.target.value as Retrieval)}
                    aria-label={`${d.art} retrieval`}
                  >
                    {Object.entries(ART_RET).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <select
                    className={styles.select}
                    value={d.ca}
                    onChange={(e) => setDatasetCa(d.sys, d.art, e.target.value as CaMethod)}
                    aria-label={`${d.art} assurance method`}
                  >
                    {Object.entries(CA).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="mono">{d.ctls.join(" ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MissionsSection() {
  const controls = useProgramStore((s) => s.controls);
  const systems = useProgramStore((s) => s.systems);
  const list = missions(controls, systems);

  return (
    <div className={styles.section}>
      {list.map((m) => (
        <div key={m.id} className={`${styles.quietCard} ${styles.missionCard}`}>
          <span className={styles.missionId}>{m.id}</span>
          <span className={styles.rowTitle}>{m.art}</span>
          <span className={styles.spacer} />
          <span className={styles.rowSub}>{m.sysName}</span>
          <span className={styles.missionMeta}>
            {m.surface} · {m.ca} · {m.cadence} · serves {m.ctls.join(", ")}
            {m.scopeUnresolved && (
              <span className={styles.warn}> · target system scope unresolved</span>
            )}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ProgramClient() {
  const [tab, setTab] = useState<Tab>("Scope");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    useProgramStore.persist.rehydrate();
    setHydrated(true);
  }, []);

  return (
    <>
      <nav className={styles.subnav} aria-label="Program sections">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            className={`${styles.tab} ${tab === t ? styles.tabActive : ""}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </nav>
      {hydrated && (
        <>
          {tab === "Scope" && <ScopeSection />}
          {tab === "Controls" && <ControlsSection />}
          {tab === "Datasets" && <DatasetsSection />}
          {tab === "Missions" && <MissionsSection />}
        </>
      )}
    </>
  );
}
