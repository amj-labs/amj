"""Systems: SYS-001 CLI-to-runtime behavior on Linux."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from common import ROOT, run


class SystemsCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The runner builds first; this also supports direct unittest execution.
        cls.cli = ROOT / "target/debug/amj"
        if not cls.cli.is_file():
            raise AssertionError("Build the CLI first: cargo build -p amj-cli")

    def child(self, source, *args):
        return run([self.cli, "run", sys.executable, "-c", source, *args])

    def test_stdout_stderr_and_success_exit(self):
        result = self.child("import sys; print('hello'); print('diagnostic', file=sys.stderr)")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "hello\n")
        self.assertIn("diagnostic\n", result.stderr)

    def test_nonzero_child_exit_is_preserved(self):
        result = self.child("import sys; sys.exit(23)")
        self.assertEqual(result.returncode, 23, result.stderr)

    def test_arguments_are_literal_and_child_has_finished(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "completed"
            arguments = ["two words", "", "--flag", "; touch SHOULD_NOT_EXIST", "$(echo injected)"]
            source = (
                "import json, pathlib, sys; "
                "pathlib.Path(sys.argv[1]).write_text('finished'); "
                "print(json.dumps(sys.argv[2:]))"
            )
            result = self.child(source, marker, *arguments)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), arguments)
            self.assertEqual(marker.read_text(), "finished")

    def test_missing_command_and_spawn_failure_are_reported(self):
        for command in ([self.cli, "run"], [self.cli, "run", "/amj-missing-test-dir/command"]):
            with self.subTest(command=command):
                result = run(command)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr.strip(), "error must have a diagnostic")
