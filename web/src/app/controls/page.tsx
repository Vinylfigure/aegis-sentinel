"use client";

import Link from "next/link";
import { useProgramStore } from "@/lib/state/programStore";
import type { ControlFn, Nature } from "@/lib/types/authoring";
import styles from "./Controls.module.css";

const NAT_SEG: [Nature, string, keyof typeof styles][] = [
  ["cfg", "CONFIGURABLE", "cfgv"],
  ["auto", "AUTOMATED", "autv"],
  ["manual", "MANUAL", "manv"],
];
const FN_SEG: [ControlFn, string, keyof typeof styles][] = [
  ["prev", "PREVENTATIVE", "prevv"],
  ["det", "DETECTIVE", "detv"],
];

export default function ControlsPage() {
  const controls = useProgramStore((s) => s.controls);
  const systems = useProgramStore((s) => s.systems);
  const openDoms = useProgramStore((s) => s.openDoms);
  const toggleDom = useProgramStore((s) => s.toggleDom);
  const setNature = useProgramStore((s) => s.setNature);
  const setFn = useProgramStore((s) => s.setFn);
  const toggleComp = useProgramStore((s) => s.toggleComp);
  const toggleCtlSystem = useProgramStore((s) => s.toggleCtlSystem);

  const doms = [...new Set(controls.map((x) => x.dom))];

  return (
    <div>
      <p className="hint">
        The control library, seeded from the Aegis testing matrix. Classify
        each control&apos;s nature (configurable · automated-detective ·
        manual) and function (preventative · detective), flag compensating
        controls, and map the in-scope systems it operates over. The posture
        gauges on the right respond live.
      </p>
      {doms.map((dom) => {
        const cs = controls.filter((c) => c.dom === dom);
        const cfg = cs.filter((c) => c.nat === "cfg").length;
        const man = cs.filter((c) => c.nat === "manual").length;
        return (
          <div
            key={dom}
            className={`${styles.dom} ${openDoms[dom] ? styles.open : ""}`}
          >
            <div className={styles.domh} onClick={() => toggleDom(dom)}>
              <b>{dom}</b>
              <span className={styles.stats}>
                <i className={styles.cfg}>{cfg} cfg</i> ·{" "}
                {cs.length - cfg - man} auto ·{" "}
                <i className={styles.man}>{man} manual</i>
              </span>
            </div>
            <div className={styles.domb}>
              {cs.map((ctl) => (
                <div key={ctl.c} className={styles.ctl}>
                  <div className={styles.ctlh}>
                    <span className={styles.code}>{ctl.c}</span>
                    <b>{ctl.n}</b>
                    {ctl.comp && (
                      <span
                        className={`${styles.comp} ${styles.on}`}
                        style={{ cursor: "default" }}
                      >
                        COMPENSATING
                      </span>
                    )}
                  </div>
                  <div className={styles.ctldesc}>{ctl.d}</div>
                  <div className={styles.ctlrow}>
                    <div className={styles.seg}>
                      {NAT_SEG.map(([v, label, cls]) => (
                        <button
                          key={v}
                          className={ctl.nat === v ? styles[cls] : ""}
                          onClick={() => setNature(ctl.c, v)}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                    <div className={styles.seg}>
                      {FN_SEG.map(([v, label, cls]) => (
                        <button
                          key={v}
                          className={ctl.fn === v ? styles[cls] : ""}
                          onClick={() => setFn(ctl.c, v)}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                    <button
                      className={`${styles.comp} ${ctl.comp ? styles.on : ""}`}
                      onClick={() => toggleComp(ctl.c)}
                    >
                      COMP
                    </button>
                  </div>
                  <div className={styles.syschips}>
                    {systems.map((s) => {
                      const on = ctl.sys.includes(s.id);
                      const dis = s.v !== "in";
                      return (
                        <span
                          key={s.id}
                          className={`${styles.sc} ${on ? styles.on : ""} ${dis ? styles.dis : ""}`}
                          title={dis ? "not in scope — unknown taints mappings" : ""}
                          onClick={
                            dis ? undefined : () => toggleCtlSystem(ctl.c, s.id)
                          }
                        >
                          {s.name}
                          {dis && on ? " ⚠" : ""}
                        </span>
                      );
                    })}
                  </div>
                  <div className={styles.dslink}>
                    {ctl.ds.length ? (
                      <Link href="/datasets">
                        {ctl.ds.length} dataset{ctl.ds.length > 1 ? "s" : ""} →
                      </Link>
                    ) : (
                      <span className={styles.none}>
                        no dataset defined — untestable as designed
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
