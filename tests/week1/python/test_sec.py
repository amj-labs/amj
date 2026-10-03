"""Structural checks only; threat-model correctness still requires human review."""
import re
import unittest

from common import ROOT


class ThreatModel(unittest.TestCase):
    def test_document_has_reviewable_sections_and_eight_scenarios(self):
        path = ROOT / "docs/threat-model.md"
        self.assertTrue(path.is_file(), "SEC-001 must add docs/threat-model.md")
        text = path.read_text()
        sections = {}
        for match in re.finditer(r"(?m)^## +([^\n]+)\n([\s\S]*?)(?=^## |\Z)", text):
            sections[match[1].strip().lower()] = match[2].strip()
        required = (
            "trust boundaries", "protected assets", "attacker assumptions",
            "non-goals", "abuse scenarios", "security invariant",
        )
        for heading in required:
            with self.subTest(heading=heading):
                self.assertIn(heading, sections)
                self.assertTrue(sections.get(heading, "").strip())
        scenarios = sections.get("abuse scenarios", "")
        # Each scenario gets its own numbered entry or level-three heading.
        entries = re.findall(r"(?m)^(?:\d+[.)] +|### +)(.+)$", scenarios)
        self.assertGreaterEqual(len(entries), 8, "use 8 numbered entries or ### scenario headings")
        # These are presence checks, not a claim of semantic security assurance.
        invariant = sections.get("security invariant", "").lower()
        for word in ("ml", "deterministic", "override"):
            self.assertIn(word, invariant)
