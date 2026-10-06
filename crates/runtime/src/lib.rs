//! Session, process, and sandbox lifecycle for AMJ.

use std::io;
use std::process::{Command, ExitStatus};
use std::time::SystemTime;
use uuid::Uuid;

/// A unique identifier for one command execution.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct SessionId(Uuid);

impl std::fmt::Display for SessionId {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(formatter)
    }
}

/// The command and lifecycle information for one execution.
#[derive(Debug)]
pub struct Session {
    pub id: SessionId,
    pub command: String,
    pub args: Vec<String>,
    pub started_at: SystemTime,
    pub ended_at: Option<SystemTime>,
    pub exit_status: Option<ExitStatus>,
}

/// Run a command with literal arguments and inherited standard streams.
///
/// Waits for the child to finish before returning its completed session. A
/// nonzero child exit is a completed session, not an error. Errors from spawning
/// or waiting for the child are returned to the caller.
///
/// This initial execution path does not apply sandboxing or policy enforcement.
pub fn run(command: &str, args: &[&str]) -> io::Result<Session> {
    let mut session = Session {
        id: SessionId(Uuid::new_v4()),
        command: command.to_owned(),
        args: args.iter().map(|arg| (*arg).to_owned()).collect(),
        started_at: SystemTime::now(),
        ended_at: None,
        exit_status: None,
    };

    let status = Command::new(command).args(args).status()?;
    session.exit_status = Some(status);
    session.ended_at = Some(SystemTime::now());
    Ok(session)
}
