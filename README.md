# AMJ

> Task-scoped least-privilege runtime for autonomous AI agents.

AMJ is a local-first security runtime designed to execute autonomous AI agents with the minimum capabilities required for their current task.

Instead of granting agents broad access to the host system, AMJ combines deterministic security policies with task and behavioral analysis to decide whether an action should be:

- automatically allowed,
- automatically denied,
- escalated for human approval, or
- considered severe enough to terminate the session.

Machine-learning components may assist with task understanding, risk assessment, capability inference, and anomaly detection, but they never override deterministic security boundaries.

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