//! Test fixture only; this is not a production policy parser or authorization path.
fn main() {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let result = match args.as_slice() {
        [mode, value] if mode == "--risk" => amj_sec_acceptance::risk(value).map(|_| ()),
        [mode, value] if mode == "--capability" => {
            amj_sec_acceptance::capability(value).map(|_| ())
        }
        _ => Err("usage: capability-probe (--risk | --capability) VALUE".into()),
    };
    if let Err(error) = result {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
