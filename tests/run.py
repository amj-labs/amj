"""Run completion checks with diagnostic logs and a machine-readable summary."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shlex
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def steps_for(suite, week=1):
    def python_tests(domain, filename):
        return [
            sys.executable, "-m", "unittest", "discover",
            "-s", str(HERE / domain / f"week{week}"), "-t", str(HERE),
            "-p", filename, "-v",
        ]

    def cargo_tests(domain):
        return ["cargo", "test", "--manifest-path",
                str(HERE / domain / f"week{week}/Cargo.toml"), "--", "--nocapture"]

    manifest = str(HERE / "security" / f"week{week}/Cargo.toml")
    suites = {
        "rust": [
            ("format", ["cargo", "fmt", "--all", "--", "--check"], None),
            ("compile", ["cargo", "check", "--workspace"], None),
            ("clippy", ["cargo", "clippy", "--workspace", "--all-targets", "--", "-D", "warnings"], None),
            ("workspace-tests", ["cargo", "test", "--workspace", "--", "--nocapture"], None),
        ],
        "infra": [("runner-tests", python_tests("infrastructure", "test_runner.py"), None)],
        "sys": [
            ("cli-build", ["cargo", "build", "-p", "amj-cli"], None),
            ("cli-tests", python_tests("systems", "test_cli.py"), "cli-build"),
            ("session-tests", cargo_tests("systems"), None),
        ],
        "sec": [
            ("threat-model", python_tests("security", "test_threat_model.py"), None),
            ("primitive-tests", cargo_tests("security"), None),
        ],
        "ml": [("dataset-tests", python_tests("ml", "test_dataset.py"), None)],
        "ml-sec": [
            ("bridge-build", ["cargo", "build", "--manifest-path", manifest, "--bin", "capability-probe"], None),
            ("compatibility-tests", python_tests("integration", "test_ml_security.py"), "bridge-build"),
        ],
    }
    return suites[suite]


def execute(name, command, log_path, timeout=180, blocked_by=None):
    """Record real subprocess results; a timeout kills its Linux process group."""
    started_at = timestamp()
    start = time.monotonic()
    exit_code, output, status = None, "", "BLOCKED"
    if blocked_by:
        output = f"Not executed: prerequisite {blocked_by} did not pass.\n"
    else:
        env = os.environ.copy()
        env.update(RUST_BACKTRACE="1", PYTHONUNBUFFERED="1", CARGO_TERM_COLOR="never")
        try:
            process = subprocess.Popen(
                command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", env=env,
                start_new_session=True,
            )
            try:
                output, _ = process.communicate(timeout=timeout)
                exit_code = process.returncode
                status = "PASS" if exit_code == 0 else "FAIL"
                # Older Python versions exit 0 for empty discovery; newer ones exit 5.
                if exit_code in (0, 5) and command[1:3] == ["-m", "unittest"] and re.search(
                    r"(?m)^Ran 0 tests\b", output,
                ):
                    status = "ERROR"
                    output += "\nERROR: no tests were discovered; check the test path and pattern.\n"
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                output, _ = process.communicate()
                output += f"\nTIMEOUT: exceeded {timeout:g}s; terminated process group.\n"
                exit_code = process.returncode
                status = "TIMEOUT"
        except OSError as error:
            output = f"Unable to execute command: {error}\n"
            status = "ERROR"
    duration = round(time.monotonic() - start, 3)
    record = {
        "step": name, "status": status, "exit_code": exit_code,
        "duration_seconds": duration, "started_at": started_at,
        "command": command, "cwd": str(ROOT), "log": log_path.name,
    }
    header = (
        f"Step: {name}\nStarted: {started_at}\nWorking directory: {ROOT}\n"
        f"Command: {shlex.join(command)}\n\n"
    )
    footer = f"\nResult: {status} | exit={exit_code} | duration={duration:.3f}s\n"
    log_path.write_text(header + output + footer, encoding="utf-8")
    print(output, end="" if output.endswith("\n") else "\n", flush=True)
    print(footer.strip(), flush=True)
    return record


def run_suite(suite, week, log_root, timeout):
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = log_root / f"week{week}-{suite}-{run_id}"
    directory.mkdir(parents=True)
    records, results = [], {}
    print(f"\n[{suite}] Logs: {directory}", flush=True)
    for index, (name, command, dependency) in enumerate(steps_for(suite, week), 1):
        print(f"\n[{suite}/{name}] {shlex.join(command)}", flush=True)
        github = bool(os.environ.get("GITHUB_ACTIONS"))
        if github:
            print(f"::group::{suite}/{name}", flush=True)
        blocked = dependency if dependency and results[dependency] != "PASS" else None
        record = execute(name, command, directory / f"{index:02d}-{name}.log", timeout, blocked)
        records.append(record)
        results[name] = record["status"]
        if github:
            print("::endgroup::", flush=True)

    passed = all(record["status"] == "PASS" for record in records)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    summary = {
        "suite": suite, "week": week, "status": "PASS" if passed else "FAIL",
        "commit": commit, "python": platform.python_version(),
        "platform": platform.platform(), "steps": records,
    }
    (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    markdown = f"## Week {week} / {suite}: {summary['status']}\n\n"
    markdown += f"Commit: `{commit}`\n\n| Step | Result | Seconds | Exit | Log |\n| --- | --- | ---: | ---: | --- |\n"
    for record in records:
        markdown += (
            f"| {record['step']} | {record['status']} | {record['duration_seconds']:.3f} | "
            f"{record['exit_code']} | {record['log']} |\n"
        )
    (directory / "summary.md").write_text(markdown)
    print(f"\n{markdown}\nLogs: {directory}", flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as stream:
            stream.write(markdown + "\n")
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=("rust", "sys", "sec", "ml", "ml-sec", "infra", "all"))
    parser.add_argument("--week", type=int, choices=(1,), default=1)
    parser.add_argument("--log-dir", type=Path, default=ROOT / "logs/tests")
    parser.add_argument("--timeout", type=float, default=180, help="Seconds per step")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    suites = ("rust", "infra", "sys", "sec", "ml", "ml-sec") if args.suite == "all" else (args.suite,)
    passed = True
    for suite in suites:
        passed = run_suite(suite, args.week, args.log_dir.resolve(), args.timeout) and passed
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
