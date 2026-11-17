//! Command-line argument parsing.

use std::collections::HashSet;

pub struct Conf {
	pub allowed_upstreams: HashSet<String>,
}

pub fn parse_args(args: impl IntoIterator<Item = String>) -> Result<Conf, ()> {
	let mut result = Conf {
		allowed_upstreams: HashSet::new(),
	};
	let mut allowed_next = false;

	for mut arg in args.into_iter().skip(1) {
		if allowed_next {
			allowed_next = false;
			result.allowed_upstreams.insert(arg);
		} else if arg == "-a" {
			allowed_next = true;
		} else if arg.starts_with("-a") {
			arg.replace_range(..2, "");
			result.allowed_upstreams.insert(arg);
		} else {
			return Err(());
		}
	}

	if result.allowed_upstreams.is_empty() {
		Err(())
	} else {
		Ok(result)
	}
}
