# Contributing to AMJ

Use Linux, Rust stable with `rustfmt` and `clippy`, and Python 3.12+.
Run commands from the repository root.

## Workspace checks

```bash
cargo fmt --all -- --check
cargo check --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

## Acceptance tests

Install the test dependency in a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r tests/week1/requirements.txt
```

Run the relevant task checks and the shared integration:

```bash
python3 tests/week1/run.py sys
python3 tests/week1/run.py sec
python3 tests/week1/run.py ml
python3 tests/week1/run.py ml-sec
```

Run all completion checks with `python3 tests/week1/run.py all`.
These checks intentionally fail against the scaffold until the corresponding
Week 1 tasks are implemented. The Rust acceptance tests use reference APIs
that engineers must adapt to their chosen public APIs while preserving the
behavioral assertions. Passing the workspace checks alone does not establish
task completion.

The ML ↔ Security integration checks dataset capability and risk compatibility
with actual core types. The other cross-engineer integrations are deferred
until their production interfaces exist. See the
[Week 1 testing guide](tests/week1/README.md) for test contracts, API adaptation,
and required human reviews.

## Pull requests and CI

Run the checks relevant to your task before considering it complete, and include
the commands and results in your PR's validation notes. Follow the acceptance
criteria in the corresponding GitHub issue.

[CI](.github/workflows/ci.yml) runs the workspace checks and four independent
Week 1 completion jobs on pull requests and pushes to `main`. Completion jobs
will remain red until their implementations are available.
