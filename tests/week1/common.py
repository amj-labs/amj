"""Shared test helpers; no runtime, policy, schema, or dataset implementation."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "ml/datasets"


def run(command, **kwargs):
    return subprocess.run(
        [str(part) for part in command], cwd=ROOT, capture_output=True,
        text=True, timeout=30, **kwargs,
    )


def load_dataset():
    for name in ("schema.json", "examples.jsonl"):
        if not (DATASET / name).is_file():
            raise AssertionError(f"ML-001 must add ml/datasets/{name}")
    schema = json.loads((DATASET / "schema.json").read_text())
    records = []
    for number, line in enumerate((DATASET / "examples.jsonl").read_text().splitlines(), 1):
        if not line.strip():
            raise AssertionError(f"Blank dataset record at line {number}")
        records.append(json.loads(line))
    return schema, records
