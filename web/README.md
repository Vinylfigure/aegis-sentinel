# Aegis web

Next.js 15 frontend for the Aegis assurance compiler — the demo-engagement
surface. CSS Modules on a token sheet extracted from `docs/prototypes/*.html`
(`src/styles/tokens.css`); no Tailwind, no component library. Fonts load via
`next/font/google` (Inter, Space Grotesk, IBM Plex Mono — the prototypes'
families).

## Run

```bash
cd web
npm install        # or npm ci for the locked install
npm run dev        # http://localhost:3000
```

Verify (what CI runs in `.github/workflows/web-verify.yml`, job `web-verify`):

```bash
npm ci
npx tsc --noEmit
npm run build
```

## Layout

- `src/app/` — App Router pages. `/scope`, `/controls`, `/process`,
  `/reconciliation`, `/verdicts`, `/registry`, `/proof` are stubs today; each
  page states the execution-plan task (A3–B4) that fills it in.
- `src/components/` — `AppShell` (two-column shell), `NavTabs` (route tabs),
  `GaugesRail` (sticky right rail), `StubPage`.
- `src/styles/tokens.css` — the single source of color/type/scale tokens.
  Extend it only from a prototype or ratified design, never ad hoc.

## Data contract: `artifacts/demo-engagement/`

The later pages consume the artifact set emitted by the Python pipeline
(`scripts/build_demo_engagement.py`, drift-tested byte-for-byte — do not hand
edit those files, and do not vendor copies into `web/`):

| File | Shape | Consumed by |
| --- | --- | --- |
| `verdicts.json` | array of verdict records (`record_id`, `control_id`, `status`, `population_id`, `evidence_refs`, hashes) | `/verdicts` (B3), `/proof` (B4) |
| `reconciliation.json` | one population: `ladder`, `sources`, `canonical_members`, six-bucket `buckets`, `dispositions`, `counts` | `/reconciliation` (B2) |
| `registry.json` | `entries` (capability entries with `lifecycle` + `history_caveats`), `compile_errors` (E-codes), top-level `note` | `/registry` (B3) |
| `poisons.json` | `cases` + `detection` + embedded `verdict_records` | `/verdicts` mutation scorecard (B3) |

B1 lands hand-authored mocks in `web/src/data/engagement/` matching these
shapes; C2 swaps them for the real artifacts above.

## REQUIRED for B3: render ratification caveats on `/registry`

`registry.json` carries a top-level DEMO-ONLY `note` ("workday.terminated_workers
appears frozen because the demo registry ratifies a COPY in memory; the on-disk
entry stays DRAFT pending the Owner's real act") and several entries whose
`history_caveats` begin with `DRAFT:` (github.audit_log, okta.users,
slack.scim_users, workday.terminated_workers). Per the #28 PR note requirement,
the `/registry` page MUST render the top-level `note` and every entry's DRAFT
caveats verbatim alongside the lifecycle badge. A registry page that shows these
entries as usable/frozen without the caveats misrepresents ratification state —
that is a demo-correctness bug, not a styling choice.

## Deployment (Owner console action — not automated)

Vercel project creation is an Owner action in the Vercel console; nothing in
this repo or CI calls Vercel:

- Root Directory: `web/`
- Ignored Build Step: skip the build unless `web/` or `artifacts/` changed,
  e.g. `git diff --quiet HEAD^ HEAD -- :/web :/artifacts` (exit 0 skips,
  non-zero builds). `artifacts/` must be in the diff because C2 renders the
  real demo-engagement output.
