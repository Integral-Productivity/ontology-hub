// ontology-router — Cloudflare Worker in front of ontology.integralproductivity.com
//
// Does two things (ADR-0004):
//   1. Routes each registered path prefix to the repository that publishes it.
//      The prefix that owns the GitHub Pages custom domain is passed through
//      unchanged; other prefixes are fetched from that repo's project site.
//   2. Content negotiation: a GET/HEAD under a registered prefix whose Accept
//      header prefers an RDF media type over HTML gets 303 → the .ttl file.
//
// Deployed via the Cloudflare API from the output of build.py (inlines registry.json).
// Service-worker syntax on purpose: no bundler, readable in one sitting.

const REGISTRY = __REGISTRY__;

const RDF_TYPES = [
  "text/turtle", "application/x-turtle", "application/rdf+xml",
  "application/ld+json", "application/n-triples", "text/n3",
];

addEventListener("fetch", (event) => {
  event.respondWith(handle(event.request));
});

function matchPrefix(path) {
  for (const [prefix, cfg] of Object.entries(REGISTRY.prefixes)) {
    if (path === prefix.slice(0, -1) || path.startsWith(prefix)) return [prefix, cfg];
  }
  return [null, null];
}

// Parse an Accept header into [{type, q}] — enough for html-vs-rdf.
function parseAccept(header) {
  return header.split(",").map((part) => {
    const [type, ...params] = part.trim().split(";");
    let q = 1;
    for (const p of params) {
      const [k, v] = p.trim().split("=");
      if (k === "q") q = parseFloat(v);
    }
    return { type: type.trim().toLowerCase(), q: isNaN(q) ? 1 : q };
  }).filter((e) => e.q > 0);
}

function prefersRdf(acceptHeader) {
  if (!acceptHeader) return false;
  const entries = parseAccept(acceptHeader);
  const best = (pred) => Math.max(0, ...entries.filter(pred).map((e) => e.q));
  const rdfQ = best((e) => RDF_TYPES.includes(e.type));
  const htmlQ = best((e) => e.type === "text/html" || e.type === "application/xhtml+xml");
  return rdfQ > 0 && rdfQ > htmlQ; // "*/*" alone never counts as RDF
}

async function handle(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  const [prefix, cfg] = matchPrefix(path);
  const negotiable = (request.method === "GET" || request.method === "HEAD");

  if (prefix && negotiable && !path.endsWith(".ttl") && prefersRdf(request.headers.get("accept"))) {
    return new Response(null, {
      status: 303,
      headers: { Location: url.origin + cfg.turtle, Vary: "Accept", "Cache-Control": "public, max-age=300" },
    });
  }

  let response;
  if (cfg && cfg.mode === "project-site") {
    const target = REGISTRY.origin + "/" + cfg.repo + path + url.search;
    response = await fetch(new Request(target, { method: request.method, headers: request.headers, redirect: "follow" }));
  } else {
    response = await fetch(request); // pass-through to the custom-domain origin
  }

  if (!prefix) return response;
  const out = new Response(response.body, response);
  out.headers.append("Vary", "Accept");
  out.headers.set("X-Ontology-Router", cfg.repo);
  return out;
}
