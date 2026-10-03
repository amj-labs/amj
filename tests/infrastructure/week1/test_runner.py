"""Verify diagnostic capture, failure propagation, and timeout cleanup."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import run as runner


class RunnerDiagnostics(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.log = self.root / "step.log"

    def execute(self, source, **kwargs):
        with redirect_stdout(io.StringIO()):
            return runner.execute("fixture", [sys.executable, "-c", source], self.log, **kwargs)

    def test_success_and_failure_preserve_both_output_streams(self):
        for code, status in ((0, "PASS"), (7, "FAIL")):
            with self.subTest(code=code):
                result = self.execute(
                    f"import sys; print('output'); print('diagnostic', file=sys.stderr); sys.exit({code})"
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(result["exit_code"], code)
                text = self.log.read_text()
                for expected in ("output", "diagnostic", "Command:", "Working directory:", "Started:", status):
                    self.assertIn(expected, text)

    def test_missing_executable_is_logged_as_infrastructure_error(self):
        with redirect_stdout(io.StringIO()):
            result = runner.execute("missing", ["/amj-missing-test-dir/command"], self.log)
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("Unable to execute command", self.log.read_text())

    def test_empty_test_discovery_cannot_report_a_pass(self):
        with redirect_stdout(io.StringIO()):
            result = runner.execute("empty", [
                sys.executable, "-m", "unittest", "discover", "-s", str(self.root),
            ], self.log)
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("no tests were discovered", self.log.read_text())

    def test_timeout_keeps_partial_output_and_stops_descendants(self):
        marker = self.root / "orphan"
        child = f"import time; from pathlib import Path; time.sleep(1.6); Path({str(marker)!r}).touch()"
        source = (
            "import subprocess, sys, time; "
            f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
            "print('before timeout', flush=True); time.sleep(30)"
        )
        result = self.execute(source, timeout=1)
        self.assertEqual(result["status"], "TIMEOUT")
        text = self.log.read_text()
        self.assertIn("before timeout", text)
        self.assertIn("TIMEOUT", text)
        time.sleep(0.8)
        self.assertFalse(marker.exists(), "a timed-out test left its child running")

    def test_blocked_step_does_not_execute_stale_command(self):
        marker = self.root / "executed"
        result = self.execute(
            f"from pathlib import Path; Path({str(marker)!r}).touch()", blocked_by="build",
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(marker.exists())
        self.assertIn("prerequisite build", self.log.read_text())

    def test_failed_dependency_still_runs_independent_step_and_writes_summaries(self):
        commands = [
            ("build", [sys.executable, "-c", "raise SystemExit(7)"], None),
            ("dependent", [sys.executable, "-c", "raise SystemExit(99)"], "build"),
            ("independent", [sys.executable, "-c", "print('independent')"], None),
        ]
        github_summary = self.root / "github.md"
        console = io.StringIO()
        with patch.object(runner, "steps_for", return_value=commands), patch.dict(
            os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_STEP_SUMMARY": str(github_summary)},
        ), redirect_stdout(console):
            passed = runner.run_suite("fixture", 1, self.root, 5)
        self.assertFalse(passed)
        summary_path = next(self.root.glob("*/summary.json"))
        summary = json.loads(summary_path.read_text())
        self.assertEqual(summary["status"], "FAIL")
        self.assertEqual([step["status"] for step in summary["steps"]], ["FAIL", "BLOCKED", "PASS"])
        for step in summary["steps"]:
            self.assertTrue((summary_path.parent / step["log"]).is_file())
        self.assertTrue((summary_path.parent / "summary.md").is_file())
        self.assertIn("BLOCKED", github_summary.read_text())
        self.assertIn("::group::fixture/independent", console.getvalue())

    def test_all_suites_run_even_after_a_failure_and_return_nonzero(self):
        with patch.object(sys, "argv", ["run.py", "all"]), patch.object(
            runner, "run_suite", side_effect=[True, True, False, True, True, True],
        ) as suites:
            self.assertEqual(runner.main(), 1)
        self.assertEqual(suites.call_count, 6)
