# Aegis — Design Fix D-7: UNKNOWN Decomposition + Deterministic Identity Resolution

Status: paste-ready edits (July 16, 2026)
Scope: closes the UNKNOWN-funnel judgment leak (`Aegis_Investigator_Agentic_Architecture.md §9`) that Fix 1 explicitly did **not** touch. Two moves: (1) decompose the monolithic UNKNOWN bucket by *why the deterministic join failed*, moving the dominant volume to a fully deterministic path; (2) solve the residual identity-fuzzy branch with a **frozen probabilistic record-linkage model** so the agent exits the runtime verdict path entirely. Lands one new decision (**D-7**) in `Aegis_Investigator_Design_Decisions.md`, edits to Architecture `§2 / §3 / §4 / §5 / §9`, and one API-lane placement in `API_Constraints_By_Trust_Consequence.md`.

Verdict: **ADOPT (with conditions).** The plan → freeze → execute split is untouched; this hardens what happens *inside* the UNKNOWN residue that split already routes to a human.

---

## 0. What this closes and what it deliberately does not

- **Closes (mechanically):** the "agent has a proposal monopoly on UNKNOWN resolution and the gate only ever confirms/denies the agent's framing" leak in `§9`. The dominant UNKNOWN cause becomes a deterministic join against declared exception sources; the fuzzy residual becomes a frozen deterministic scorer. The agent no longer *generates* resolutions at runtime.
- **Does not close (stated honestly, per `Aegis_Design_Fixes.md` discipline):** judgment is not eliminated — it is relocated across the gate to versioned, testable, human-ratified artifacts (exception-source catalog; linkage model + thresholds). The clerical-review band still needs humans. A genuinely novel legitimate basis nobody declared is still UNKNOWN→FAIL/human. These are the correct residuals, surfaced, not engineered away.

---

## 1. The reframe: UNKNOWN is not one thing

The `§9` leak exists because "UNKNOWN" is an undifferentiated bucket, and undifferentiated buckets are where judgment hides. Decompose by join-failure cause. Each cause wants a different mechanism and maps to a *different control conclusion*.

| Cause | What it means | Mechanism | Agent runtime role |
| --- | --- | --- | --- |
| **Basis-missing** | Record is legitimate but its authorizing basis isn't in the *primary* declared source (break-glass approved out-of-band; policy-exempt service account) | Deterministic join against **declared exception-source registries** (§3) | **None** |
| **Identity-fuzzy** | Record can't be keyed because the join key itself is soft (name variants, missing employee ID, cross-system ID mismatch) | **Frozen probabilistic linkage model** (§4) | **None at runtime** (drafts params at authoring only) |
| **No-basis-anywhere** | Record keys to nothing in the primary source or any exception registry | Deterministic → **FAIL** (the clean finding you want to keep) | **None** |

Basis-missing is most of the volume, and it is not ambiguity at all — it is an incomplete source *declaration*. That is why the old design leaked: it sent a declaration problem to an agent as if it were a judgment problem.

---

## 2. D-7 decision entry (paste into `Aegis_Investigator_Design_Decisions.md`)

> ## D-7. UNKNOWN decomposition + deterministic identity resolution — **ADOPT (with conditions)**
>
> - **Decision:** Replace the monolithic UNKNOWN-investigation loop with a three-way deterministic split by join-failure cause. **Basis-missing** records join deterministically against human-declared *exception-source registries*; **no-basis-anywhere** records are a deterministic FAIL; only **identity-fuzzy** records enter a resolution step, and that step is a **frozen probabilistic record-linkage model** (Fellegi-Sunter; reference implementation Splink) whose prediction is a pure deterministic function of a versioned `model.json`. The UNKNOWN *rate is itself a verdict input*, per cause.
> - **Rationale:** The `§9` honest ceiling correctly names the leak — the agent shapes the tested population one candidate at a time and the deterministic gate only confirms/denies the agent's framing. Decomposition removes the agent from the two dominant branches entirely (a declared-source join and a deterministic FAIL are not agent acts), and the frozen linkage model removes it from the third at runtime: a byte-identical scorer replaces a runtime agent pick. Judgment moves from a per-record, runtime, outcome-aware agent call (unauditable, high-volume) to per-control frozen artifacts (auditable, seeded-fixture-able) — the same relocation D-2/D-4 already make for the verifier and the semantic gate.
> - **Conditions:**
>   1. **Exception-source registries must be queryable systems of record**, declared and ratified in the Skill at authoring time (§3). Where a basis lives only in email/Slack, there is no deterministic source to join against → it stays human-attest (D-5), and the *absence of a registry is itself a finding* (an org with break-glass but no system of record for it fails the documentation control, correctly).
>   2. **The linkage model is trained once, seeded, and frozen** (§4). Re-performance loads the frozen `model.json` and predicts — it never retrains. The training run (seed, population snapshot, Splink version, term-frequency tables) is the ratified planning artifact.
>   3. **Thresholds are ratified judgment**, tiered by control impact like D-4. The clerical-review band routes to a human, never to the agent, never to autonomous PASS.
> - **Design note:** No change to the plan → freeze → execute split. The linkage model *is* a frozen spec in the §3 sense; the exception registries are more declared sources in the §4 two-tier sense. D-7 reuses existing gates rather than adding one.

---

## 3. Mechanism A — Exception-source registries (basis-missing branch)

**File:** `Aegis_Investigator_Agentic_Architecture.md`

### 3a. Add to §5 (the human-authored / human-ratified judgment set)

> - **Authoritative exception sources** — the systems of record that vouch for *legitimate* deviations from the primary population: the break-glass ticket system, the PAM/privileged-access approval log, the service-account registry, the policy-exemption tracker. Declared per control at authoring time and ratified at the same trust boundary as the primary population source. A record missing the primary source is deterministically joined against these; keys there → PASS whose **support is the approval record itself** (the exact evidence an auditor wants), keys nowhere → FAIL. The catalog is a **living ratified artifact**, not a one-time declaration: a genuinely novel legitimate basis is UNKNOWN→FAIL/human until its source is declared and ratified. The system cannot certify a basis it has no authoritative vouch for — and should not.

### 3b. Add to §4 (source of truth: two-tier with override)

> **Third tier — exception sources.** Below the domain and control population sources sits a declared set of *exception authorities* (§5). The intake runner joins primary-source-missing records against these deterministically. This is not a fallback the agent chooses at runtime; it is a fixed, versioned join order the runner executes. An empty exception catalog for a control that exhibits basis-missing volume is surfaced as a documentation-control finding, never silently resolved.

---

## 4. Mechanism B — Deterministic identity resolution (identity-fuzzy branch)

**File:** `Aegis_Investigator_Agentic_Architecture.md` — new subsection **§4b**; substrate note in §2.

This is the research payload: the branch where the agent previously tie-broke at runtime is replaced by a frozen, re-performable probabilistic model. The agent exits the runtime verdict path.

### 4b. Insert new subsection §4b (after §4a)

> ### 4b. Identity resolution — frozen probabilistic linkage, not runtime agent judgment
>
> When a record cannot be keyed because the join key is soft (name variants, missing/rekeyed employee ID, cross-system identifier mismatch), resolution runs as a **two-stage deterministic pipeline**, not an agent call.
>
> **Stage 1 — deterministic rule cascade.** A frozen, versioned waterfall of exact/near-exact blocking rules (strong keys first: email, employee ID; then progressively weaker composite rules). A record that matches *uniquely* under any rule is a deterministic resolution — no probability, no agent. A record that matches *nothing* under the cascade drops to no-basis (FAIL). Only records that remain *multi-candidate* after the cascade enter Stage 2.
>
> **Stage 2 — frozen probabilistic scorer.** A Fellegi-Sunter linkage model (reference implementation: **Splink** — Python, open-source, DuckDB/Spark/Athena backends) assigns each candidate pair a **match weight**. Two ratified thresholds band the result: **match** (deterministic resolution, flagged as fuzzy-resolved), **clerical-review** (routes to a *human*, never the agent, never autonomous PASS), **no-match** (contributes to no-basis/FAIL). The score, not an agent, breaks the tie; the band, not an agent, routes it.
>
> **Why this is on the correct side of the gate.** Prediction is a pure function of a frozen model file. Given the same `model.json` and the same input, the score is byte-identical on every re-run — the re-performance property the independent verifier (`D-2`) checks. Training (unsupervised EM parameter estimation) is stochastic but **seedable**, and it is an *authoring* act: the model is trained once, seeded, ratified, and frozen. Re-performance loads the frozen model and predicts; it never retrains. The training run is the planning artifact — its seed, population snapshot, Splink version, and term-frequency tables are versioned and hashed into the freeze bundle (Fix 3 discipline).
>
> **The agent's only role is at authoring, above the gate:** it may *draft* the blocking/cascade rules and the comparison-column design (Lane 1 mechanics — wrong values fail loud). It does **not** decide the m/u weights, the thresholds, or which candidate wins. Those are the frozen model and the ratified threshold set.
>
> **Determinism requirements (pin all four, or re-performance drifts):**
> 1. **Seed** the parameter-estimation / random-sampling step so the trained model is reproducible.
> 2. **Freeze `model.json`** (weights, comparison levels, blocking rules, `probability_two_random_records_match`) as a versioned, hashed artifact; predict from the frozen file, never from a fresh train.
> 3. **Freeze the term-frequency tables** (or recompute them from the identical frozen population snapshot). TF adjustments are data-distribution-dependent; a score that depends on corpus frequencies is only re-performable if those frequencies are frozen too. This is the subtle determinism gotcha — pin it explicitly.
> 4. **Pin the exact Splink version** in the freeze bundle. Methodology is stable across v3→v4 (same settings → same predictions), but pin the version so a re-run cannot silently ride a point-release change.
>
> **Clustering.** Pairwise links resolve to identities via connected-components clustering over the accepted-edge set — deterministic given a fixed edge set and threshold. The cluster assignment is part of the hashed output.

### 4c. Substrate note in §2 (layer 1, deterministic substrate)

> Identity resolution for soft-keyed records runs here as frozen deterministic linkage (§4b), not in the agent loop. The linkage model is a versioned artifact under drift detection; a model change flows through the same freeze-validate-approve gate as any test-predicate change (`§7`).

---

## 5. Mechanism C — Rate-as-verdict, per cause

**File:** `Aegis_Investigator_Agentic_Architecture.md §9` (folds into the honest-ceiling rewrite in §6 below).

The UNKNOWN rate stops being a soft cap and becomes a verdict input — and because it is now *per cause*, each rate maps to a distinct control conclusion. This inverts the incentive the leak depended on: resolving records can never improve a verdict past the point where volume is the finding, and each cause tells the assessor which control to open.

| Per-cause rate | Control conclusion |
| --- | --- |
| High **basis-missing** (keys to exception registry) | Legitimate access whose approvals are queryable — PASS *conditional on confirming the registry is authoritative*; the volume itself flags process reliance on out-of-band provisioning |
| High **no-basis-anywhere** | Undocumented provisioning — a true **CC6.2 exception**, not a data-cleanliness problem |
| High **identity-fuzzy** (clerical-review band) | Identifiers don't reconcile across systems — an **ITGC / data-quality finding** in its own right |

"UNKNOWN rate is 12%" tells an assessor nothing. "9% keys to break-glass, 2% keys to nothing, 1% unmatched identities" tells them exactly which control to open. The opaque metric becomes three diagnostics.

---

## 6. Architecture §9 honest-ceiling rewrite

**File:** `Aegis_Investigator_Agentic_Architecture.md §9`

**Replace** the "UNKNOWN is doing suspicious work" bullet and its mitigations block **with:**

> - **UNKNOWN is decomposed, not agent-funneled (D-7).** The old risk — the agent shaping the tested population one candidate at a time while the gate only confirms its framing — is removed from the two dominant branches and the runtime of the third. **Basis-missing** records join deterministically against declared exception-source registries (§4/§5); **no-basis-anywhere** is a deterministic FAIL; **identity-fuzzy** records are scored by a frozen probabilistic linkage model (§4b) whose prediction is byte-identical on re-run, with only a bounded **clerical-review band** reaching a human. The agent no longer generates resolutions at runtime — it drafts blocking rules and comparison design at authoring, above the gate.
>   - **Rate is a verdict input, per cause (§5-C).** Above a ratified per-control threshold each cause maps to a distinct finding (undocumented provisioning = CC6.2; unmatched identities = ITGC/data-quality). Resolution cannot improve a verdict past the point where volume is the finding.
>   - **Residual, stated honestly:** judgment is relocated, not eliminated. The exception-source catalog, the linkage thresholds, the comparison design, and the training snapshot are all ratified human artifacts (versioned, seeded-fixture-able — the correct side of the gate). The clerical-review band is real human work, bounded and measured, not zero. A legitimate basis nobody declared, or an identity pattern the comparison design didn't anticipate, is still UNKNOWN→FAIL/human — the system cannot certify a basis it has no authoritative vouch for, and that is correct behavior, not a gap to close.

---

## 7. Residual, stated honestly (post-fix status of the four items)

1. **Identity-fuzzy tie-break** — *substantially closed.* Runtime agent selection is replaced by a frozen deterministic scorer; agent exits the verdict path. Residual is the **clerical-review band** (human, bounded by threshold choice) and the possibility of correlated blind spots in the comparison design — surfaced as review volume, not eliminated.
2. **Exception registries must exist as queryable sources** — *unchanged and correct.* Where the basis is in email/Slack it is human-attest (D-5). The absence of a registry is now a *finding*, which turns the limitation into audit signal.
3. **Match predicate + exception-authority choice are ratified judgment** — *unchanged and correct.* Moved across the gate to versioned, testable artifacts (frozen `model.json` + declared catalog), not eliminated. Same shape as tolerance semantics in §5.
4. **Novel legitimate basis → UNKNOWN→FAIL/human** — *unchanged and correct.* The exception-source catalog is a living ratified artifact. The system cannot vouch for a basis no authoritative source vouches for.

Net: the honest-ceiling sentence upgrades from *"we surface UNKNOWNs as reviewable volume"* to *"the agent cannot invent a resolution; the dominant volume resolves against declared sources deterministically; the fuzzy residual is scored by a frozen re-performable model with only a bounded human review band; and each residual rate is itself a per-control finding."* That is a materially stronger claim you can back with a byte-identical re-run.

---

## 8. API-lane placement (`API_Constraints_By_Trust_Consequence.md`)

Add the linkage model to the taxonomy so it lands on the right side of the gate:

- **Blocking / cascade rules → Lane 1 (fail-loud mechanics).** A bad blocking rule produces a visible error or an obviously wrong candidate count; the agent may draft/refine these under the §7 fence.
- **m/u weights, thresholds, comparison design, TF tables → Lane 3 (semantic, mandatory D-4 human sign-off before freeze).** A wrong threshold or comparison mapping produces a plausible-but-wrong match (genuine-but-irrelevant identity resolution) — the exact semantic-trap failure mode. Never agent-owned.
- **Version this model file and put it under drift detection (§6.2)** on the same cadence as the rest of the frozen specs.

---

## Apply order & residual

1. **Mechanism A (exception registries) first** — it captures the dominant UNKNOWN volume and is pure declaration + deterministic join; no new runtime component.
2. **Mechanism B (frozen linkage)** next — introduces the Splink model as a frozen artifact; the four determinism requirements (seed, freeze model, freeze TF, pin version) are blocking for re-performance.
3. **Mechanism C (rate-as-verdict) + §9 rewrite** last — positioning/verdict-logic, reuses A and B.

**What this does not close (per the red-team's own discipline):** the clerical-review band is real human judgment; the ratified artifacts are judgment relocated, not removed; and correlated errors in the comparison design can survive a single model. Do not claim the fuzzy branch is *zero* human — claim the agent exited the runtime path and the residual is bounded, measured, and re-performable.

---

## Sources

- **Splink** — MoJ Analytical Services, Python probabilistic record linkage / entity resolution (Fellegi-Sunter, unsupervised EM); backends DuckDB (bundled), Spark, AWS Athena, PostgreSQL, SQLite; used by NHS England and the UK MoD Veterans' Card system. GitHub `moj-analytical-services/splink`; docs `moj-analytical-services.github.io/splink`; Linacre et al., *Splink: Free software for probabilistic record linkage at scale*, IJPDS 7(3), 2022.
- **Reproducibility / determinism** — Splink docs, *Methods in Linker.training*: seeding `estimate_u_using_random_sampling` makes the entire model reproducible; *Splink 4.0.0 released* (2024-07-24): same settings → same predictions, no change to statistical methodology v3→v4; *Defining Splink models* / *Real time record linkage*: model serializes to `model.json`, predict from a pre-trained model via `linker.inference.predict()` / `compare_two_records()`.
- **Probabilistic vs deterministic linkage & thresholds** — Splink docs, *Probabilistic vs Deterministic linkage*: rules-based cascade supported via blocking; probabilistic scoring with user-chosen evidence threshold; match/uncertain/non-match banding for clerical review.
- **Aegis corpus anchors** — `Aegis_Investigator_Agentic_Architecture.md` §2/§3/§4/§4a/§5/§7/§9; `Aegis_Investigator_Design_Decisions.md` D-2, D-4, D-5; `Aegis_Design_Fixes.md` Fix 1/Fix 3; `API_Constraints_By_Trust_Consequence.md` Lanes 1–3; `Workflow_Theory_Supporting_Information.md` Contradicting Info §1 (8.5% contextual false-positive rate), §2 (deterministic ≠ truthful).
