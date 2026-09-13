#!/usr/bin/env node
/* Sync the real pipeline artifacts into the web bundle.
 *
 * Copies ../artifacts/demo-engagement/*.json → src/data/engagement/, and
 * removes any target file with no matching source name. The committed
 * copies are meant to always equal the synced output — `npm run build`'s
 * `prebuild` hook re-runs this script, so a checkout that builds locally
 * self-heals — but no CI step yet diffs the committed copies against a
 * fresh sync to catch drift on its own (a gap, not a guarantee; add one
 * if this ever proves not enough). Removing orphans (not just copying
 * present ones) matters regardless: `manifest.json`/
 * `capability_registry.json`/`populations.json`/`proof_graph.json` used
 * to sit here as stale, never-synced stand-ins for files the backend
 * never produced (issue #162) — without a delete step, that same
 * silent-staleness failure mode could recur under new names.
 * If the source directory is absent (e.g. a web-only checkout), the
 * script exits 0 silently and the committed copies stand.
 */

import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(here, "..", "..", "artifacts", "demo-engagement");
const target = resolve(here, "..", "src", "data", "engagement");

if (!existsSync(source)) {
  // Web-only checkout: nothing to sync, committed copies stand.
  process.exit(0);
}

mkdirSync(target, { recursive: true });
const sourceFiles = new Set(readdirSync(source).filter((f) => f.endsWith(".json")));
const targetFiles = readdirSync(target).filter((f) => f.endsWith(".json"));

let removed = 0;
for (const f of targetFiles) {
  if (!sourceFiles.has(f)) {
    rmSync(join(target, f));
    removed += 1;
  }
}
for (const f of sourceFiles) {
  copyFileSync(join(source, f), join(target, f));
}
console.log(
  `sync-artifacts: copied ${sourceFiles.size} artifact file(s), removed ${removed} orphan(s)`
);
