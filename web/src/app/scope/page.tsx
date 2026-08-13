"use client";

import { DATA_CLASSES, LAYERS, PRODUCTS } from "@/data/seed";
import { useProgramStore } from "@/lib/state/programStore";
import type { Tri } from "@/lib/types/authoring";
import styles from "./Scope.module.css";

const TRI: { v: Tri; label: string; selCls: keyof typeof styles }[] = [
  { v: "in", label: "IN", selCls: "selIn" },
  { v: "unk", label: "?", selCls: "selUnk" },
  { v: "out", label: "OUT", selCls: "selOut" },
];

function TriButtons({
  value,
  onChange,
}: {
  value: Tri;
  onChange: (v: Tri) => void;
}) {
  return (
    <div className={styles.tri}>
      {TRI.map((t) => (
        <button
          key={t.v}
          className={value === t.v ? styles[t.selCls] : ""}
          onClick={(e) => {
            e.stopPropagation();
            onChange(t.v);
          }}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export default function ScopePage() {
  const products = useProgramStore((s) => s.products);
  const systems = useProgramStore((s) => s.systems);
  const toggleProduct = useProgramStore((s) => s.toggleProduct);
  const toggleProductOpen = useProgramStore((s) => s.toggleProductOpen);
  const toggleClass = useProgramStore((s) => s.toggleClass);
  const toggleLayer = useProgramStore((s) => s.toggleLayer);
  const setAssetItem = useProgramStore((s) => s.setAssetItem);
  const setSystemScope = useProgramStore((s) => s.setSystemScope);
  const addSystem = useProgramStore((s) => s.addSystem);

  const cats = [...new Set(systems.map((s) => s.cat))];

  return (
    <div>
      <p className="hint">
        Scope is decided by product and by the data that product carries — not
        by framework. Select the products that carry a commitment, declare the
        data classes each one handles, then walk the asset stack. Every asset
        is in, unknown, or out; unknowns block the scope assertion rather than
        defaulting into it. Only in-scope systems become available for control
        mapping downstream — an unknown system blocks nothing here but taints
        every control mapped to it.
      </p>

      <div className="slab">Products &amp; data</div>
      {PRODUCTS.map((p) => {
        const s = products[p.id];
        if (!s) return null;
        return (
          <div
            key={p.id}
            className={`${styles.prod} ${s.on ? styles.on : ""} ${s.open ? styles.open : ""}`}
          >
            <div
              className={styles.phead}
              onClick={() => toggleProductOpen(p.id)}
            >
              <div
                className={styles.box}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleProduct(p.id);
                }}
              />
              <div>
                <div className={styles.pname}>{p.name}</div>
                <div className={styles.pdesc}>{p.desc}</div>
              </div>
              <div className={styles.chev}>▶</div>
            </div>
            <div className={styles.pbody}>
              <div className={styles.pstep} style={{ margin: "14px 0 0" }}>
                Data classes this product carries
              </div>
              <div className={styles.dcGrid}>
                {DATA_CLASSES.map((d) => (
                  <div
                    key={d.id}
                    className={`${styles.dc} ${s.cls.includes(d.id) ? styles.on : ""}`}
                    onClick={() => toggleClass(p.id, d.id)}
                  >
                    <b>{d.name}</b>
                    <span>{d.note}</span>
                    <span className={styles.tier}>{d.tier}</span>
                  </div>
                ))}
              </div>
              <div className={styles.pstep} style={{ margin: "18px 0 2px" }}>
                Asset inventory
              </div>
              {LAYERS.map((L, li) => {
                const counts = L.items.reduce(
                  (a, _, ii) => {
                    const v: Tri = s.items[`${li}:${ii}`] || "unk";
                    a[v]++;
                    return a;
                  },
                  { in: 0, unk: 0, out: 0 } as Record<Tri, number>
                );
                return (
                  <div
                    key={L.n}
                    className={`${styles.layer} ${s.layersOpen[li] ? styles.open : ""}`}
                  >
                    <div
                      className={styles.lhead}
                      onClick={() => toggleLayer(p.id, li)}
                    >
                      <span className={styles.lnum}>
                        {String(li + 1).padStart(2, "0")}
                      </span>
                      <span className={styles.lname}>{L.n}</span>
                      <span className={styles.lcount}>
                        {counts.in} in · <b>{counts.unk} unknown</b> ·{" "}
                        {counts.out} out
                      </span>
                    </div>
                    <div className={styles.lbody}>
                      {L.items.map((it, ii) => {
                        const v: Tri = s.items[`${li}:${ii}`] || "unk";
                        return (
                          <div key={it.name} className={styles.item}>
                            <TriButtons
                              value={v}
                              onChange={(nv) =>
                                setAssetItem(p.id, li, ii, nv)
                              }
                            />
                            <div className={styles.itxt}>
                              <b>{it.name}</b>
                              <span>{it.note}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      <div className="slab">System registry</div>
      {cats.map((cat) => (
        <div key={cat} className={styles.syscat}>
          <h4>{cat}</h4>
          <div className={styles.sysgrid}>
            {systems
              .filter((s) => s.cat === cat)
              .map((s) => (
                <div key={s.id} className={styles.sys}>
                  <b>{s.name}</b>
                  <TriButtons
                    value={s.v}
                    onChange={(v) => setSystemScope(s.id, v)}
                  />
                </div>
              ))}
            {cat === "Third parties" && (
              <button
                className={styles.addsys}
                onClick={() => {
                  const n = prompt("System name");
                  if (n) addSystem(n);
                }}
              >
                + system
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
