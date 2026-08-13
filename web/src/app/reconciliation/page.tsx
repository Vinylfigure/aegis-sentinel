"use client";

/* Population index: every defined universe with its type, ladder state,
 * size, and open-delta count. Size shows "—" wherever the denominator
 * is unratified — the no-%-against-an-unratified-denominator rule. A
 * population whose derivation names a source with no capability entry
 * wears its E117: DEFINED, and it cannot advance until the entry lands. */

import Link from "next/link";
import {
  blockingCompileError,
  loadEngagement,
  openDeltaCount,
} from "@/lib/data/engagement";
import { LadderChip, MiniChip, Tip, TypeBadge } from "@/components/engagement/Badges";
import SchemaDriftBanner from "@/components/engagement/SchemaDriftBanner";
import styles from "./Reconciliation.module.css";

export default function ReconciliationIndexPage() {
  const load = loadEngagement();
  const { populations } = load.artifacts;

  return (
    <div>
      <SchemaDriftBanner drift={load.drift} />
      <p className="sub">
        The denominator is the breakthrough. Each card is a population — a
        defined universe with a derivation rule, source roles, and an assurance
        state. Sizes render only against a ratified denominator; open deltas are
        what stands between DISCOVERED and RECONCILED. Click through for the
        set-reconciliation board.
      </p>

      <div className={styles.grid}>
        {populations.map((p) => {
          const open = Math.max(openDeltaCount(load, p.population_id), p.open_deltas.length);
          const ratified = p.state === "RATIFIED";
          const blocker = blockingCompileError(load, p);
          return (
            <Link
              key={p.population_id}
              href={`/reconciliation/${p.population_id}`}
              className={styles.card}
              data-population={p.population_id}
            >
              <div className={styles.cardTop}>
                <TypeBadge type={p.type} />
                <LadderChip state={p.state} />
                {blocker && (
                  <MiniChip
                    tone="red"
                    title={`${blocker.missing_source}: no ratified capability entry — discovery cannot run`}
                  >
                    {blocker.code}
                  </MiniChip>
                )}
              </div>
              <div className={styles.name}>{p.name}</div>
              <code className={styles.pid}>{p.population_id}</code>
              <p className={styles.def}>{p.definition}</p>
              <div className={styles.stats}>
                <div className={styles.stat}>
                  {ratified && p.size !== null ? (
                    <b>{p.size}</b>
                  ) : (
                    <b className={styles.dash}>
                      <Tip tip="Size is withheld until the denominator is RATIFIED — no count or coverage % is ever published against an unratified population.">
                        —
                      </Tip>
                    </b>
                  )}
                  <span>size</span>
                </div>
                <div className={styles.stat}>
                  <b className={open ? styles.openWarn : ""}>{open}</b>
                  <span>open deltas</span>
                </div>
                <div className={styles.stat}>
                  <b>{p.sources.length}</b>
                  <span>sources</span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
