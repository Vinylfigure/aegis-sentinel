# Aegis — Live Alert Demo Runbook

The live "config change → evidence flips → Google Chat alert → revert" loop, driven
by the single allowlisted script `scripts/demo_mutate.sh <control> apply|revert`. Each
control flips **exactly one** verdict; the org CAI feed → `aegis-trigger` → scoped collector
run records the new verdict, `compute_transitions` emits the transition, and
`alert_transitions` POSTs it to Google Chat. Revert restores the prior state.

The table below is the reviewed, reversible set wired into `demo_mutate.sh`.

## How to run the demo

1. **Clear cold-start.** The transition model carries *changes*, not levels — first-run has
   no prior state. Run the baseline collector **twice** before the demo so you're past
   cold-start and every control has a recorded prior verdict.
   - Prereq: `scripts/bootstrap_fleet.sh` has run (folder + projects B/C + mixed posture)
     and `AEGIS_BOUNDARY_FOLDER` is set in `deploy.yml`, so runs collect the whole fleet and
     the per-project PASS/FAIL grid is already visible in BigQuery.
2. **Per control: edit → run → record flips → alert lands → revert.** Narrate each beat:
   ```bash
   bash scripts/demo_mutate.sh <control> apply     # flip one verdict
   # (CAI feed → aegis-trigger fires a scoped run automatically; or trigger a manual run)
   #   → within seconds a Google Chat line lands (PASS→FAIL or FAIL→UNKNOWN)
   bash scripts/demo_mutate.sh <control> revert    # restore; next run recovers (no re-alert)
   ```
3. **Safety rails baked into the script:** never `allUsers`/`allAuthenticatedUsers` (named
   test principals only); `au11_retention` only ever touches a **throwaway** bucket
   (`gs://aegis-demo-lock-<suffix>`), never the real/locked central or evidence buckets;
   every `apply` has a matching `revert`.

## Control reference

| control | apply command | expected transition | Google Chat line | revert command |
|---|---|---|---|---|
| `cp9_backups` | `bash scripts/demo_mutate.sh cp9_backups apply` | CP-9 **PASS → FAIL** (automated backups off) | `CP-9 \| <FLEET_SQL>: PASS → FAIL` | `bash scripts/demo_mutate.sh cp9_backups revert` |
| `au2_exempt` | `bash scripts/demo_mutate.sh au2_exempt apply` | AU-2 **PASS → FAIL** (exemptedMember added to auditConfigs) | `AU-2 \| <AU2_PROJECT>: PASS → FAIL` | `bash scripts/demo_mutate.sh au2_exempt revert` |
| `au6_exclusion` | `bash scripts/demo_mutate.sh au6_exclusion apply` | AU-6 **PASS → FAIL** (silent exclusion on org sink) | `AU-6 \| aegis-org-sink: PASS → FAIL` | `bash scripts/demo_mutate.sh au6_exclusion revert` |
| `au94_iam` | `bash scripts/demo_mutate.sh au94_iam apply` | AU-9(4) **PASS → FAIL** (read access ⊄ privileged set) | `AU-9(4) \| <CENTRAL_BUCKET>: PASS → FAIL` | `bash scripts/demo_mutate.sh au94_iam revert` |
| `au11_retention` | `bash scripts/demo_mutate.sh au11_retention apply` | AU-11 **PASS → FAIL** (retention 30d < 365d, throwaway bucket) | `AU-11 \| aegis-demo-lock-<suffix>: PASS → FAIL` | `bash scripts/demo_mutate.sh au11_retention revert` |
| `cp6_colocate` | `bash scripts/demo_mutate.sh cp6_colocate apply` | CP-6 **PASS → FAIL** (backups co-located in-region) | `CP-6 \| <FLEET_SQL>: PASS → FAIL` | `bash scripts/demo_mutate.sh cp6_colocate revert` |
| `lov_unknown` | `bash scripts/demo_mutate.sh lov_unknown apply` | **FAIL → UNKNOWN** (collector loses read; never silent PASS) | `CP-9 \| <LOV_PROJECT>: FAIL → UNKNOWN ⚠ loss-of-visibility` | `bash scripts/demo_mutate.sh lov_unknown revert` |
| `cp9_disk` | `bash scripts/demo_mutate.sh cp9_disk apply` | CP-9 **PASS → FINDING** (snapshot schedule detached — **Compute** parity) | `CP-9 \| aegis-disk-demo: PASS → FINDING` | `bash scripts/demo_mutate.sh cp9_disk revert` |
| `new_resource` | `bash scripts/demo_mutate.sh new_resource apply` | **auto-enroll → CP-9 FAIL** (new `--no-backup` Cloud SQL, picked up by the CAI feed) | `CP-9 \| <NEW_SQL>: FAIL` (new record) | `bash scripts/demo_mutate.sh new_resource revert` (**deletes it**) |
| `new_resource_disk` | `bash scripts/demo_mutate.sh new_resource_disk apply` | **auto-enroll → CP-9 FINDING** (new unscheduled disk; fast to show live) | `CP-9 \| <NEW_DISK>: FINDING` (new record) | `bash scripts/demo_mutate.sh new_resource_disk revert` (**deletes it**) |

### Baseline grid (no mutation — shown before any flips)

These are read straight from BigQuery after the fleet is provisioned; they demonstrate the
**same control passing for some infrastructure and failing for other** across the fleet:

| scenario | resource | verdict | what it proves |
|---|---|---|---|
| Data Access — compliant in-scope | A `aegis-sql-demo` (labelled `regulated`, logging on) | `data_access` **PASS** | a regulated store with Data Access logging on |
| Data Access — **caught** | B `aegis-app-sql-b` (labelled `regulated`, logging off) | `data_access` **FAIL** | the label brings B into scope → logging-off is a real FAIL |
| Data Access — **excluded** | C `aegis-app-sql-c` (**unlabelled**) | `data_access` **PASS (out of scope)** | the label gates scope — an unlabelled store is honestly excluded, not a false FAIL |
| Backup encryption (Compute parity) | every disk (CP-9(8)) | **PASS** (Google-managed FIPS) | "backups encrypted" now covers Compute disks too, not just Cloud SQL |
| Region completeness | each `(project × region)` | run **FAIL** if any in-scope region has no record | the "no regions unintentionally excluded" requirement — see below |

### Auto-enrollment beats — `new_resource` / `new_resource_disk`

These prove **"a new resource is automatically picked up and evidenced"** (the requirements'
"new projects/regions get picked up automatically"). `apply` creates a deliberately
non-compliant resource in a fleet app project; the **Cloud Asset Inventory feed** publishes the
change → `aegis-trigger` (≤120 s debounce) → a **scoped** collector run records a brand-new
evidence record and fires its alert — with **no manual enrollment**. `revert` **deletes** the
created resource. Timing: the **disk** beat is seconds (use it live); the **SQL** beat takes a
few minutes to create/delete (start it early, or narrate while it provisions). If a `revert`
is interrupted, delete manually: `gcloud sql instances delete <NEW_SQL> --project <p>` /
`gcloud compute disks delete <NEW_DISK> --zone <z> --project <p>`.

### Region completeness (negative)

To show the per-`(project × region)` guarantee: revoke a regional read (the `lov_unknown`
pattern, or scope discovery at a region with an unreadable resource) so that region produces no
record. The full-sweep reconciliation raises a `region_uncovered` finding and the run state goes
`incomplete` (**run FAIL**) — a region is never silently dropped. Restore the read → the next
full sweep returns to `complete`. (Scoped event runs deliberately do **not** assert region
completeness — only the hourly full sweep is the completeness proof.)

### The headline beat — `lov_unknown`

`lov_unknown` is the differentiator: an attacker who can't fix a FAIL might try to **hide**
it by cutting the collector's visibility. Revoking the collector SA's `roles/cloudsql.viewer`
on one project makes that project's CP-9 read fail — and Aegis records **UNKNOWN**, never a
synthesized PASS. The Chat alert flags it as a high-severity loss-of-visibility. `revert`
re-adds the viewer role and the next run recovers the real verdict.

## Tunable env vars (defaults in `demo_mutate.sh`)

| var | default | used by |
|---|---|---|
| `AEGIS_FLEET_SQL` / `AEGIS_FLEET_SQL_PROJECT` | `aegis-sql-demo` / host | `cp9_backups`, `cp6_colocate` |
| `AEGIS_DEMO_AU2_PROJECT` | `AEGIS_PROJECT_C` (fleet C) | `au2_exempt` |
| `AEGIS_DEMO_LOV_PROJECT` | `AEGIS_PROJECT_B` (fleet B) | `lov_unknown` |
| `AEGIS_DEMO_TEST_SA` | `aegis-demo-tester@<host>.iam…` | `au2_exempt`, `au94_iam` |
| `AEGIS_DEMO_LOCK_SUFFIX` / `AEGIS_DEMO_LOCK_BUCKET` | `demo` / `aegis-demo-lock-demo` | `au11_retention` |
| `AEGIS_ORG_SINK` | `aegis-org-sink` | `au6_exclusion` |
| `AEGIS_CENTRAL_LOG_BUCKET` | `aegis-central-logs-<host>` | `au94_iam` |
| `AEGIS_DEMO_DISK` / `AEGIS_SNAP_POLICY` / `AEGIS_ZONE` | `aegis-disk-demo` / `aegis-snap-sched` / `europe-west1-b` | `cp9_disk` |
| `AEGIS_DEMO_NEW_PROJECT` | `AEGIS_PROJECT_C` (fleet C) | `new_resource`, `new_resource_disk` |
| `AEGIS_DEMO_NEW_SQL` / `AEGIS_DEMO_NEW_DISK` | `aegis-demo-newsql` / `aegis-demo-newdisk` | `new_resource`, `new_resource_disk` |

> The `gcloud` flag spellings carry `# validate:` notes in the script where not 100% certain —
> confirm against `gcloud … --help` before running live.
