# 2. Turtle file at the root; registered entries can be unlisted until release

Date: 2026-10-02

## Status

Accepted. Decided by the Marketing role (domain-naming authority) for
[metawork-ontology#7](https://github.com/Integral-Productivity/metawork-ontology/issues/7),
which registers `/vertical-development/`.

## Context

The second ontology, `vertical-development-ontology`, mints IRIs under
`https://ontology.integralproductivity.com/vertical-development`. To register
it, two questions needed one answer for every ontology:

1. **Where is an ontology's Turtle file?** Two candidates:
   - at the root, `/<name>.ttl`, the pattern `/metawork.ttl` already
     publishes; or
   - under the prefix, `/<name>/<name>.ttl`, the wording in
     `vertical-development-ontology` ADR-0006 ("the Turtle file at the prefix").
   ADR-0001 §3 already made the Worker route each entry's `turtle` path to
   its repository, so either works technically; mixing them would not.

2. **What does the landing page show for a registered but unreleased
   ontology?** The registry drives both routing and the landing page
   (ADR-0001, Consequences). `vertical-development-ontology` stays private
   until its publication gate passes (its ADR-0006), so a listed link would
   be a 404.

## Decision

1. **Turtle at the root.** Every registry entry's `turtle` is
   `/<name>.ttl`, where `/<name>/` is its prefix. The Worker routes that path
   to the entry's repository and is the `303` target for RDF requests under
   the prefix. A test (`tests/worker.test.mjs`) enforces the rule for every
   entry. `/metawork.ttl` is already published and stays where it is.

2. **`listed: false` hides an entry from the landing page.** Routing and
   content negotiation work for every registered entry; only the landing
   page skips unlisted ones. The ontology's release sets `listed` to `true`
   (or removes it). `validate.yml` fails if a listed entry is missing from
   the page or an unlisted one appears on it.

3. **`/vertical-development/` is registered** with
   `repo: vertical-development-ontology`, `mode: project-site`,
   `turtle: /vertical-development.ttl`, `listed: false`. The name is
   confirmed by the Marketing role; it becomes permanent when the first IRI
   under it is published (metawork-ontology ADR-0004 §1).

## Consequences

- One rule for all ontologies; a consumer can guess any ontology's Turtle
  file from its prefix.
- `vertical-development-ontology` ADR-0006 ("the Turtle file at the prefix")
  needs a note pointing here, and its site build (its issue #3) writes
  `site/vertical-development.ttl`, not `site/vertical-development/…ttl`.
- Registering a prefix is now safe before release: it publishes no IRI and
  shows nothing on `/`. The registered-but-404 state is visible in
  `smoke.py`, which checks routing and negotiation for every entry and
  reports, without asserting, the page status.
