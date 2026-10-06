//! Shared domain types and security primitives for AMJ.
#[derive(Debug, PartialEq, Eq)]
pub enum Action {
    FilesystemRead,
    FilesystemWrite,
    NetworkConnect,
    ProcessExecute,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Resource {
    Filesystem { path: String },
    Network { endpoint: String },
    Process { command: String },
}

#[derive(Debug, PartialEq, Eq)]
pub struct Capability {
    pub action: Action,
    pub resource: Resource,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Decision {
    Allow,
    Deny,
    AskUser,
    TerminateSession,
}

#[derive(Debug, PartialEq, Eq)]
pub enum RiskLevel {
    Low,
    Medium,
    High,
    Critical,
}
