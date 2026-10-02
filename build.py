"""Inline registry.json into worker.js and print the deployable script.

Deployment itself goes through the Cloudflare API (Workers script upload +
zone route). This keeps the source of truth in git; the deploy step is:

    python infra/ontology-router/build.py > /tmp/ontology-router.js

then upload the result as the worker script named `ontology-router` and
ensure a route `ontology.integralproductivity.com/*` points at it.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
registry = json.loads((HERE / "registry.json").read_text())
registry.pop("$comment", None)
script = (HERE / "worker.js").read_text().replace("__REGISTRY__", json.dumps(registry, indent=2))
sys.stdout.write(script)
