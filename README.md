# AMJ

> Task-scoped least-privilege runtime for autonomous AI agents.

AMJ is a local-first security runtime designed to execute autonomous AI agents with the minimum capabilities required for their current task.

AMJ is intended to combine deterministic security policies with task and behavioral analysis to decide whether an action should be:

- automatically allowed,
- automatically denied,
- escalated for human approval, or
- considered severe enough to terminate the session.

Machine-learning components may assist with task understanding, risk assessment, capability inference, and anomaly detection, but they never override deterministic security boundaries.

## Current status

AMJ is in early development. The repository currently contains a Rust workspace
scaffold, and the CLI prints an introductory banner. Runtime enforcement and ML
components are planned.

## Core goals

- Task-scoped least privilege
- Minimal human interruptions
- Local-first inference
- Linux sandboxing
- Secure credential handling
- Runtime behavioral monitoring
- Auditable execution
- Session replay

## Initial architecture

AMJ is being developed as a monorepo.

```text
amj/
├── crates/
│   ├── cli/
│   ├── core/
│   ├── runtime/
│   └── policy/
├── ml/
│   ├── task_analyzer/
│   ├── risk_model/
│   └── datasets/
├── docs/
│   └── adr/
├── scripts/
└── tests/
```

Rust (edition 2024) is used for the runtime and security components. Python is
planned for ML components. Linux is the first supported platform. See the
[initial architecture decision](docs/adr/0001-initial-architecture.md).

## Getting started

On Linux with Rust stable, run from the repository root:

```bash
cargo build --workspace
cargo run -p amj-cli
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and
contribution checks.

## License

[Apache License 2.0](LICENSE).
