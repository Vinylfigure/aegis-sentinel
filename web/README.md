This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Engagement data (155a/155b, issue #162)

`src/data/engagement/*.json` is synced verbatim from `../artifacts/demo-engagement/`
by `scripts/sync-artifacts.mjs` (`npm run build`'s `prebuild` hook re-runs it).
Two views the UI needs — populations and proof-graph lineage — have no backend
producer at all, so `src/lib/data/engagement.ts` derives them at load time
instead of reading a committed stand-in file:

| Derived view | Source of truth |
| --- | --- |
| `Population` | `reconciliation.json`'s own `population_*` fields, `ladder.after_dispositions` (state), `buckets` minus `intersection` (deltas — mirrors `reconcile/engine.py`'s own attachment rule), `boundary_exclusions` (exclusions) |
| `ProofGraph` (per verdict) | `commitments.json` (commitment/requirement stage, via `claim_ids`), `reconciliation.json` (population/source/reconciliation stages), `contracts.json` (contract stage, keyed by `spec_hash`), `snapshot.json` (snapshot stage, when the population is in `blocks.populations`) |

If a backend rename breaks one of these, `loadEngagement()`'s runtime guards
(`check*` functions) flag it as artifact drift before the derivation runs on
stale assumptions — see that file's header comment for the full mapping.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
