use amj_core::{Action, Capability, Decision, Resource, RiskLevel};
use amj_sec_acceptance::{capability, risk};

#[test]
fn capabilities_preserve_action_and_resource_identity() {
    let read = capability("filesystem.read:/workspace/src/**").unwrap();
    assert_eq!(
        read,
        Capability {
            action: Action::FilesystemRead,
            resource: Resource::Filesystem {
                path: "/workspace/src/**".into()
            },
        }
    );
    assert_ne!(
        read,
        capability("filesystem.write:/workspace/src/**").unwrap()
    );
    assert_ne!(read, capability("filesystem.read:ssh-keys").unwrap());
    assert_eq!(
        capability("network.connect:api.github.com:443")
            .unwrap()
            .resource,
        Resource::Network {
            endpoint: "api.github.com:443".into()
        }
    );
    assert_eq!(
        capability("process.execute:cargo").unwrap().resource,
        Resource::Process {
            command: "cargo".into()
        }
    );
}

#[test]
fn four_decision_outcomes_remain_distinct() {
    let decisions = [
        Decision::Allow,
        Decision::Deny,
        Decision::AskUser,
        Decision::TerminateSession,
    ];
    for (i, left) in decisions.iter().enumerate() {
        for (j, right) in decisions.iter().enumerate() {
            assert_eq!(left == right, i == j);
        }
    }
}

#[test]
fn risk_labels_map_to_distinct_core_values() {
    let labels = ["low", "medium", "high", "critical"];
    let values = [
        RiskLevel::Low,
        RiskLevel::Medium,
        RiskLevel::High,
        RiskLevel::Critical,
    ];
    for (i, label) in labels.iter().enumerate() {
        assert_eq!(risk(label).unwrap(), values[i]);
        for (j, other) in values.iter().enumerate() {
            assert_eq!(&values[i] == other, i == j);
        }
    }
    assert!(risk("unknown").is_err());
}

#[test]
fn wire_adapter_rejects_unknown_or_missing_capabilities() {
    for wire in [
        "filesystem.delete:/workspace",
        "filesystem.read:",
        "filesystem.read",
        ":x",
    ] {
        assert!(capability(wire).is_err(), "accepted {wire}");
    }
}
