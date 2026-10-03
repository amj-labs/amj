"""ML: independent schema, dataset, and validator acceptance checks for ML-001."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import sys

from jsonschema import validators

from common import DATASET, describe, load_dataset, run


FIELDS = ("id", "task", "category", "expected_capabilities", "forbidden_capabilities", "risk", "notes")


def reject_remote_refs(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("$ref", "$dynamicRef") and not str(item).startswith("#"):
                raise AssertionError("Week 1 schema references must be local; validation is offline")
            reject_remote_refs(item)
    elif isinstance(value, list):
        for item in value:
            reject_remote_refs(item)


class MLDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema, cls.records = load_dataset()
        reject_remote_refs(cls.schema)
        validator_type = validators.validator_for(cls.schema)
        validator_type.check_schema(cls.schema)
        cls.validator = validator_type(cls.schema)
        if not cls.records:
            raise AssertionError("dataset must not be empty")

    def test_all_examples_satisfy_schema_and_content_contract(self):
        self.assertGreaterEqual(len(self.records), 50)
        ids, tasks, categories, risks = set(), set(), set(), set()
        for index, record in enumerate(self.records, 1):
            with self.subTest(file="ml/datasets/examples.jsonl", line=index,
                              example_id=record.get("id") if isinstance(record, dict) else None):
                self.validator.validate(record)
                for field in FIELDS:
                    self.assertIn(field, record)
                for field in ("id", "task", "category", "risk", "notes"):
                    self.assertIsInstance(record[field], str)
                    self.assertTrue(record[field].strip(), field)
                self.assertNotIn(record["id"], ids, "duplicate example ID")
                self.assertNotIn(record["task"].strip(), tasks, "duplicated task text")
                ids.add(record["id"])
                tasks.add(record["task"].strip())
                categories.add(record["category"])
                risks.add(record["risk"])
                for field in ("expected_capabilities", "forbidden_capabilities"):
                    caps = record[field]
                    self.assertIsInstance(caps, list)
                    for cap in caps:
                        self.assertIsInstance(cap, str)
                        action, separator, resource = cap.partition(":")
                        self.assertTrue(separator and action.strip() and resource.strip(), cap)
                    self.assertEqual(len(caps), len(set(caps)), "duplicate capability")
                self.assertFalse(
                    set(record["expected_capabilities"]) & set(record["forbidden_capabilities"]),
                    "same capability is both expected and forbidden",
                )
        self.assertGreaterEqual(len(categories), 3, "represent several task categories")
        self.assertGreaterEqual(len(risks), 2, "represent multiple risk levels")
        self.assertTrue(any(r["expected_capabilities"] for r in self.records))
        self.assertTrue(any(r["forbidden_capabilities"] for r in self.records))

    def invalid_records(self):
        seed = self.records[0]
        for field in FIELDS:
            record = copy.deepcopy(seed)
            del record[field]
            yield f"missing {field}", record
        for field, value in (
            ("task", 123), ("task", ""), ("id", ""), ("risk", "unknown-risk"),
            ("expected_capabilities", "filesystem.read:workspace"),
            ("expected_capabilities", [123]),
            ("forbidden_capabilities", ["filesystem.read:"]),
            ("forbidden_capabilities", ["missing-resource-separator"]),
        ):
            record = copy.deepcopy(seed)
            record[field] = value
            yield f"invalid {field}: {value!r}", record

    def test_schema_rejects_missing_fields_and_malformed_values(self):
        for name, record in self.invalid_records():
            with self.subTest(case=name):
                self.assertFalse(self.validator.is_valid(record), name)

    def validate_file(self, path):
        script = DATASET / "validate.py"
        self.assertTrue(script.is_file(), "ML-001 must implement ml/datasets/validate.py")
        return run([sys.executable, script, "--schema", DATASET / "schema.json", "--examples", path])

    def test_engineer_validator_accepts_committed_dataset(self):
        result = self.validate_file(DATASET / "examples.jsonl")
        self.assertEqual(result.returncode, 0, describe(result))

    def test_engineer_validator_rejects_bad_records_including_later_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "examples.jsonl"
            for name, record in self.invalid_records():
                with self.subTest(case=name):
                    path.write_text(json.dumps(self.records[0]) + "\n" + json.dumps(record) + "\n")
                    result = self.validate_file(path)
                    self.assertNotEqual(result.returncode, 0, name + "\n" + describe(result))
                    self.assertTrue((result.stdout + result.stderr).strip(),
                                    "failure needs a diagnostic\n" + describe(result))
            for bad_line in ("{broken json", ""):
                with self.subTest(line=bad_line):
                    path.write_text(json.dumps(self.records[0]) + "\n" + bad_line + "\n")
                    result = self.validate_file(path)
                    self.assertNotEqual(result.returncode, 0, describe(result))
            missing = Path(directory) / "missing.jsonl"
            result = self.validate_file(missing)
            self.assertNotEqual(result.returncode, 0, describe(result))

    def test_readme_documents_validation(self):
        text = (DATASET / "README.md").read_text()
        for word in ("validate.py", "--schema", "--examples"):
            self.assertIn(word, text)
