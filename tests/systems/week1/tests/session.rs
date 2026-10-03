//! Reference API only: adapt field access to SYS-001's final API, preserving assertions.
use std::time::SystemTime;

#[test]
fn completed_sessions_record_identity_command_times_and_status() {
    let before = SystemTime::now();
    let first = amj_runtime::run("/bin/sh", &["-c", "exit 0"]).expect("spawn first child");
    let second = amj_runtime::run("/bin/sh", &["-c", "exit 23"]).expect("spawn second child");
    let after = SystemTime::now();

    assert_ne!(
        first.id, second.id,
        "each execution needs its own SessionId"
    );
    assert_eq!(first.command, "/bin/sh");
    assert_eq!(first.args, ["-c", "exit 0"]);
    assert_eq!(second.args, ["-c", "exit 23"]);
    assert_eq!(first.exit_status.expect("completed status").code(), Some(0));
    assert_eq!(
        second.exit_status.expect("completed status").code(),
        Some(23)
    );
    for session in [first, second] {
        let end = session.ended_at.expect("completed session has an end time");
        assert!(before <= session.started_at);
        assert!(session.started_at <= end);
        assert!(end <= after);
    }
}

#[test]
fn spawn_failure_is_an_error_not_a_successful_session() {
    assert!(amj_runtime::run("/amj-nonexistent-test-directory/command", &[]).is_err());
}
