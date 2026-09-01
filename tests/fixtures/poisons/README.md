# Poison fixtures — VAL02, the six seeded assurance defects (PRD-v3 §6)

One deliberately nasty fixture tenant (`meridian-financial-poisons` /
GCP project `meridian-prod-poisons`), seeded with the mutation
playbook's six poison cases. `scripts/build_demo_engagement.py poisons`
runs them through the REAL pipeline — lane instantiation → compile gate
→ collectors → `reconcile_sets` → typed evaluator — and writes
`artifacts/demo-engagement/{poisons,reconciliation,registry,contracts,snapshot}.json`;
`tests/test_poison_suite.py` asserts detection rate == 100% and pins the
artifacts byte-for-byte.

**TODO(playbook):** the mutation playbook document is not in this repo
(`[NEED: Owner]`, HANDOFF §3). Every case below derives from PRD §6's
one-line description; refs marked TODO(playbook) re-point at the
playbook when it lands.

**Reference-engagement scale (ruled on issue #52, 2026-08-29):** the
sanitized synthetic profile for the V1 termination lane is 750
employees at period start, a 12-month review window, 105 terminations
in-window, 90 active contractors, 3 rehires, 2 same-day terminations,
and 1 termination in the final week of the window. This poison tenant
does not scale to that profile — it stays a deliberately small, hand-
engineered set (**8 terminations in a 77-day window**, 2026-10-15 →
2026-12-31) built to exercise the six specific poison cases below, with
the window deliberately inside the Okta System Log 90-day history
caveat so the TIMING claim compiles honestly (the six-month period is
the E204 trap, exercised in `tests/test_type_checker.py`). Scaling this
fixture to the full reference-engagement profile would dilute the
targeted mechanics without adding detection-rate signal, so it is left
as-is per L-014/L-015 unless a future case needs the larger volume.

## Case → fixture → expected outcome

| # | Poison (PRD §6) | Seeded where | Expected outcome |
|---|---|---|---|
| 1 | Contractor absent from HRIS | `mira.chen@example.com`: okta deactivation `pvt-0009` + tracker `POF-3309`, **no row** in `hris_terminations.json` | RIGHT_ONLY delta, undispositioned → ladder blocks RECONCILED → **UNKNOWN (UNKNOWN_POPULATION)** on the HRIS existence claim |
| 2 | Dormant GitHub local account | `github_members/page_2.json` login `rhea-bell-local` (`sso_identity: null`), named via `identity_map.json`; Rhea Bell terminated `2026-11-16` in HRIS | **NON-EXISTENCE FAIL** naming `rhea.bell@example.com` |
| 3 | Break-glass cloud account, no usable capability | claim/population wired to `breakglass.config` (a system absent from `registry/capabilities/`); the account itself sits in `gcp_service_accounts/page-1.json` | **E117 compile error** — caught before any collection |
| 4 | Failed identity join (garbled email) | `okta_system_log/page-001.json` event `pvt-0003`: target `alternate_id` `quinn.ash%example.com` (no `@` → no canonical key) | UNRESOLVABLE delta (`okta:00u9104`) + Quinn LEFT_ONLY; revocation unattributable → **UNKNOWN (UNKNOWN_EVIDENCE)** on Quinn's timing verdict |
| 5 | Delayed revocation (8+ business days) | Omar Diaz: terminated `2026-10-26` (Mon), okta deactivation `pvt-0002` on `2026-11-06` (Fri) = **9 business days** vs the 5-day constraint | **TIMING FAIL** |
| 6 | Legitimate exception | Pia Voss: phased offboarding, deactivated `2026-12-01` (21 business days late), dispositioned in `exceptions.json` | **EXCEPTION** carrying the disposition ref |

Board seasoning (not poison cases, but the six-bucket board and the
five verdict states must all render distinctly): Uma Wynn's
`worker_type` conflicts between HRIS and tracker (CONFLICT bucket);
`vik.rao@example.com` is a ratified boundary exclusion
(`boundary_exclusions.json`, EXCLUDED bucket, born dispositioned);
`breakglass-admin@…` is boundary-excluded from the termination
population (EXCLUDED verdict); Nia / Rhea / Sam / Tess revoke within
1–2 business days (PASS verdicts).

## Files

- `hris_terminations.json` — authoritative Workday RaaS extract, 8 rows (COL01 format).
- `okta_system_log/page-00{1,2}.json` — deactivation event cursor chain (COL02 format).
- `github_members/page_{1,2}.json` — org member pages incl. the dormant local account (COL03 format).
- `gcp_service_accounts/page-{1,2}.json` — service-account pages incl. `breakglass-admin` (COL04 format).
- `offboarding_tracker.json` — contributing ticket source (walking-skeleton format; `worker_type` on `POF-3308` seeds the CONFLICT).
- `identity_map.json` — ratified local-account ownership register (names case 2's member).
- `boundary_exclusions.json` — ratified exclusions: reconciliation-side (vik.rao) and verdict-side (breakglass-admin).
- `dispositions.json` — the human acts that unblock DISCOVERED→RECONCILED *after* case 1/4 verdicts are recorded against the blocked denominator.
- `exceptions.json` — Pia's dispositioned exception (case 6).

No Slack fixture: no poison case needs it, and `slack.scim_users` is a
DRAFT capability entry — a Slack-scoped claim would refuse to compile
(E117), which is the registry doing its job, not a gap in this suite.
