"""Inline registry.json into worker.js and print the deployable script.

Deployment goes through the Cloudflare API (Workers script upload + zone
route); see .github/workflows/deploy-router.yml. Locally:

    python build.py > /tmp/ontology-router.js
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render() -> str:
    registry = json.loads((HERE / "registry.json").read_text())
    registry.pop("$comment", None)
    return (HERE / "worker.js").read_text().replace("__REGISTRY__", json.dumps(registry, indent=2))


if __name__ == "__main__":
    sys.stdout.write(render())
