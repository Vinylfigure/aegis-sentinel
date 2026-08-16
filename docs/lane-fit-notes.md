# Lane fit notes

Evidence ledger for lane-template schema misfits, per the LANE02 acceptance
criterion: where a new lane does not fit the ratified template schema, the
misfit is *recorded* here as dated evidence, never papered over and never
silently patched into the model. Per L-014, a schema extension enters the
codebase only after entries here demonstrate the need; the extension sketches
below are evidence of shape, not commitments.

Each entry states: what the lane needed, what the schema offers today, what
was expressed instead (if anything), and what an extension would look like.

## 2026-08-16 — LANE02, AP-automation lane (`templates/lanes/ap_automation.json`)

### FIT-001 · No second event population (payments)

- **Needed:** a payments-executed EVENT population from the payment-execution
  system, so the flagship AP control — NON-EXISTENCE of payments without an
  approved invoice — can bind to its true domain (every payment in the period).
- **Schema offers:** `instantiate()` mints exactly one EVENT population, at
  `event_role`; every downstream role is hardwired to an ENTITY
  "access holders" population ("enumerate {system} members; join against
  {event_system} identities"). There is no template field to declare a
  downstream role's population as an event feed.
- **Expressed instead:** only the completeness direction — every approved
  invoice has a payment event (`cp-payment-discipline`, EVENT-adjacent via
  SEQUENCE/TIMING over the approved-invoice population). The reverse
  direction (no unapproved payment) is *not* in the template: binding it to
  the approved-invoice population would invert its domain, which is exactly
  the papering-over this ledger exists to prevent. Same root cause blocks a
  vendor-records ENTITY population (vendor-master gets an access-holder
  population instead, which is honest only for the access control).
- **Extension sketch:** per-downstream population shape declared in the
  template (e.g. `population_kind: "event-feed" | "access-holders"` on a
  downstream role), or multiple event roles per lane.

### FIT-002 · SEQUENCE across two event populations

- **Needed:** approval-before-payment ordering, which relates two event
  populations (approvals, payments).
- **Schema offers:** `SEQUENCE` exists as an assertion type, but a Claim
  binds to exactly one `population_id`, and an `AssertionSpec` carries no
  secondary population reference. The payment leg can only live in prose.
- **Expressed instead:** the SEQUENCE assertion in `cp-payment-discipline`,
  bound to the approved-invoice population with the payment leg prose-only —
  the same degraded pattern the ratified termination lane uses for its
  EVENT-in-IdP assertions, so it is precedented, but the compiler cannot
  demand payment-feed evidence from the claim's population reference (TYP01
  sees one population). Recorded here so the degradation is evidence, not
  convention.
- **Extension sketch:** an optional `counterpart_population` /
  `counterpart_role` field on SEQUENCE (and cross-population EVENT)
  assertion specs, resolved at instantiation like `population_id`.

### FIT-003 · Amount thresholds are not parameterizable

- **Needed:** tiered approval — invoices at or above an amount threshold
  require a second, distinct approver.
- **Schema offers:** `AssertionSpec` parameterizes timing only
  (`timing_days`, `timing_business_days`). There is no typed numeric
  threshold, so an amount could only be hardcoded into description prose,
  invisible to instantiation and to evidence typing.
- **Expressed instead:** only the untiered form — every approved invoice
  carries a captured approval (`cp-approval-capture`). The tiered control is
  omitted, not prose-smuggled.
- **Extension sketch:** a typed threshold parameter analogous to
  `timing_days` (amount + currency, paired with an assertion type that
  requires it) — deferred until a second lane needs it (L-014).

### FIT-004 · `per_downstream` assumes a fan-out hub role

- **Needed:** an access-restriction control across all three downstream
  systems (approver roster, payment release, vendor bank-detail edits).
- **Schema offers:** `per_downstream: true` fans one control point across
  `downstream_roles`, but instance-population resolution keys off
  `at_role == event_role`: anchoring a per-downstream control point at the
  event role binds every fanned claim to the *event* population instead of
  the per-target access populations. The device therefore requires a hub
  role distinct from the event role (the termination lane's IdP). AP has no
  such hub — access is administered in each system directly.
- **Expressed instead:** the fan-out is unrolled into three per-role control
  points (`cp-approval-access`, `cp-payment-access`,
  `cp-vendor-master-access`), each anchored at its own downstream role. This
  is honest (and lets each statement be system-specific) at the cost of
  duplication the template device was meant to remove.
- **Extension sketch:** resolve the fanned claim's population by the
  *target* role rather than `at_role`, so `per_downstream` works from any
  anchor — a semantics fix in `instantiate()`, not a schema field.

### FIT-005 · Single `{system}` placeholder in templates

- **Needed:** control-point text that names both sides of a cross-system
  control (ERP and banking; ERP and vendor master) from the bindings.
- **Schema offers:** `statement_template` / `description_template` are
  formatted with exactly one `{system}` — the anchor (or fan-out target)
  binding. Counterpart systems can only appear as fixed role-level prose
  ("the approval workflow", "the vendor master"), so rebinding a role to a
  different concrete system never updates the counterpart wording.
- **Expressed instead:** counterpart systems referenced generically by role
  name in prose, mirroring the termination lane's "downstream IdP" wording.
  Cosmetic today; it becomes load-bearing the day claim text is compiled
  into evidence requests.
- **Extension sketch:** format templates with the full bindings map
  (`{approval-workflow}`, `{payment-execution}`, …) instead of a single
  positional `{system}`.
