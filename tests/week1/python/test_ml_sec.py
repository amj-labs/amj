"""Real Week 1 interface: committed ML records must map to actual core types."""
import unittest

from common import ROOT, load_dataset, run


class DatasetSecurityCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = ROOT / "tests/week1/security/target/debug/capability-probe"
        if not cls.probe.is_file():
            raise AssertionError("build the security acceptance probe first")

    def test_all_expected_forbidden_capabilities_and_risks_are_representable(self):
        _, records = load_dataset()
        self.assertTrue(records)
        values = set()
        for record in records:
            values.update(("--capability", value) for value in record["expected_capabilities"])
            values.update(("--capability", value) for value in record["forbidden_capabilities"])
            values.add(("--risk", record["risk"]))
        for mode, value in sorted(values):
            with self.subTest(mode=mode, value=value):
                result = run([self.probe, mode, value])
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_probe_rejects_vocabulary_drift(self):
        for mode, value in (
            ("--capability", "filesystem.teleport:workspace"),
            ("--capability", "filesystem.read:"),
            ("--capability", "risk:low"),
            ("--risk", "unknown"),
        ):
            with self.subTest(mode=mode, value=value):
                self.assertNotEqual(run([self.probe, mode, value]).returncode, 0)
