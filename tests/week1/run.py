"""Run strict Week 1 completion gates; missing implementations are failures."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=("sys", "sec", "ml", "ml-sec", "all"))
    args = parser.parse_args()
    def python_tests(name):
        return [
            sys.executable, "-m", "unittest", "discover", "-s", str(HERE / "python"),
            "-p", f"test_{name}.py", "-v",
        ]
    security_manifest = str(HERE / "security/Cargo.toml")
    commands = {
        "sys": [
            ["cargo", "build", "-p", "amj-cli"],
            python_tests("sys"),
            ["cargo", "test", "--manifest-path", str(HERE / "systems/Cargo.toml")],
        ],
        "sec": [
            python_tests("sec"),
            ["cargo", "test", "--manifest-path", security_manifest],
        ],
        "ml": [python_tests("ml")],
        "ml-sec": [
            ["cargo", "build", "--manifest-path", security_manifest, "--bin", "capability-probe"],
            python_tests("ml_sec"),
        ],
    }
    failed = False
    suites = commands if args.suite == "all" else [args.suite]
    for suite in suites:
        for command in commands[suite]:
            print(f"\n[{suite}] {' '.join(command)}", flush=True)
            result = subprocess.run(command, cwd=ROOT, timeout=180)
            failed |= result.returncode != 0
            if result.returncode != 0 and suite == "ml-sec":
                # A failed build is already a failure; never run a stale probe.
                break
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
