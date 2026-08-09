# Aegis Sentinel v0.2 — Event-Driven, Agentic, OSCAL
## Build specification for Replit Agent

**Supersedes the collection model in v0.1.** Monitoring is now event-driven: GitHub pushes configuration changes to us the moment they happen. The interval sweep is retained but demoted — it is no longer how drift is *detected*, it is how event delivery is *proven complete*. This document also adds the agent layer and OSCAL Assessment Results export.

Part A is written to be pasted into Replit Agent. Part B is your setup.

---

# PART A — Paste this into Replit Agent

Extend Aegis Sentinel from scheduled polling to event-driven monitoring, add an AI investigation layer, and add OSCAL export.

## The architectural rule, restated

Every pass/fail decision is made by a plain deterministic Python function. The AI layer being added in this version investigates and explains findings that have *already* been decided — it never produces, revises, or influences a verdict. Keep decision logic in `src/controls/` and `src/verdict.py`, keep the AI layer in `src/agents/`, and do not import any AI client into the decision modules. If an agent's output could change whether something passes, the design is wrong.

## Event ingestion

Add a webhook receiver at `POST /webhook/github`.

**Verify before anything else.** GitHub signs each delivery with an HMAC-SHA256 signature in the `X-Hub-Signature-256` header, computed over the raw request body using the webhook secret. Compute the expected signature and compare using a constant-time comparison. Reject mismatches with 401 and record the rejection in the ledger — a forged or misconfigured delivery is itself a security event. Verify against the raw body bytes, not a re-serialized parse.

**Acknowledge immediately.** Return 200 within a couple of seconds, then process asynchronously in a background task. GitHub times out slow endpoints and will mark the delivery failed.

**Handle these event types**, read from the `X-GitHub-Event` header:

- `branch_protection_rule` with actions created, edited, deleted
- `repository_ruleset` with actions created, edited, deleted
- `branch_protection_configuration` with actions enabled, disabled
- `repository` with action created — a new repository needs a scope decision
- `ping` — respond 200 so hook registration succeeds

For edited actions, the payload carries a `changes` object describing what was modified along with the actor who did it. Capture the full payload verbatim into the ledger before any interpretation, hashed as received. The raw event is the evidence; everything after it is derived.

**Deduplicate.** Every delivery has a unique `X-GitHub-Delivery` GUID. Store it and ignore repeats — GitHub retries on failure and you must not double-record.

## Evaluation on event

When a configuration event arrives, immediately re-collect the affected repository's current branch protection and rulesets, evaluate against the ratified baseline using the existing deterministic controls, and write the verdict to the ledger with a reference to the triggering delivery GUID. Then notify Slack if the verdict is FAIL or UNKNOWN, or if the configuration changed at all.

Latency target: alert within thirty seconds of the change occurring in GitHub.

## Delivery completeness — the part that matters

Webhooks fail silently. A dropped delivery produces no error on our side; it produces nothing at all, and nothing looks identical to no-change-occurred. This is the exact failure mode that manufactures false assurance, so it must be actively checked rather than assumed.

Add a reconciliation job, run hourly, that does two things.

**First, audit delivery.** Call `GET /orgs/{org}/hooks/{hook_id}/deliveries` and enumerate recent deliveries. Any delivery whose status is not successful is a gap. For each gap, fetch its detail and trigger a redelivery. Record the gap and its resolution in the ledger — a webhook that failed and was recovered is a completeness event worth evidencing.

**Second, verify state.** Re-collect current configuration for every monitored repository and compare against the last state recorded from events. If live configuration differs from what our event stream says it should be, an event was missed entirely. Record this as a `completeness_gap` finding with high severity, because it means the event stream cannot be trusted for that window.

Record on every evaluation which mode produced it — `event` or `reconciliation` — and treat the distinction as meaningful evidence rather than an implementation detail. An assertion backed by an event with a verified delivery record is stronger than one backed by periodic observation.

## Agent layer

Add four agent roles in `src/agents/`, each calling the Anthropic API. All are advisory. All write to the ledger with record type `advisory`, never `result`. Each has a hard cap of ten tool calls and must degrade gracefully — if the AI call fails, the finding still stands with its deterministic verdict and no narrative.

**Investigator.** Fires on any FAIL or on any detected configuration change. Given the event payload, the ruleset version history, and recent repository activity, it answers three questions in prose: what specifically changed, who changed it and when, and whether any authorizing record exists — a pull request, an issue, a linked change ticket. It has read-only access to repository history, pull requests, issues, and ruleset version history. It produces narrative and nothing else.

**Triage.** Fires on any UNKNOWN. Classifies the cause into exactly one of three families: permission or API gap, feature not enabled on the repository, or evidence genuinely missing. Each routes differently — the first to a token-permission review, the second to a proposed baseline exception, the third to a human queue. Classification is a proposal; a human confirms it.

**Scope discovery.** Fires on repository creation events, and on demand. Reads repository metadata, topics, languages, and dependency manifests, and proposes whether the repository is in scope for monitoring and which baseline applies, with reasoning. The proposal is written to the ledger and surfaced in the interface for human ratification. It does not take effect until ratified — an agent may draft the judgment set, only a human may adopt it.

**Remediation.** Fires on a confirmed FAIL. Drafts the precise configuration change that would restore the baseline, expressed as a pull request against the repository's ruleset configuration where config-as-code exists, or as a described API call otherwise. It opens the pull request but never merges it — the fix must pass through the same review control the tool audits.

Surface all agent output in the interface inside a visually distinct block labelled "AI-generated — not evidence."

## OSCAL export

Add `GET /export/oscal` producing an OSCAL Assessment Results document as JSON, covering a caller-specified date range.

Build the document as follows. The root is `assessment-results` with a generated UUID and a metadata block carrying title, last-modified timestamp, version, and OSCAL version. Include a `results` array containing one result object for the requested period, with a UUID, title, description, and the period start and end timestamps.

Within the result, emit one `observation` per evaluation drawn from the ledger. Each observation carries a UUID, a description of what was examined, a `methods` array containing `EXAMINE`, a `subjects` array identifying the repository, the collection timestamp, and a `relevant-evidence` entry whose `href` points to the ledger record hash. The evidence link is the point of the whole document — it is what lets an assessor re-perform the assertion.

Emit one `finding` per control evaluation with a UUID, title, description, and a `target` object whose `type` is `objective-id`, whose `target-id` is the control identifier, and whose `status.state` is `satisfied` for PASS and `not-satisfied` for FAIL.

Handle UNKNOWN honestly. OSCAL has no native unknown state. Map it to `not-satisfied` and attach a property named `unknown-cause` carrying the triage classification. Never map UNKNOWN to `satisfied` — that would convert an absence of evidence into a claim of compliance, which is the precise failure this system exists to prevent.

Exclude advisory records entirely. The exporter reads only records of type `result` and `ratification`. Add a test asserting that no advisory content can appear in an exported document, and make that test fail loudly if the invariant breaks.

Also record in the document, per observation, whether the evidence was event-backed or reconciliation-backed, and for state-sampled evidence, the sampling interval. An assessor is entitled to know the detection window.

## Interface additions

Add to the existing dashboard: a live event feed showing recent webhook deliveries with their processing outcome; a delivery-health panel showing successful versus failed deliveries and any redeliveries triggered; the agent investigation narrative attached to each finding in its labelled block; a pending-ratification queue for scope proposals; and a download button for the OSCAL export with a date range selector.

## Environment

Add `GITHUB_WEBHOOK_SECRET` and `ANTHROPIC_API_KEY` to the existing environment variables. Never log either.

---

# PART B — What you do yourself

**Register the webhook at the organization level, not per repository.** One org hook covers every repository including ones created later, which matters because a repository created without protection is exactly the case you want caught. Subscribe to branch protection rule, repository ruleset, branch protection configuration, and repository events. Generate a long random webhook secret, set it in both GitHub and Replit Secrets.

**Your Replit web deployment must be publicly reachable and warm.** GitHub will not retry indefinitely and a cold start that exceeds the timeout marks the delivery failed. This is the strongest argument for a reserved instance rather than scale-to-zero, at least for demo day.

**Token permissions gain one requirement.** Reading `/orgs/{org}/hooks/{hook_id}/deliveries` needs organization administration read. Add it to the fine-grained token, still read-only.

**Test the hook before trusting it.** GitHub's hook settings page shows recent deliveries with full request and response detail, and lets you redeliver any of them. Use it to confirm signature verification works before wiring anything downstream.

---

## Why the sweep survives

It would be tidier to delete the scheduled job now that events arrive in real time. Don't. The event stream is low-latency but fail-silent — when a delivery is dropped, nothing arrives, and nothing is indistinguishable from nothing-happened. The hourly reconciliation is not a second detection mechanism, it is the *proof* that the first one didn't miss anything, and the delivery-audit endpoint makes that proof enumerable rather than assumed.

This is the distinction worth articulating when you demo it: the system detects on events and proves completeness on a schedule. Most monitoring tools do one or the other and quietly hope the gap doesn't matter.

## Where the agency actually is

The agents here decide what to look at, what a change means, and what should be done about it. They do not decide whether anything passes. That boundary is what makes the output re-performable by an assessor who does not trust the model — and re-performability, not accuracy, is the property that makes compliance evidence worth anything.
