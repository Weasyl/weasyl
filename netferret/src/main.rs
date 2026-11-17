#![forbid(unsafe_code)]

mod args;
mod proto;
mod util;

use std::fmt;
use std::io::{
	self,
	BufReader,
	ErrorKind,
	Read,
	Write,
};
use std::net::{
	self,
	IpAddr,
	Ipv6Addr,
	SocketAddr,
	TcpListener,
	TcpStream,
};
use std::panic;
use std::process::ExitCode;
use std::str;
use std::thread;

use self::args::Conf;
use self::proto::CommandReply;
use self::util::read_n;

// [::]:1080
const BIND: SocketAddr = SocketAddr::new(IpAddr::V6(Ipv6Addr::UNSPECIFIED), 1080);

enum StartupError {
	Io(io::Error),
	Protocol,
	Unsupported,
	ForbiddenDestination {
		domain_name: Vec<u8>,
		port: u16,
	},
	Upstream(io::Error),
}

impl From<io::Error> for StartupError {
	fn from(e: io::Error) -> Self {
		Self::Io(e)
	}
}

impl fmt::Display for StartupError {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match self {
			Self::Io(e) => write!(f, "{e}"),
			Self::Protocol => write!(f, "SOCKS5 protocol error"),
			Self::Unsupported => write!(f, "SOCKS5 unsupported use"),
			Self::ForbiddenDestination {domain_name, port} => {
				let readable_domain_name = String::from_utf8_lossy(domain_name);
				write!(f, "SOCKS5 forbidden connection attempt to {readable_domain_name:?} (port {port})")
			}
			Self::Upstream(e) => write!(f, "error connecting to upstream: {e}"),
		}
	}
}

struct Startup<'a> {
	upstream: TcpStream,
	upstream_host: &'a str,
	client: TcpStream,
}

fn startup(conf: &Conf, client: TcpStream) -> Result<Startup<'_>, StartupError> {
	let mut client = BufReader::new(client);

	let [ver, nmethods] = read_n::<2>(&mut client)?;
	if ver != proto::ver::SOCKS5 || nmethods < 1 {
		return Err(StartupError::Protocol);
	}

	let mut methods = vec![0_u8; usize::from(nmethods)];
	client.read_exact(&mut methods)?;

	if !methods.contains(&proto::auth::NONE) {
		client.into_inner().write_all(&proto::msg::NO_ACCEPTABLE_METHODS)?;
		return Err(StartupError::Unsupported);
	}

	client.get_mut().write_all(&[proto::ver::SOCKS5, proto::auth::NONE])?;

	let [ver, cmd, _rsv, atyp, name_len] = read_n::<5>(&mut client)?;

	if ver != proto::ver::SOCKS5 {
		return Err(StartupError::Protocol);
	}

	if cmd != proto::cmd::CONNECT {
		client.into_inner().write_all(&CommandReply::CommandNotSupported.bytes())?;
		return Err(StartupError::Unsupported);
	}

	if atyp != proto::atyp::DOMAIN_NAME {
		client.into_inner().write_all(&CommandReply::AddressTypeNotSupported.bytes())?;
		return Err(StartupError::Unsupported);
	}

	let mut domain_name = vec![0_u8; usize::from(name_len)];
	client.read_exact(&mut domain_name)?;

	let port = u16::from_be_bytes(read_n::<2>(&mut client)?);

	match (str::from_utf8(&domain_name).map(|n| conf.allowed_upstreams.get(n)), port) {
		(Ok(Some(domain_name)), 443) => {
			// XXX: For simplicity, this doesn’t handle the client disconnecting during the connection attempt – that is, if the client has a shorter timeout than the default, the proxy will still be stuck connecting for the rest of the time.
			let mut upstream = match TcpStream::connect((domain_name as &str, port)) {
				Ok(upstream) => upstream,
				Err(e) => {
					client.into_inner().write_all(&match e.kind() {
						ErrorKind::ConnectionRefused => CommandReply::ConnectionRefused,
						ErrorKind::HostUnreachable => CommandReply::HostUnreachable,
						ErrorKind::NetworkUnreachable => CommandReply::NetworkUnreachable,
						_ => CommandReply::HostUnreachable,
					}.bytes())?;
					return Err(StartupError::Upstream(e));
				}
			};
			let _ = upstream.set_nodelay(true);

			client.get_mut().write_all(&CommandReply::Success.bytes())?;

			// Send anything left in the buffer to the upstream. This operation would ideally be done in `splice_both` to avoid blocking and delaying anything received from the upstream, and to have its errors handled using the same logic, but `BufReader` doesn’t offer a way to take ownership of its buffer. In practice:
			// - `net.ipv4.tcp_wmem`’s default default of 16KiB > `BufReader`’s default buffer capacity of 8KiB, so the buffer will never be large enough to block
			// - this buffer is always empty because the relevant SOCKS clients don’t send preemptively (that’s implied to be against spec)
			// - TLS starts with a message from the client anyway
			upstream.write_all(client.buffer())?;

			Ok(Startup {
				upstream,
				upstream_host: domain_name,
				client: client.into_inner(),
			})
		}
		_ => {
			client.into_inner().write_all(&CommandReply::ConnectionNotAllowed.bytes())?;
			Err(StartupError::ForbiddenDestination {
				domain_name,
				port,
			})
		}
	}
}

fn splice_both(mut a: TcpStream, mut b: TcpStream) -> io::Result<()> {
	// The Rust standard library doesn’t provide anything like Tokio’s `split`, so we waste some fds and introduce new failure paths.
	let mut a2 = a.try_clone()?;
	let mut b2 = b.try_clone()?;

	let a_to_b = thread::spawn(move || {
		match io::copy(&mut a2, &mut b2) {
			Ok(_count) => Ok(()),
			Err(e) => {
				let _ = a2.shutdown(net::Shutdown::Both);
				let _ = b2.shutdown(net::Shutdown::Both);
				Err(e)
			}
		}
	});

	match io::copy(&mut b, &mut a) {
		Ok(_count) => {}
		Err(e) => {
			// Try to avoid having one direction alive while the other isn’t in the event of some unexpected error that only manifests in one direction.
			let _ = a.shutdown(net::Shutdown::Both);
			let _ = b.shutdown(net::Shutdown::Both);
			return Err(e);
		}
	}

	match a_to_b.join() {
		Ok(result) => result,
		Err(thread_panic) => panic::resume_unwind(thread_panic),
	}
}

fn communicate(
	conf: &Conf,
	client: TcpStream,
	peer_addr: SocketAddr,
) {
	let _ = client.set_nodelay(true);

	match startup(conf, client) {
		Err(e) => {
			eprintln!("error: startup with {peer_addr} failed: {e}");
		}
		Ok(Startup {upstream, upstream_host, client}) => {
			if let Err(e) = splice_both(client, upstream) {
				eprintln!("error: proxying between client {peer_addr} and upstream {upstream_host:?} failed: {e}");
			}
		}
	}
}

fn show_usage() {
	eprintln!("Usage: netferret (-a <allowed-upstream>)...");
}

fn main() -> ExitCode {
	use std::env;

	let conf = match args::parse_args(env::args()) {
		Ok(conf) => conf,
		Err(()) => {
			show_usage();
			return ExitCode::FAILURE;
		}
	};

	let listener = match TcpListener::bind(BIND) {
		Ok(l) => l,
		Err(e) => {
			eprintln!("fatal: failed to bind to {BIND}: {e}");
			return ExitCode::FAILURE;
		}
	};

	thread::scope(|s| {
		loop {
			let (stream, peer_addr) = match listener.accept() {
				Ok(t) => t,
				Err(e) if e.kind() == ErrorKind::ConnectionAborted => {
					eprintln!("info: failed to accept a connection: {e}");
					continue;
				}
				Err(e) => {
					eprintln!("fatal: failed to accept a connection: {e}");
					return ExitCode::FAILURE;
				}
			};

			let conf = &conf;
			let _ = thread::Builder::new()
				.name(peer_addr.to_string())
				.spawn_scoped(s, move || communicate(conf, stream, peer_addr));
		}
	})
}
