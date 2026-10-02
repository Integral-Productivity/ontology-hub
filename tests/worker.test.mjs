// Routing and content-negotiation tests for the built Worker (node --test).
// Loads the exact script build.py emits, with a fake fetch standing in for
// GitHub Pages, so these test what is deployed.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import vm from "node:vm";

const script = execFileSync("python3", ["build.py"], { encoding: "utf8" });
const registry = JSON.parse(execFileSync("python3", ["-c",
  "import json;r=json.load(open('registry.json'));r.pop('$comment',None);print(json.dumps(r))"], { encoding: "utf8" }));

function loadWorker() {
  const calls = [];
  let handler;
  const fakeFetch = async (input) => {
    const url = typeof input === "string" ? input : input.url;
    calls.push(url);
    const path = new URL(url).pathname;
    if (path.endsWith("/does-not-exist/")) return new Response("nope", { status: 404 });
    const type = path.endsWith(".ttl") ? "text/turtle" : "text/html";
    return new Response("ok", { status: 200, headers: { "content-type": type } });
  };
  const ctx = {
    addEventListener: (_t, fn) => { handler = fn; },
    fetch: fakeFetch, Request, Response, URL, Headers, console,
  };
  vm.runInNewContext(script, ctx);
  const get = async (path, accept) => {
    const req = new Request("https://ontology.integralproductivity.com" + path,
      { headers: accept ? { accept } : {} });
    let p;
    handler({ request: req, respondWith: (r) => { p = r; } });
    return p;
  };
  return { get, calls };
}

const PS = registry.origin + "/metawork-ontology";

test("registry: /metawork/ is a project site", () => {
  assert.equal(registry.prefixes["/metawork/"].mode, "project-site");
  assert.equal(registry.prefixes["/metawork/"].turtle, "/metawork.ttl");
});

test("registry: every prefix ends with / and reserved prefixes are not registered", () => {
  for (const p of Object.keys(registry.prefixes)) assert.match(p, /^\/[a-z0-9-]+\/$/);
  for (const r of registry.reserved) assert.ok(!(r in registry.prefixes), r);
});

test("HTML request under a prefix is fetched from the project site", async () => {
  const w = loadWorker();
  const r = await w.get("/metawork/vocab/MetaWork/", "text/html");
  assert.equal(r.status, 200);
  assert.equal(w.calls[0], PS + "/metawork/vocab/MetaWork/");
  assert.equal(r.headers.get("x-ontology-router"), "metawork-ontology");
  assert.match(r.headers.get("vary"), /Accept/);
});

test("RDF request gets 303 to the ontology's Turtle file", async () => {
  const w = loadWorker();
  const r = await w.get("/metawork/vocab/MetaWork/", "text/turtle");
  assert.equal(r.status, 303);
  assert.equal(r.headers.get("location"), "https://ontology.integralproductivity.com/metawork.ttl");
  assert.equal(w.calls.length, 0);
});

test("browser Accept header (html preferred, */* present) is not RDF", async () => {
  const w = loadWorker();
  const r = await w.get("/metawork/", "text/html,application/xhtml+xml,*/*;q=0.8");
  assert.equal(r.status, 200);
});

test("Turtle file is routed to the publishing repo, never 303'd", async () => {
  const w = loadWorker();
  const r = await w.get("/metawork.ttl", "text/turtle");
  assert.equal(r.status, 200);
  assert.equal(w.calls[0], PS + "/metawork.ttl");
  assert.equal(r.headers.get("content-type"), "text/turtle");
});

test("prefix without trailing slash is routed", async () => {
  const w = loadWorker();
  await w.get("/metawork");
  assert.equal(w.calls[0], PS + "/metawork");
});

test("unregistered paths pass through to the hub's custom domain", async () => {
  const w = loadWorker();
  const r = await w.get("/");
  assert.equal(r.status, 200);
  assert.equal(w.calls[0], "https://ontology.integralproductivity.com/");
  assert.equal(r.headers.get("x-ontology-router"), null);
});

test("look-alike paths are not captured by a prefix", async () => {
  const w = loadWorker();
  await w.get("/metaworkshop/");
  assert.equal(w.calls[0], "https://ontology.integralproductivity.com/metaworkshop/");
});

test("404 from the project site is preserved", async () => {
  const w = loadWorker();
  const r = await w.get("/metawork/vocab/does-not-exist/");
  assert.equal(r.status, 404);
});

// ADR-0002: one Turtle rule for every ontology, and every entry is routed.
test("registry: every turtle is /<name>.ttl at the root (ADR-0002)", () => {
  for (const [prefix, cfg] of Object.entries(registry.prefixes)) {
    assert.equal(cfg.turtle, prefix.slice(0, -1) + ".ttl", prefix);
  }
});

test("registry: listed, if present, is a boolean", () => {
  for (const [prefix, cfg] of Object.entries(registry.prefixes)) {
    if ("listed" in cfg) assert.equal(typeof cfg.listed, "boolean", prefix);
  }
});

for (const [prefix, cfg] of Object.entries(registry.prefixes)) {
  const site = registry.origin + "/" + cfg.repo;

  test(`${prefix}: HTML and Turtle are fetched from ${cfg.repo}`, async () => {
    const w = loadWorker();
    const page = await w.get(prefix, "text/html");
    assert.equal(w.calls[0], site + prefix);
    assert.equal(page.headers.get("x-ontology-router"), cfg.repo);
    await w.get(cfg.turtle, "text/turtle");
    assert.equal(w.calls[1], site + cfg.turtle);
  });

  test(`${prefix}: RDF request gets 303 to ${cfg.turtle}`, async () => {
    const w = loadWorker();
    const r = await w.get(prefix + "anything/", "text/turtle");
    assert.equal(r.status, 303);
    assert.equal(r.headers.get("location"), "https://ontology.integralproductivity.com" + cfg.turtle);
  });
}
