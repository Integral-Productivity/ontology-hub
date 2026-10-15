"""Unit tests for smoke.py's planning logic: which checks run for each
registered prefix, and how an unreleased prefix is treated (ADR-0004).
No network: only the pure functions are exercised.

    python -m unittest discover -s tests
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import smoke  # noqa: E402

RELEASED = {"repo": "a-ontology", "mode": "project-site", "turtle": "/a.ttl", "title": "A"}
UNRELEASED = {"repo": "b-ontology", "mode": "project-site", "turtle": "/b.ttl", "title": "B", "listed": False}
REGISTRY = {"origin": "https://example.github.io", "prefixes": {"/a/": RELEASED, "/b/": UNRELEASED}}


def kinds(checks):
    return {c.kind: c.required for c in checks}


class Published(unittest.TestCase):
    def test_listed_absent_or_true_is_published(self):
        self.assertTrue(smoke.is_published(RELEASED))
        self.assertTrue(smoke.is_published({**RELEASED, "listed": True}))

    def test_listed_false_is_unreleased(self):
        self.assertFalse(smoke.is_published(UNRELEASED))


class PrefixChecks(unittest.TestCase):
    def test_released_prefix_requires_page_turtle_negotiation_and_routing(self):
        self.assertEqual(
            kinds(smoke.prefix_checks("/a/", RELEASED)),
            {"routing": True, "negotiation": True, "page": True, "turtle": True},
        )

    def test_unreleased_prefix_still_requires_routing_and_negotiation(self):
        # The Worker routes and negotiates every registered entry, released or
        # not, so those are asserted. The page and Turtle file only exist once
        # the ontology's site is live, so they are reported as pending.
        self.assertEqual(
            kinds(smoke.prefix_checks("/b/", UNRELEASED)),
            {"routing": True, "negotiation": True, "page": False, "turtle": False},
        )

    def test_check_names_name_the_prefix_and_its_turtle(self):
        names = " ".join(c.name for c in smoke.prefix_checks("/a/", RELEASED))
        self.assertIn("/a/", names)
        self.assertIn("/a.ttl", names)


class Outcome(unittest.TestCase):
    def test_outcomes(self):
        self.assertEqual(smoke.outcome(True, required=True), "PASS")
        self.assertEqual(smoke.outcome(False, required=True), "FAIL")
        self.assertEqual(smoke.outcome(False, required=False), "PEND")
        self.assertEqual(smoke.outcome(True, required=False), "PASS")

    def test_only_fail_counts_against_the_exit_code(self):
        self.assertEqual(smoke.failures(["PASS", "PEND", "PEND", "PASS"]), 0)
        self.assertEqual(smoke.failures(["PASS", "FAIL", "PEND"]), 1)


class LandingPage(unittest.TestCase):
    HUB = "<h1>Integral Productivity ontologies</h1>"

    def test_lists_every_published_prefix_and_hides_unreleased(self):
        ok, _ = smoke.landing_verdict(self.HUB + '<a href="/a/">A</a>', REGISTRY)
        self.assertTrue(ok)

    def test_fails_when_a_published_prefix_is_missing(self):
        ok, detail = smoke.landing_verdict(self.HUB, REGISTRY)
        self.assertFalse(ok)
        self.assertIn("/a/", detail)

    def test_fails_when_an_unreleased_prefix_leaks(self):
        ok, detail = smoke.landing_verdict(self.HUB + '<a href="/a/">A</a><a href="/b/">B</a>', REGISTRY)
        self.assertFalse(ok)
        self.assertIn("/b/", detail)

    def test_fails_when_not_the_hub_page(self):
        ok, _ = smoke.landing_verdict('<a href="/a/">A</a>', REGISTRY)
        self.assertFalse(ok)


class AllChecks(unittest.TestCase):
    def test_every_prefix_in_registry_json_is_checked(self):
        registry = json.loads((ROOT / "registry.json").read_text())
        names = " ".join(c.name for c in smoke.build_checks(registry))
        for prefix, cfg in registry["prefixes"].items():
            self.assertIn(prefix, names)
            self.assertIn(cfg["turtle"], names)


if __name__ == "__main__":
    unittest.main()
