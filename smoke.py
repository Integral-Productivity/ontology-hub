"""Live checks against https://ontology.integralproductivity.com (issue
metawork-ontology#1 acceptance list, extended to every registered prefix by
ontology-hub#11). Run from outside the Cloudflare account, e.g. a GitHub
Actions runner:

    python smoke.py [base_url]

Prints one line per check: PASS, FAIL, or PEND. Exit 0 when nothing FAILs.

For every prefix in registry.json the Worker's routing and 303 content
negotiation are asserted. The HTML page and the Turtle file are asserted for
released prefixes and reported as PEND for unreleased ones (`listed: false`),
whose site does not exist until their first public release (ADR-0004).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, NamedTuple
import urllib.error
import urllib.request

DEFAULT_BASE = "https://ontology.integralproductivity.com"
BASE = DEFAULT_BASE
UA = "ontology-hub-smoke/1 (+https://github.com/Integral-Productivity/ontology-hub)"
HUB_HEADING = "<h1>Integral Productivity ontologies</h1>"


class Check(NamedTuple):
    name: str
    fn: Callable[[], tuple[bool, str]]
    required: bool = True
    kind: str = "site"


# ---- planning (pure; unit-tested in tests/test_smoke.py) -------------------

def is_published(cfg: dict) -> bool:
    """`listed: false` marks a registered prefix whose ontology has not had its
    first public release (ADR-0002); anything else is released (ADR-0004)."""
    return cfg.get("listed", True) is not False


def outcome(ok: bool, required: bool) -> str:
    if ok:
        return "PASS"
    return "FAIL" if required else "PEND"


def failures(outcomes) -> int:
    return sum(o == "FAIL" for o in outcomes)


def landing_verdict(body: str, registry: dict) -> tuple[bool, str]:
    """`/` is the hub's landing page, it links every released prefix, and it
    links no unreleased one."""
    prefixes = registry["prefixes"]
    hub = HUB_HEADING in body
    missing = [p for p, c in prefixes.items() if is_published(c) and f'href="{p}"' not in body]
    leaked = [p for p, c in prefixes.items() if not is_published(c) and f'href="{p}"' in body]
    return hub and not missing and not leaked, f"hub page={hub} missing={missing} leaked={leaked}"


def prefix_checks(prefix: str, cfg: dict) -> list[Check]:
    released = is_published(cfg)
    tag = "" if released else " (unreleased: pending until first public release)"
    turtle = cfg["turtle"]
    return [
        Check(f"{prefix} routed to {cfg['repo']}", lambda: check_routing(prefix, cfg), True, "routing"),
        Check(f"{prefix} (Accept: text/turtle) → 303 → {turtle}", lambda: check_negotiation(prefix, turtle), True, "negotiation"),
        Check(f"GET {prefix} → 200 text/html{tag}", lambda: check_html(prefix), released, "page"),
        Check(f"GET {turtle} → 200 text/turtle{tag}", lambda: check_turtle(turtle), released, "turtle"),
    ]


def build_checks(registry: dict) -> list[Check]:
    checks = [
        # Meta Work specifics from metawork-ontology#1: a term page, negotiation
        # from a term IRI, and a 404 passed through from the project site.
        Check("GET /metawork/vocab/MetaWork/ → 200 text/html", lambda: check_html("/metawork/vocab/MetaWork/")),
        Check("GET /metawork/vocab/MetaWork/ (Accept: text/turtle) → 303 → /metawork.ttl",
              lambda: check_negotiation("/metawork/vocab/MetaWork/", "/metawork.ttl")),
        Check("GET /metawork/vocab/does-not-exist/ → 404", check_404),
        Check("GET / → 200, hub landing page lists every released prefix and no unreleased one",
              lambda: check_root(registry)),
    ]
    for prefix, cfg in registry["prefixes"].items():
        checks += prefix_checks(prefix, cfg)
    return checks


# ---- network ---------------------------------------------------------------

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


def check_turtle(path):
    s, h, body = get(path, "text/turtle")
    return s == 200 and ctype(h) == "text/turtle" and b"@prefix" in body, f"{s} {ctype(h)}"


def check_negotiation(path, turtle):
    s, h, _ = get(path, "text/turtle")
    loc = h.get("Location") or ""
    return s == 303 and loc in (turtle, BASE + turtle), f"{s} Location={loc!r}"


def check_routing(prefix, cfg):
    # The Worker stamps every response under a registered prefix, whatever the
    # project site answered, so this holds before an ontology's release too.
    s, h, _ = get(prefix, "text/html")
    header = h.get("X-Ontology-Router")
    return header == cfg["repo"], f"{s} X-Ontology-Router={header!r}"


def check_root(registry):
    s, h, body = get("/", "text/html")
    ok, detail = landing_verdict(body.decode("utf-8", "replace"), registry)
    return s == 200 and ok, f"{s} {ctype(h)} {detail}"


def check_404():
    s, _, _ = get("/metawork/vocab/does-not-exist/", "text/html")
    return s == 404, str(s)


REGISTRY = json.loads((Path(__file__).resolve().parent / "registry.json").read_text())


def main(argv: list[str]) -> int:
    global BASE
    BASE = (argv[1] if len(argv) > 1 else DEFAULT_BASE).rstrip("/")
    outcomes = []
    for check in build_checks(REGISTRY):
        try:
            ok, detail = check.fn()
        except Exception as e:  # network errors are failures, not crashes
            ok, detail = False, repr(e)
        o = outcome(ok, check.required)
        outcomes.append(o)
        print(f"{o}  {check.name}  [{detail}]")
    failed, pending = failures(outcomes), outcomes.count("PEND")
    print(f"{len(outcomes) - failed - pending} passed, {pending} pending, {failed} failed of {len(outcomes)} against {BASE}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
