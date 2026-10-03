"""Systems: SYS-001 CLI-to-runtime behavior on Linux."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from common import ROOT, describe, run


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
        self.assertEqual(result.returncode, 0, describe(result))
        self.assertEqual(result.stdout, "hello\n", describe(result))
        self.assertIn("diagnostic\n", result.stderr, describe(result))

    def test_nonzero_child_exit_is_preserved(self):
        result = self.child("import sys; sys.exit(23)")
        self.assertEqual(result.returncode, 23, describe(result))

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
            self.assertEqual(result.returncode, 0, describe(result))
            try:
                forwarded = json.loads(result.stdout)
            except json.JSONDecodeError:
                self.fail("Child output is not the expected JSON:\n" + describe(result))
            self.assertEqual(forwarded, arguments, describe(result))
            self.assertTrue(marker.is_file(), "Child did not finish:\n" + describe(result))
            self.assertEqual(marker.read_text(), "finished", describe(result))

    def test_missing_command_and_spawn_failure_are_reported(self):
        for command in ([self.cli, "run"], [self.cli, "run", "/amj-missing-test-dir/command"]):
            with self.subTest(command=command):
                result = run(command)
                self.assertNotEqual(result.returncode, 0, describe(result))
                self.assertTrue(result.stderr.strip(), "error must have a diagnostic\n" + describe(result))
