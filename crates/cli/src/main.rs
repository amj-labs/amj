use std::process::ExitCode;

fn main() -> ExitCode {
    match run() {
        Ok(code) => ExitCode::from(code),
        Err(error) => {
            eprintln!("amj: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<u8, String> {
    let args = std::env::args_os()
        .skip(1)
        .map(|arg| {
            arg.into_string()
                .map_err(|_| "arguments must be valid UTF-8")
        })
        .collect::<Result<Vec<_>, _>>()?;

    if args.first().map(String::as_str) != Some("run") || args.len() < 2 {
        return Err("usage: amj run <command> [args...]".to_owned());
    }

    let command = &args[1];
    let child_args: Vec<&str> = args[2..].iter().map(String::as_str).collect();
    let session = amj_runtime::run(command, &child_args)
        .map_err(|error| format!("could not run {command:?}: {error}"))?;
    let status = session
        .exit_status
        .ok_or("runtime returned a session without an exit status")?;

    if let Some(code) = status.code() {
        return Ok(u8::try_from(code).unwrap_or(1));
    }

    // Match the conventional shell exit code for a child killed by a signal.
    #[cfg(unix)]
    {
        use std::os::unix::process::ExitStatusExt;
        if let Some(signal) = status.signal() {
            return Ok(u8::try_from(128 + signal).unwrap_or(1));
        }
    }
    Ok(1)
}
