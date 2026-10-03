"""Shared test helpers; no runtime, policy, schema, or dataset implementation."""
import json
from pathlib import Path
import subprocess
import shlex

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "ml/datasets"


def run(command, **kwargs):
    command = [str(part) for part in command]
    try:
        return subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, timeout=30, **kwargs,
        )
    except subprocess.TimeoutExpired as error:
        raise AssertionError(
            f"Child command timed out after 30s: {shlex.join(command)}\n"
            f"stdout: {error.stdout!r}\nstderr: {error.stderr!r}"
        ) from error
    except OSError as error:
        raise AssertionError(f"Cannot execute {shlex.join(command)}: {error}") from error


def describe(result):
    return (
        f"Command: {shlex.join(result.args)}\nExit: {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def load_dataset():
    for name in ("schema.json", "examples.jsonl"):
        if not (DATASET / name).is_file():
            raise AssertionError(f"ML-001 must add ml/datasets/{name}")
    schema = json.loads((DATASET / "schema.json").read_text())
    records = []
    for number, line in enumerate((DATASET / "examples.jsonl").read_text().splitlines(), 1):
        if not line.strip():
            raise AssertionError(f"ml/datasets/examples.jsonl:{number}: blank record")
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise AssertionError(
                f"ml/datasets/examples.jsonl:{number}:{error.colno}: {error.msg}"
            ) from error
    return schema, records
