# Capability Registry

The versioned, inspectable catalog of evidence surfaces (PRD-v3 §3).
Each file under `capabilities/` is one JSON capability entry describing
one evidence surface of one system, validated against
`schemas/capability-entry.schema.json` (generated from
`src/aegis_sentinel/capability/entry.py`).

## Layout

```
registry/
  capabilities/
    <system>.<surface-slug>.json    # one CapabilityEntry per file
```

Entries are loaded with `Registry.load("registry/capabilities")`
(`src/aegis_sentinel/capability/registry.py`). Loading validates every
file; one invalid entry fails the whole load. CAP01 landed the seven
V1 termination-lane entries across the five lane systems (HRIS feed,
Okta users + System Log, GitHub org members + audit log, GCP IAM via
Cloud Asset Inventory, Slack users), each with vendor-doc citations and
`ratified_by: "vinylfigure (Ratifier)"`. An entry's
`populations_yielded[].name` values are the source ids that lane
populations declare — that name equality is how the compiler (TYP01)
resolves a derivation-rule source to a surface, and a source no usable
entry yields is compile error E117.

## Ratification is mechanical, not convention

An entry's `provenance.ratified_by` field is the gate:

- `ratified_by: null` — a **draft** (e.g. a Cartographer proposal with
  citations). Drafts are visible in `Registry.all()` for review and
  nothing else.
- `ratified_by: "<human identity>"` — ratified. Only ratified entries
  appear in `Registry.usable()`, which is the **only** view the
  compiler (TYP01) consumes.

So an unratified entry cannot type-check a claim or gate a collector,
regardless of caller intent: the draft is mechanically unusable, not
merely marked "pending". Agents may research and propose entries; only
a human sets `ratified_by`. The agent maps the territory; it does not
annex it.

## Versioning

The registry is versioned by git. Every entry carries a const-pinned
`schema_version` (`capability-entry@0.1.0`); a schema change bumps that
constant, regenerates `schemas/capability-entry.schema.json` via
`python scripts/export_schemas.py`, and shows up as an E302-class drift
against previously ratified entries rather than being silently absorbed.
