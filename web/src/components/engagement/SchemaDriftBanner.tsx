"use client";

/* Red "artifact schema drift" banner — rendered whenever the runtime
 * guards find the mock artifacts out of shape with the mirrored
 * ontology. The page still renders what was parseable; it never crashes. */

import styles from "./SchemaDriftBanner.module.css";

export default function SchemaDriftBanner({ drift }: { drift: string[] }) {
  if (!drift.length) return null;
  return (
    <div className={styles.banner} role="alert">
      <div className={styles.head}>
        artifact schema drift — {drift.length} finding{drift.length > 1 ? "s" : ""}
      </div>
      <p className={styles.sub}>
        The engagement artifacts no longer match the mirrored ontology. Rendering
        what parses; treat every figure below as suspect until re-mirrored.
      </p>
      <ul className={styles.list}>
        {drift.slice(0, 8).map((d, i) => (
          <li key={i}>{d}</li>
        ))}
        {drift.length > 8 && <li>… and {drift.length - 8} more</li>}
      </ul>
    </div>
  );
}
