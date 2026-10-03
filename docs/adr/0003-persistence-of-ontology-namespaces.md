# 3. Persistence of the ontology namespaces (w3id.org, or not)

Date: 2026-10-02

## Status

**Proposed. Not decided.** This record prepares the decision of
[metawork-ontology#8](https://github.com/Integral-Productivity/metawork-ontology/issues/8).
The Marketing role (domain-naming authority, ADR-0001) fills in the Decision
section. Until then this pull request stays a draft and nothing here is in force.

When accepted, this record supersedes decision 4 of
[metawork-ontology ADR-0004](https://github.com/Integral-Productivity/metawork-ontology/blob/main/docs/adr/0004-one-domain-many-ontologies.md)
and the "still deferred" line of ADR-0001.

## Context

### What must be decided, and why now

metawork-ontology ADR-0004, decision 4, deferred one question: do the ontology
namespaces move under a permanent-identifier service (`w3id.org`), or stay on
`ontology.integralproductivity.com`? Its trigger is "the earlier of (a) the
Institute's formation, or (b) the second ontology's first public release. At
that point, decide w3id once for all prefixes."

Trigger (b) is close. `vertical-development-ontology` is the second ontology.
Its ADR-0006 keeps the repository private until this decision is made (gate
item 2), and its ADR-0003 plans the first public release for week 3
(2026-10-23). The reason for the gate: an IRI is permanent after it is public.
A namespace change before that release breaks nothing. A change after it
breaks each consumer.

ADR-0004 gives the reason to consider w3id at all: "The domain belongs to a
company; the ontologies are meant to outlive any one entity." The stewardship
decision of 2026-10-02 moves the repositories to the Integral Productivity
Institute when it exists.

### The state of the two ontologies on 2026-10-02

| | Meta Work | Vertical Development |
|---|---|---|
| Namespace | `https://ontology.integralproductivity.com/metawork#` and `…/metawork/vocab/` | `https://ontology.integralproductivity.com/vertical-development#`, `…/vocab/`, `…/vocab/label/`, `…/source/` |
| Public | Yes, since 2026-10-02 (version 0.1.0) | No (private repository; entry `listed: false`) |
| Known consumers of the IRIs | One: the sync test of `metawork-claude-plugin` (as ADR-0004 states; the plugin repository was not read for this record) | None. The scholarship skill uses labels, not IRIs |
| Files that hold the base IRI | 15 in `metawork-ontology` | 9 in `vertical-development-ontology` |

So a change of namespace costs the least on the day this record is written:
one ontology is one day old with one known consumer, and the other is not
public.

### What w3id.org is

- A redirect service. `https://w3id.org/<name>/…` answers with an HTTP
  redirect to a URL that the owner of `<name>` chooses.
- Operation: "A growing group of organizations have pledged responsibility as
  a consortium to ensure the operation of this website." The stated intent:
  "All identifiers associated with this website are intended to be around for
  as long as the Web is around." The agreement is made so that some of the
  organizations "could fail, lose interest, or become unavailable for long
  periods of time without negatively affecting the operation of the site."
  ([w3id.org](https://www.w3id.org))
- Registration: fork the GitHub repository, add a directory with an
  `.htaccess` file (the redirect rules) and a `README.md` (contact
  information), and open a pull request. ([w3id.org](https://www.w3id.org))
- Names: "There is no official policy on identifier names." The
  administrators can refuse a name that is too generic or can cause
  confusion. ([w3id.org](https://www.w3id.org))
- Common practice: Garijo and Poveda-Villalón (2020), section 2.5, recommend
  permanent URIs for the long-term sustainability of an ontology, and name
  `purl.org` and `w3id.org` as the services most used. The same paper says an
  ontology's URIs must be in "a URI namespace under the developer's control",
  because "only in a domain under our control we will be able to serve the
  right serialization of the ontology."
  ([arXiv:2003.13084](https://arxiv.org/pdf/2003.13084))

Those two statements of the paper are in tension, and that tension is this
decision: an identifier that outlives the steward AND full control of what
the identifier serves.

### How w3id would fit this hub

Nothing in the router changes. The Worker and the registry stay as ADR-0001
and ADR-0002 made them.

```
https://w3id.org/<name>/vertical-development/vocab/stage-4   (the IRI)
   → redirect by w3id.org (one .htaccess rule for all paths under <name>)
https://ontology.integralproductivity.com/vertical-development/vocab/stage-4
   → the hub's Worker: HTML for a browser, 303 to the Turtle file for an RDF client
```

One rule forwards each path, so a new ontology needs a registry line here and
no change at w3id.org. If the host or the steward changes, the one rule
changes, and each published IRI keeps working.

Two facts follow from that picture:

1. **The Institute does not have to exist first.** A w3id entry is two files
   in a git repository. The contact in its README can be the LLC's
   role-holder today and the Institute later; the change is a pull request.
   ADR-0004 deferred partly because "the Institute does not yet exist to own
   the w3id entry". *This is an inference from the registration procedure,
   not a statement by w3id.org.*
2. **The IRI and the serving URL become different.** Today the two site
   builders and their CI checks assume that the base IRI's host is the host
   that serves the pages (`tools/build_site.py` in both ontology
   repositories; the "every minted IRI maps to a file" assertion in each
   `pages.yml`). With w3id, the base IRI is on `w3id.org` and the pages are
   on this host. The builders need a second setting, the serving origin.
   `ontology-tooling` is in construction now
   ([metawork-ontology#10](https://github.com/Integral-Productivity/metawork-ontology/issues/10)).
   It is cheaper to give it that setting before version 0.1.0 than after two
   repositories use it.

## Options

The four options of metawork-ontology#8. The order is not a ranking.

### Option 1. No w3id: all namespaces stay on this host

- **Work now:** none. `vertical-development-ontology#2` closes with a status
  note.
- **What you get:** one hop per request, one namespace pattern, full control,
  no third party.
- **What you accept:** each IRI depends on the registration of
  `integralproductivity.com`. The Institute inherits a dependency on a
  hostname of the company. If the domain lapses or changes hands, each IRI
  breaks, and no outside party can repair it.
- **A mitigation that fits this option:** the LLC keeps the domain and gives
  the Institute control of the `ontology` subdomain by DNS delegation. That
  moves operation, not ownership of the name.
- **Fits when:** the domain is sure to stay with an entity that wants the
  ontologies to resolve, and "outlive any one entity" is a preference and not
  a requirement.

### Option 2. w3id for all prefixes now; Meta Work re-mints

- **Work now:**
  1. Choose `<name>`; open the pull request at `perma-id/w3id.org`.
  2. Meta Work: change the base IRI in 15 files, release a new version, update the
     plugin's fixture and sync test. The old IRIs keep resolving (this host
     still serves them), but they are no longer the names.
  3. Vertical Development: change the base IRI in 9 files before the first
     release (`vertical-development-ontology#2`).
  4. `ontology-tooling` and the two `pages.yml` checks: separate the base IRI
     from the serving origin.
  5. Hub: `smoke.py` also follows the w3id redirect for each prefix.
- **What you get:** one namespace pattern for the family. A change of host,
  domain or steward is a one-line change. The stated goal of ADR-0004 is met.
- **What you accept:** a breaking change for Meta Work on its second day; one
  more hop and one more party in each dereference; a change of the redirect
  waits for a merge by the w3id.org administrators (how long that takes is
  not known to this record); `<name>` is permanent.
- **Schedule risk:** the w3id pull request must be merged before the release
  of 2026-10-23, or the first public IRIs do not resolve.
- **Fits when:** "outlive any one entity" is a requirement. This is the
  cheapest day to do it: the cost of step 2 grows with each consumer and each
  release.

### Option 3. w3id for new ontologies only; Meta Work keeps its namespace

- **Work now:** steps 1, 3, 4 and 5 of option 2. No change to Meta Work or to
  the plugin.
- **What you get:** no breaking change. Vertical Development, Holacracy, TPD
  and the mappings are persistent from their first release.
- **What you accept:** two namespace patterns in one family, for as long as
  the IRIs live. The exception is Meta Work: the one framework that
  Integral Productivity owns, and the one most likely to move to the
  Institute. The tooling must support the two patterns.
- **Fits when:** a break of the Meta Work namespace is not acceptable, and an
  inconsistent family is.

### Option 4. Defer again, to the Institute's formation

- **Work now:** a new ADR in `vertical-development-ontology` that changes
  gate item 2 of its ADR-0006. Then that ontology releases on this host.
- **What you get:** the entity that will own the identifiers makes the
  decision.
- **What you accept:** two ontologies with public IRIs on the company
  hostname. A later move to w3id is then a breaking change for the two, with
  more consumers than today. This option also sets aside trigger (b) of
  ADR-0004.
- **Fits when:** the Institute will exist before 2026-10-23, or the release
  can wait for it.

### An option that issue #8 does not list

A neutral domain that the Institute owns (not `integralproductivity.com`,
not w3id). It gives control and independence from the company name, but a
domain needs an owner that pays for it each year, and the Institute does not
exist. It is not compared here.

## Comparison

| Characteristic | 1. No w3id | 2. w3id, all, now | 3. w3id, new only | 4. Defer |
|---|---|---|---|---|
| IRIs survive a change of domain or steward | No | Yes | New ones only | Not decided |
| One namespace pattern in the family | Yes | Yes | **No** | Yes, until a later move |
| Breaking change today | None | Meta Work (1 known consumer) | None | None |
| Breaking change later, if persistence is wanted | All ontologies | None | Meta Work | All public ontologies |
| Work before 2026-10-23 | None | Most | Medium | Small (one ADR) |
| Hops per request; outside parties | 1; none | 2; w3id.org | 2 for new, 1 for Meta Work | 1; none |
| Control of the redirect | Full | By pull request to w3id.org | By pull request to w3id.org | Full |
| Can be undone after the release | Only by a breaking change | Only by a breaking change | Only by a breaking change | n/a |

Each option is hard to reverse after `vertical-development-ontology` is
public. That is the reason its ADR-0006 put a gate here.

## Assessment (by the preparing session; not the decision)

Two positions are coherent. The choice between them is a choice about one
premise, and the role-holder owns that premise.

- **If the ontologies must outlive the company's domain** (the premise that
  ADR-0004 states, and the stewardship decision of 2026-10-02 supports),
  option 2 fits best. Its largest cost, the Meta Work re-mint, is as low
  today as it will be at any time. Option 3 buys the same persistence for new
  ontologies and leaves the owned framework as the permanent exception.
- **If that premise is a preference** (the company keeps the domain; no
  consumer outside Integral Productivity exists today), option 1 with the DNS
  mitigation fits best, and it costs nothing. Then the honest record is: "we
  accept the dependency", and the trigger in ADR-0004 is closed, not deferred.

Option 4 fits least. It makes no decision and it buys the highest later cost.

A caution against option 2 that the role-holder should weigh: no consumer
outside Integral Productivity uses an IRI of either ontology today. Work on
persistence for identifiers that no outside party uses can be the escapist
meta-work that metawork-ontology ADR-0003 names as a risk. The answer to that
caution is the cost curve, not the present need: the work is small now and
grows with each release.

## Sub-decisions, if the answer includes w3id (options 2 and 3)

1. **The name.** `https://w3id.org/<name>/<ontology>…`. It is permanent. It
   should fit the LLC today and the Institute later. A short generic
   name (for example `ip`) can be refused. Candidate: `integral-productivity`.
2. **The contact** in the w3id README today, and the rule for its change
   when the Institute exists.
3. **Meta Work's old namespace** (option 2 only): keep it resolving with no
   promise, or state an end date.
4. **Who does the tooling change**, and whether `ontology-tooling` 0.1.0
   waits for it.

## Decision

*Not made. To be filled in by the Marketing role:*

- Option: …
- Entity that owns the identifiers: …
- Name and contact, if w3id: …
- What happens to the Meta Work namespace: …
- Namespace pattern for new ontologies: …

## Consequences

*To be written with the decision.* For each option, the first actions are in
"Work now" above. In each case `vertical-development-ontology#2` gets a
comment with the result, and GlassFrog action
`actn_b17d05ea24094bc28625da4afb91c4bd` (Marketing) is marked completed.

## Sources

- w3id.org, "Permanent Identifiers for the Web": <https://www.w3id.org>
  (read 2026-10-02).
- Garijo, D. and Poveda-Villalón, M. (2020). *Best Practices for Implementing
  FAIR Vocabularies and Ontologies on the Web.*
  <https://arxiv.org/pdf/2003.13084>, sections 2, 2.5 and 4.1.
- metawork-ontology ADR-0004; ontology-hub ADR-0001 and ADR-0002;
  vertical-development-ontology ADR-0003 and ADR-0006.
- The file counts are from a search for the host name in each repository's
  `main` on 2026-10-02.
