"""Render the hub's GitHub Pages site: the root of ontology.integralproductivity.com.

The hub owns the Pages custom domain. Every registered prefix is routed by the
Worker to its own repository, so this site only serves paths no ontology owns:

  site/
  ├── CNAME          ontology.integralproductivity.com (informational; Actions deploys ignore it)
  ├── .nojekyll
  ├── index.html     list of published ontologies, generated from registry.json
  └── 404.html

Usage: python build_site.py [out_dir]
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = "ontology.integralproductivity.com"
REPO = "https://github.com/Integral-Productivity/ontology-hub"

CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#5a5a5a;--line:#e3e3e3;--accent:#2a5d8f;--code:#f4f4f4}
@media(prefers-color-scheme:dark){:root{--bg:#121212;--fg:#e8e8e8;--muted:#a0a0a0;--line:#2c2c2c;--accent:#7fb3e6;--code:#1e1e1e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:32px 16px 64px}a{color:var(--accent)}
h1{font-size:1.7rem;margin:.2em 0}code{background:var(--code);padding:.1em .35em;border-radius:4px;font-size:.92em}
.muted{color:var(--muted)}table{border-collapse:collapse;width:100%}
td,th{text-align:left;padding:.35em .5em;border-bottom:1px solid var(--line);vertical-align:top}
footer{margin-top:3em;color:var(--muted);font-size:.85em;border-top:1px solid var(--line);padding-top:1em}
"""


def page(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><main>{body}
<footer>Integral Productivity · <a href="{REPO}">hub source and registry</a> · content CC-BY-SA-4.0</footer></main></body></html>"""


def root_page(registry: dict) -> str:
    rows = ""
    for prefix, cfg in registry["prefixes"].items():
        title = html.escape(cfg.get("title", prefix.strip("/")))
        source = cfg.get("source", f"https://github.com/Integral-Productivity/{cfg['repo']}")
        rows += (f'<tr><td><a href="{prefix}">{title}</a></td><td><code>{prefix}</code></td>'
                 f'<td><a href="{cfg["turtle"]}">{html.escape(cfg["turtle"].lstrip("/"))}</a></td>'
                 f'<td><a href="{source}">{html.escape(cfg["repo"])}</a></td></tr>')
    body = f"""<h1>Integral Productivity ontologies</h1>
<p>Formal, inspectable, testable vocabularies for the frameworks Integral Productivity uses and creates. Each ontology is a public repository with competency questions, conformance shapes, and architecture decision records; concerns are raised as issues.</p>
<table><tr><th>Ontology</th><th>Path</th><th>Turtle</th><th>Source</th></tr>{rows}</table>
<p class="muted">Every IRI resolves to an HTML page for people and, with <code>Accept: text/turtle</code>, to the ontology's Turtle file.</p>
<p class="muted">Stewardship: Integral Productivity LLC; to be transferred to the Integral Productivity Institute once established.</p>"""
    return page("Integral Productivity ontologies", body)


def not_found_page() -> str:
    return page("Not found", '<h1>Not found</h1><p>No ontology publishes this path. See the <a href="/">list of ontologies</a>.</p>')


def build(out: Path) -> None:
    registry = json.loads((HERE / "registry.json").read_text())
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "CNAME").write_text(HOST + "\n")
    (out / ".nojekyll").write_text("")
    (out / "index.html").write_text(root_page(registry), encoding="utf-8")
    (out / "404.html").write_text(not_found_page(), encoding="utf-8")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "site"
    build(out)
    print(f"built {out}")
