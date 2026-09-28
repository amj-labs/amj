# ADR-0001: Initial AMJ Architecture

## Status

Accepted

## Context

AMJ is a security runtime for autonomous AI agents.

Agents may require access to files, processes, networks, APIs, credentials,
and external tools. Granting unrestricted access to these resources creates
an unnecessarily large security boundary.

AMJ aims to grant only the capabilities required for the current task while
keeping human intervention low.

## Decision

AMJ will initially use:

- Rust for security-sensitive runtime and policy components
- Python for ML and LLM components
- Linux as the first supported platform
- deterministic policy enforcement as the final security authority
- local-first inference
- a monorepo architecture

The initial Rust workspace consists of:

- `amj-core`
- `amj-runtime`
- `amj-policy`
- `amj-cli`

## Security invariant

Machine-learning components may generate recommendations, confidence scores,
anomaly scores, and proposed capabilities.

They may never override deterministic security restrictions.

A hard denial always takes precedence over an ML recommendation.

## Decision outcomes

Security-sensitive actions will eventually resolve to one of:

- `ALLOW`
- `DENY`
- `ASK_USER`
- `TERMINATE_SESSION`

## Future enforcement mechanisms

The architecture is intended to support:

- Linux namespaces
- Landlock
- seccomp
- cgroups
- network isolation
- controlled egress proxying
- credential brokering
- eBPF telemetry
- behavioral anomaly detection
- session auditing and replay

These mechanisms will be added incrementally.

## Consequences

The core authorization model remains independent from any single sandbox
implementation.

Security enforcement remains outside the ML layer.
