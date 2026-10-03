"""ML ↔ Security: committed ML records must map to actual core types."""
import unittest

from common import ROOT, describe, load_dataset, run


class DatasetSecurityCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = ROOT / "tests/security/week1/target/debug/capability-probe"
        if not cls.probe.is_file():
            raise AssertionError("build the security acceptance probe first")

    def test_all_expected_forbidden_capabilities_and_risks_are_representable(self):
        _, records = load_dataset()
        self.assertTrue(records)
        for line, record in enumerate(records, 1):
            values = [
                (field, "--capability", value)
                for field in ("expected_capabilities", "forbidden_capabilities")
                for value in record[field]
            ]
            values.append(("risk", "--risk", record["risk"]))
            for field, mode, value in values:
                with self.subTest(file="ml/datasets/examples.jsonl", line=line,
                                  example_id=record["id"], field=field, value=value):
                    result = run([self.probe, mode, value])
                    self.assertEqual(result.returncode, 0, describe(result))

    def test_probe_rejects_vocabulary_drift(self):
        for mode, value in (
            ("--capability", "filesystem.teleport:workspace"),
            ("--capability", "filesystem.read:"),
            ("--capability", "risk:low"),
            ("--risk", "unknown"),
        ):
            with self.subTest(mode=mode, value=value):
                result = run([self.probe, mode, value])
                self.assertNotEqual(result.returncode, 0, describe(result))
