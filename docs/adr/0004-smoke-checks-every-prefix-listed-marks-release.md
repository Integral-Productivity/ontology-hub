# 4. Smoke checks every registered prefix; `listed` marks release

Date: 2026-10-15

## Status

Accepted. Resolves
[ontology-hub#11](https://github.com/Integral-Productivity/ontology-hub/issues/11).
Builds on ADR-0002 §2 (`listed: false` until first public release).

## Context

`smoke.py` asserted the HTML page, the Turtle file and content negotiation
only for `/metawork/`. For other registry entries it asserted routing and
negotiation and reported the page status without asserting it. On 2026-10-02
`/vertical-development/` returned 404 and smoke still passed. The 404 itself
is expected: `vertical-development-ontology` is private until its first public
release
([vertical-development-ontology#4](https://github.com/Integral-Productivity/vertical-development-ontology/issues/4)).
The gap was that smoke could not tell a released ontology that broke from an
unreleased one that is not live yet.

Issue #11 offered two ways to make that distinction:

- **A. A flag in `registry.json`** (it suggested `published: false`) so a
  registered but unreleased prefix is reported as pending instead of failing.
- **B. Register a prefix only once its site is live.**

How the router uses `registry.json` decides between them. `build.py` inlines
the whole registry (minus `$comment`) into the Worker. The Worker reads only
`origin` and, per prefix, `repo`, `mode` and `turtle`; it ignores every other
field. Any change to `registry.json` triggers `deploy-router` on merge, which
redeploys the production Worker.

- Option B changes router behaviour. Removing `/vertical-development/` from
  the registry would stop the Worker routing that prefix and its Turtle file
  and stop 303 negotiation under it; the path would fall through to the hub's
  Pages site. It would also undo ADR-0002, which registered the prefix before
  release on purpose: registering publishes no IRI, reserves the name, and
  lets the ontology's site build be tested against the real router.
- Option A with a new `published` field would not change router behaviour,
  since the Worker ignores unknown fields. But the registry already has a
  field with that meaning. ADR-0002 defines `listed: false` as "hidden from
  the landing page until the ontology's first public release", and the
  ontology's release flips it. A second flag, `published`, would have to be
  flipped in the same commit. The two could drift, and nothing would decide
  which one wins when they disagree.

## Decision

1. **Keep registering prefixes before release (reject B).** The router
   continues to route and negotiate every registered entry.

2. **`listed` is the single release signal (A, reusing the existing field).**
   An entry is *released* unless it has `listed: false`. No `published`
   field is added. `registry.json` does not change, so this decision does not
   redeploy the Worker.

3. **`smoke.py` derives its checks from `registry.json`.** For every prefix:

   | Check | Released | Unreleased (`listed: false`) |
   |---|---|---|
   | Routing: `X-Ontology-Router` is the entry's `repo` | asserted | asserted |
   | `Accept: text/turtle` on the prefix → `303` → `turtle` | asserted | asserted |
   | Prefix page → `200 text/html` | asserted | reported as `PEND` |
   | Turtle file → `200 text/turtle` | asserted | reported as `PEND` |

   The landing-page check asserts that `/` is the hub page, links every
   released prefix, and links no unreleased one, the same rule
   `validate.yml` applies to the built page, now checked against what is live.
   `PEND` never fails the run; `FAIL` does. The Meta Work term-page, term
   negotiation and 404 checks from metawork-ontology#1 stay as they were.

4. **The planning logic is unit-tested without network**
   (`tests/test_smoke.py`, stdlib `unittest`):
   `python -m unittest discover -s tests`.

## Consequences

- A released ontology whose page or Turtle file breaks now fails smoke. An
  unreleased one shows as `PEND`, and the run says how many are pending.
- An ontology's release is one edit: remove `listed: false`. The same edit
  makes the landing page link it and makes smoke assert its page and Turtle
  file. If the site is not actually live yet, the next smoke run fails, which
  is the intended alarm.
- `listed` now carries two jobs: landing-page visibility and release state.
  If those ever need to differ (for example a released ontology deliberately
  kept off the landing page), split the field then, with an ADR.
- The Python unit tests run locally only until CI runs them. Wiring them into
  `validate.yml` is tracked in
  [ontology-hub#18](https://github.com/Integral-Productivity/ontology-hub/issues/18).
