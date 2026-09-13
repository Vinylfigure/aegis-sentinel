#!/usr/bin/env node
/* Sync the real pipeline artifacts into the web bundle.
 *
 * Copies ../artifacts/demo-engagement/*.json → src/data/engagement/.
 * The committed copies must always equal the synced output — CI re-runs
 * this script and fails on `git diff` (web-verify "artifact-sync drift").
 * If the source directory is absent (e.g. a web-only checkout), the
 * script exits 0 silently and the committed copies stand.
 */

import { copyFileSync, existsSync, mkdirSync, readdirSync } from "node:fs";
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
const files = readdirSync(source).filter((f) => f.endsWith(".json"));
for (const f of files) {
  copyFileSync(join(source, f), join(target, f));
}
console.log(`sync-artifacts: copied ${files.length} artifact file(s)`);
