"""Live checks against https://ontology.integralproductivity.com (issue
metawork-ontology#1 acceptance list). Run from outside the Cloudflare account,
e.g. a GitHub Actions runner:

    python smoke.py [base_url]

Exit 0 when every check passes; prints one line per check either way.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://ontology.integralproductivity.com").rstrip("/")
UA = "ontology-hub-smoke/1 (+https://github.com/Integral-Productivity/ontology-hub)"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def get(path: str, accept: str | None = None):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA, **({"Accept": accept} if accept else {})})
    try:
        r = OPENER.open(req, timeout=20)
        return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def ctype(h) -> str:
    return (h.get("Content-Type") or "").split(";")[0].strip()


def check_html(path):
    s, h, _ = get(path, "text/html")
    return s == 200 and ctype(h) == "text/html", f"{s} {ctype(h)}"


def check_negotiation():
    s, h, _ = get("/metawork/vocab/MetaWork/", "text/turtle")
    loc = h.get("Location") or ""
    if s != 303 or loc not in ("/metawork.ttl", BASE + "/metawork.ttl"):
        return False, f"{s} Location={loc!r}"
    s2, h2, _ = get("/metawork.ttl", "text/turtle")
    return s2 == 200 and ctype(h2) == "text/turtle", f"303 → {loc} → {s2} {ctype(h2)}"


def check_turtle():
    s, h, body = get("/metawork.ttl")
    return s == 200 and ctype(h) == "text/turtle" and b"@prefix" in body, f"{s} {ctype(h)}"


def check_root():
    # The hub's landing page, not an ontology repo's project-site index.
    s, h, body = get("/", "text/html")
    hub = b"<h1>Integral Productivity ontologies</h1>" in body
    listed = b'href="/metawork/"' in body
    return s == 200 and hub and listed, f"{s} {ctype(h)} hub page={hub} lists /metawork/={listed}"


def check_404():
    s, _, _ = get("/metawork/vocab/does-not-exist/", "text/html")
    return s == 404, str(s)


def check_registered(prefix: str, cfg: dict):
    # Every registered prefix, released or not: the Worker routes it to its
    # repo and negotiates to its Turtle file. The page itself may 404 until
    # the ontology's site exists, so its status is reported, not asserted.
    s, h, _ = get(prefix, "text/html")
    routed = h.get("X-Ontology-Router") == cfg["repo"]
    s2, h2, _ = get(prefix, "text/turtle")
    loc = h2.get("Location") or ""
    neg = s2 == 303 and loc in (cfg["turtle"], BASE + cfg["turtle"])
    return routed and neg, f"{s} X-Ontology-Router={h.get('X-Ontology-Router')!r}; turtle → {s2} {loc}"


REGISTRY = json.loads((Path(__file__).resolve().parent / "registry.json").read_text())

CHECKS = [
    ("GET /metawork/ → 200 text/html", lambda: check_html("/metawork/")),
    ("GET /metawork/vocab/MetaWork/ → 200 text/html", lambda: check_html("/metawork/vocab/MetaWork/")),
    ("GET /metawork/vocab/MetaWork/ (Accept: text/turtle) → 303 → /metawork.ttl → 200 text/turtle", check_negotiation),
    ("GET /metawork.ttl → 200 text/turtle", check_turtle),
    ("GET / → 200, hub landing page lists Meta Work", check_root),
    ("GET /metawork/vocab/does-not-exist/ → 404", check_404),
] + [
    (f"{p} routed to {c['repo']}; Accept: text/turtle → 303 → {c['turtle']}", (lambda p=p, c=c: check_registered(p, c)))
    for p, c in REGISTRY["prefixes"].items()
]

if __name__ == "__main__":
    failed = 0
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:  # network errors are failures, not crashes
            ok, detail = False, repr(e)
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  [{detail}]")
    print(f"{len(CHECKS) - failed}/{len(CHECKS)} passed against {BASE}")
    sys.exit(1 if failed else 0)
