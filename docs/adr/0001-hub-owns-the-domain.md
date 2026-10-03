# 1. The hub owns the domain, the registry, and the router

Date: 2026-10-02

## Status

Accepted. Inherits
[metawork-ontology ADR-0004](https://github.com/Integral-Productivity/metawork-ontology/blob/main/docs/adr/0004-one-domain-many-ontologies.md)
("One domain for many ontologies") and supersedes the parts of it that place
the registry and router in `metawork-ontology`.

Status note (2026-10-02): the line "Persistence (w3id.org): … still deferred"
under Consequences is closed by
[ADR-0003](0003-persistence-of-ontology-namespaces.md). The namespaces move
under `https://w3id.org/integral-productivity/`. The text below is left as it
was decided.

## Context

ADR-0004 in `metawork-ontology` settled the naming scheme for
`ontology.integralproductivity.com`: one host, one path prefix per ontology,
a Cloudflare Worker that routes each prefix to its repository and performs
content negotiation, unversioned IRIs plus dated snapshots, and a deferred
persistence (w3id.org) decision. Everything in that ADR still holds.

It also recorded a known wrong-place-for-now: the registry and router source
lived in `metawork-ontology/infra/ontology-router/`, and that repository held
the GitHub Pages custom domain. One ontology was privileged; adding a second
meant editing the first. ADR-0004 set the trigger to fix this as "the second
ontology starts". Issue
[metawork-ontology#1](https://github.com/Integral-Productivity/metawork-ontology/issues/1)
does it before that, so the second ontology starts clean.

## Decision

1. **This repository owns everything domain-level:** `registry.json`,
   `worker.js`, `build.py`, the root landing page, and the GitHub Pages custom
   domain `ontology.integralproductivity.com`. No ontology repository holds
   the custom domain.

2. **Every ontology is a `project-site`.** `metawork-ontology`'s `/metawork/`
   entry switches from `custom-domain` to `project-site`. The `custom-domain`
   mode stays in the Worker only as the pass-through used for the hub's own
   paths (`/`, 404s).

3. **The Worker also routes each ontology's Turtle file** (`turtle` in the
   registry, e.g. `/metawork.ttl`) to the publishing repository. Before the
   move that path fell through to the custom-domain owner, which happened to
   be `metawork-ontology`; after it, the owner is the hub, so the route must
   be explicit.

4. **History: `git subtree split`.** The four router files were moved with
   `git subtree split --prefix=infra/ontology-router` from
   `metawork-ontology` `main`, so this repository's first commit is the
   original commit that created them (author, date, and message preserved;
   paths rewritten to the root). `git filter-repo` would do the same with an
   extra dependency; a plain copy with a pointer commit loses `git log` and
   `git blame` on the router.

5. **Deployment is in CI, verification is from outside.** `deploy-router.yml`
   uploads the Worker and ensures the route using a scoped Cloudflare API
   token stored as a repository secret. `smoke.py` checks the live domain
   from a GitHub runner, which is outside the Cloudflare account.

### Cutover order (as executed)

1. Hub created; Worker deployed with `/metawork/` already `project-site`
   while `metawork-ontology` still held the custom domain. GitHub redirects
   the project-site URL to the custom domain while one is set, and a Worker's
   same-zone subrequest goes to the origin, so `/metawork/` kept working.
2. `metawork-ontology` Pages switched to a project-site build (no `CNAME`).
3. Custom domain removed from `metawork-ontology`, added here; Enforce HTTPS.
4. Acceptance checks run (`smoke.py`).
5. `infra/` deleted from `metawork-ontology`; its ADR-0004 gets a status note
   pointing here.

## Consequences

**Positive**

- No ontology is privileged. Adding one is a registry entry here plus a
  project site there; the new ontology's repository is never edited by the hub.
- The landing page is generated from the registry, so it cannot drift from
  the routing.
- Router changes are tested on every PR and deployed by CI rather than by hand.

**Negative**

- One more repository to own. Marketing holds the domain-naming authority
  today; the Institute later (as ADR-0004 says).
- The Worker now depends on `integral-productivity.github.io/<repo>/` for every
  ontology. If the organization ever sets a custom domain on its user site,
  project sites would redirect and this design must be revisited.
- A Cloudflare API token sits in GitHub secrets; it is scoped to one zone and
  one account's Workers scripts.

**Unchanged and still deferred**

- Persistence (w3id.org): trigger is still the earlier of the Institute's
  formation or the second ontology's first public release (ADR-0004 §4).
