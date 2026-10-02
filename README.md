# ontology-router

Cloudflare Worker on `ontology.integralproductivity.com/*` (ADR-0004).

- `registry.json` — path prefix → publishing repository. Edit this to add an ontology.
- `worker.js` — routing + content negotiation. `__REGISTRY__` is replaced at build.
- `build.py` — prints the deployable script.

Deploy (Cloudflare account "Integral Productivity LLC", zone `integralproductivity.com`):

1. `python infra/ontology-router/build.py > /tmp/ontology-router.js`
2. Upload as Workers script `ontology-router` (API: `PUT /accounts/{account}/workers/scripts/ontology-router`, multipart with `metadata.body_part = "script"`).
3. Ensure zone route `ontology.integralproductivity.com/*` → `ontology-router` exists.

Verify:

```
curl -sI -H 'Accept: text/turtle' https://ontology.integralproductivity.com/metawork/vocab/MetaWork/   # 303 → /metawork.ttl
curl -sI -H 'Accept: text/html'   https://ontology.integralproductivity.com/metawork/vocab/MetaWork/   # 200 text/html
```

This directory moves to `Integral-Productivity/ontology-hub` when the second ontology starts (ADR-0004, trigger to revisit).
