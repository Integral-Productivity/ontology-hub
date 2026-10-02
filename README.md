# ontology-hub

Domain-level infrastructure for **<https://ontology.integralproductivity.com/>**.
No ontology lives here. Each ontology is its own repository and publishes its
own GitHub Pages project site; this hub decides which path goes to which
repository, and serves the root landing page.

```
registry.json      path prefix → publishing repository (edit this to add an ontology)
worker.js          ontology-router Cloudflare Worker: routing + content negotiation
build.py           inlines registry.json into worker.js → deployable script
build_site.py      renders the landing page (/) from registry.json
smoke.py           live acceptance checks against the domain
tests/             Worker routing tests (node --test), run on every PR
docs/adr/          decisions; ADR-0001 records the move from metawork-ontology
```

## How a request is served

1. Cloudflare route `ontology.integralproductivity.com/*` runs Worker `ontology-router`.
2. A request under a registered prefix (or for that prefix's `.ttl`) whose
   `Accept` prefers RDF over HTML gets `303 See Other` → the ontology's `.ttl`.
3. Otherwise a registered prefix is fetched from
   `integral-productivity.github.io/<repo><path>` (`mode: project-site`).
4. Every other path (`/`, `/404`) passes through to GitHub Pages for this
   repository, which owns the custom domain.

## Add an ontology

1. In the ontology repo: build its site so files sit under its prefix
   (`site/<name>/…` and `site/<name>.ttl`), deploy Pages as a project site,
   no custom domain.
2. Here: add the prefix to `registry.json` (`mode: project-site`, `turtle`,
   `title`, `source`). Prefixes are permanent once published; reserved ones
   are listed under `reserved`.
3. Open a PR. `validate` runs the routing tests; on merge, `deploy-router`
   uploads the Worker and runs `smoke.py`, and `pages` rebuilds the landing page.

## Deploy

- `deploy-router.yml` — on change to the Worker or registry. Needs repo secret
  `CLOUDFLARE_API_TOKEN` (Workers Scripts: Edit on account *Integral
  Productivity LLC*; Workers Routes: Edit and Zone: Read on zone
  `integralproductivity.com`).
- `pages.yml` — the landing page. Pages source: GitHub Actions; custom domain
  `ontology.integralproductivity.com`, Enforce HTTPS on.
- `smoke.yml` — daily and on demand; the acceptance checks from
  [metawork-ontology#1](https://github.com/Integral-Productivity/metawork-ontology/issues/1).

Manual equivalent: `python build.py > /tmp/ontology-router.js`, then upload as
Workers script `ontology-router` (`PUT /accounts/{account}/workers/scripts/ontology-router`,
multipart, `metadata.body_part = "script"`).

## License

Content CC-BY-SA-4.0; code MIT. See [`LICENSE.md`](LICENSE.md).
