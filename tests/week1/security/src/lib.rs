//! Test-only mapping from the Week 1 dataset wire vocabulary into actual core types.
//! Adapt constructors to SEC-001's API, retaining distinct actions/resources/risks.
use amj_core::{Action, Capability, Resource, RiskLevel};

pub fn capability(wire: &str) -> Result<Capability, String> {
    let (action, target) = wire.split_once(':').ok_or("missing resource separator")?;
    if target.trim().is_empty() {
        return Err("empty resource".into());
    }
    let (action, resource) = match action {
        "filesystem.read" => (
            Action::FilesystemRead,
            Resource::Filesystem {
                path: target.into(),
            },
        ),
        "filesystem.write" => (
            Action::FilesystemWrite,
            Resource::Filesystem {
                path: target.into(),
            },
        ),
        "network.connect" => (
            Action::NetworkConnect,
            // Dataset targets may be symbolic ("arbitrary") or host:port.
            Resource::Network {
                endpoint: target.into(),
            },
        ),
        "process.execute" => (
            Action::ProcessExecute,
            Resource::Process {
                command: target.into(),
            },
        ),
        _ => return Err(format!("unknown action: {action}")),
    };
    Ok(Capability { action, resource })
}

pub fn risk(wire: &str) -> Result<RiskLevel, String> {
    match wire {
        "low" => Ok(RiskLevel::Low),
        "medium" => Ok(RiskLevel::Medium),
        "high" => Ok(RiskLevel::High),
        "critical" => Ok(RiskLevel::Critical),
        _ => Err(format!("unknown risk: {wire}")),
    }
}
