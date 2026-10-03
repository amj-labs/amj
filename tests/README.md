# Acceptance tests

These are executable completion contracts for SYS-001, SEC-001, and ML-001.
They intentionally fail against the initial scaffold. Missing files, missing
APIs, and unimplemented behavior are failures, never skips or expected passes.
No production runtime, security primitives, threat model, schema, validator,
or training examples are implemented here.

Tests are grouped by domain, then by week:

```text
tests/
├── systems/week1/         # CLI tests and Rust session tests
├── security/week1/        # Threat model, Rust primitives, and test bridge
├── ml/week1/              # Schema, dataset, and validator tests
├── integration/week1/     # ML ↔ Security compatibility tests
├── infrastructure/week1/  # Logging and runner regression tests
├── common.py              # Shared test helpers
├── requirements.txt       # Python test dependencies
└── run.py                 # Test runner used locally and in CI
```

Run from the repository root (Linux, Rust stable, Python 3.12+):

```bash
python3 -m pip install -r tests/requirements.txt
python3 tests/run.py sys
python3 tests/run.py sec
python3 tests/run.py ml
python3 tests/run.py ml-sec
```

Week 1 is the default; `--week 1` can be specified explicitly. It is currently
the only configured week. New weeks should add domain subdirectories and runner
entries when their real contracts are defined.

Run everything, including workspace checks and logging regression tests, with
`python3 tests/run.py all`. These can also run separately:

```bash
python3 tests/run.py rust
python3 tests/run.py infra
```

Normal Rust commands remain available:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

The acceptance crates are separate workspaces, so one engineer's missing Rust
API does not prevent another engineer's suite or normal workspace tests from
running. CI runs all four gates as independent PR jobs with fail-fast disabled.
The matrix will remain red until the corresponding tasks are implemented;
passing the original workspace checks alone does not mean a Week 1 task is done.
An individual task can complete once its own gate passes; ML ↔ Security becomes
a shared completion requirement once both sides are available.

## Diagnosing failures

Each invocation prints the exact log directory, under ignored `logs/tests/`.
Runs have separate timestamped directories, so a rerun does not overwrite the
previous failure. Each directory contains:

- A numbered `.log` file per step, with the exact command, working directory,
  UTC start time, combined stdout/stderr, exit code, result, and duration.
- `summary.md`: a compact table of steps and their results.
- `summary.json`: the same results in a structured format, plus the Git commit,
  Python version, and platform. The commit identifies HEAD; local uncommitted
  changes can still affect the result.

Result labels are `PASS`, `FAIL`, `ERROR` (command could not start), `TIMEOUT`,
or `BLOCKED` (a prerequisite build failed). Every result other than `PASS` makes
the suite return nonzero. Independent steps still run after a failure; dependent
tests do not execute an old binary after a failed build.
An empty unittest discovery also fails, so a bad path cannot silently turn green.

Python tests run verbosely, showing test names and assertion tracebacks.
Subprocess assertions include the command, exit code, stdout, and stderr.
Dataset failures identify the source line and example ID; compatibility tests
also identify the field and capability/risk value. Rust tests use `--nocapture`
and `RUST_BACKTRACE=1` so panic output and stack traces are preserved.

Start with `summary.md`, then open the log for the first failing prerequisite.
For example, if `bridge-build` is `FAIL` and `compatibility-tests` is `BLOCKED`,
fix the compiler error in `01-bridge-build.log` before investigating the dataset.
Logs provide evidence of the failure; a human still determines its root cause.

The default timeout is 180 seconds per step. A timeout preserves output already
written and terminates the step's Linux process group. Adjust when necessary:

```bash
python3 tests/run.py sys --week 1 --timeout 300
python3 tests/run.py ml --log-dir /tmp/amj-test-logs
```

In GitHub Actions, output is grouped by step and the job summary includes the
result table. Logs are uploaded with `if: always()` as `test-logs-rust-*` and
`test-logs-week1-<suite>-*`, retained for seven days. Open the workflow run in the
Actions tab, inspect its summary, then download the relevant artifact. A failed
test stays failed even if log upload succeeds. If setup fails before the runner
starts, use that setup step's GitHub log; no test artifact may exist yet.

## SYS-001

`sys` builds the real CLI and checks child stdout/stderr, literal arguments
(including spaces, an empty argument, shell syntax, and a flag), successful and
nonzero exit codes, synchronous completion, and useful failures for missing or
unspawnable commands. It also calls the real runtime from Rust, checking unique
session IDs, stored command/arguments, timestamps, captured exit status, and
spawn failure. It does not expect sandboxing or policy enforcement.

The Rust test uses a **reference API**, not a mandated production design:

```text
amj_runtime::run(&str, &[&str]) -> Result<Session, ...>
Session: id, command, args, started_at, ended_at, exit_status
```

Adapt the calls/field access in `systems/week1/tests/session.rs` to the chosen public
API as part of SYS-001. Preserve every behavioral assertion and test the real
runtime; do not replace it with a fake or remove the test. Use SystemTime or
adapt the timestamp comparisons to the actual clock type. The CLI black-box
tests require no API adaptation.

## SEC-001

`sec` constructs real filesystem, network, and process capabilities; verifies
action/resource identity; checks four distinct decisions and distinct risk
levels; and exercises the test-only wire adapter's rejection cases. Nothing
asserts actual hard-deny enforcement, which is outside this ticket.

`security/week1/src/lib.rs` and `security/week1/tests/primitives.rs` use reference enum and
field names. Adapt their constructors/accessors to SEC-001's chosen types while
preserving assertions. This deliberately leaves production type design to the
engineer. The bridge must construct actual `amj_core` types, not just check a
string allowlist. Initial wire actions are `filesystem.read`, `filesystem.write`,
`network.connect`, and `process.execute`; initial risk labels are `low`,
`medium`, `high`, and `critical`. Extend the bridge with genuine core mappings
if the engineers agree on additional vocabulary. The adapter is test-only,
not a production parser or policy engine.

The document check requires `docs/threat-model.md` with these level-two sections:

- Trust boundaries
- Protected assets
- Attacker assumptions
- Non-goals
- Abuse scenarios (at least eight numbered entries or level-three headings)
- Security invariant (explicitly discuss ML, deterministic controls, and override)

**Human review is also required:** describe all seven issue trust boundaries,
assets, plausible attacker assumptions, concrete abuse cases with consequences,
and the invariant that ML cannot override deterministic hard denies. The
structural test cannot prove the document is correct or that a security
invariant is enforced. If serialization is added, add actual round-trip and
malformed-input tests in `amj-core`; no serializer is required by these tests.

## ML-001

The tests adopt the issue's example field names, plus required `notes`:
`id`, `task`, `category`, `expected_capabilities`, `forbidden_capabilities`,
`risk`, and `notes`. Capabilities are `action:resource` strings; split only on
the first colon, so a target can contain a port. Lists may be empty (e.g. a
malicious task requiring no permissions), but the dataset must contain both
expected and forbidden capabilities overall. Unknown actions are checked by
the ML ↔ Security gate, not by inventing a production capability registry.

`ml` independently checks the engineer's JSON Schema and all JSONL records:
at least 50 records, unique IDs and task texts, nonempty descriptive fields,
at least three categories and two risks, no duplicate capabilities or exact
expected/forbidden overlap. It mutates a real example to verify the schema
rejects missing required fields, wrong types, empty values, malformed capability
strings, and unknown risk labels. Schema references must be local so the tests
do not fetch external schemas.

Implement the validator entry point as:

```bash
python3 ml/datasets/validate.py --schema ml/datasets/schema.json --examples ml/datasets/examples.jsonl
```

Exit zero for valid files; nonzero with a diagnostic for invalid files. Tests
invoke this real script against the committed dataset and temporary files,
including invalid records on later lines, invalid JSON, blank records, and a
missing file. The dataset README must document this command. The tests do not
generate the dataset or implement its validator.

**Human review is also required:** confirm manual authorship, coverage of every
task family listed in ML-001, realistic ambiguous cases, and correctness of
expected/forbidden capabilities and rationale. Automated diversity checks do
not establish annotation quality.

## Cross-engineer coverage

| Pair/pipeline | Week 1 decision |
| --- | --- |
| ML ↔ Security | Implemented: every committed expected/forbidden capability and risk maps into real core types through a Rust test probe; unknown vocabulary is rejected. |
| ML ↔ Systems | Deferred: the runtime consumes commands, not dataset records or inferred capabilities. |
| Systems ↔ Security | Deferred: SYS-001 does not evaluate policy or authorize processes; a dependency on `amj-core` alone is not a behavioral interface. |
| ML ↔ Systems ↔ Security | Deferred: no inference-to-authorization-to-execution path exists in Week 1. |

Add the deferred integration tests when production interfaces actually exist.
Do not execute dataset commands, infer policies, or simulate enforcement just
to claim a pipeline test. `ml-sec` is data/type compatibility only; it does not
claim policy enforcement or model accuracy.

When changing acceptance Rust code, format and lint its separate workspaces:

```bash
cargo fmt --manifest-path tests/systems/week1/Cargo.toml -- --check
cargo fmt --manifest-path tests/security/week1/Cargo.toml -- --check
cargo clippy --manifest-path tests/systems/week1/Cargo.toml --all-targets -- -D warnings
cargo clippy --manifest-path tests/security/week1/Cargo.toml --all-targets -- -D warnings
```
