//! SOCKS5 protocol constants and structures; see RFC 1928.

/// versions
pub mod ver {
	pub const SOCKS5: u8 = 0x05;
}

/// authentication methods
pub mod auth {
	pub const NONE: u8 = 0x00;
}

pub mod msg {
	pub const NO_ACCEPTABLE_METHODS: [u8; 1] = [0xff];
}

/// commands
pub mod cmd {
	pub const CONNECT: u8 = 0x01;
}

/// address types
pub mod atyp {
	pub const IPV4: u8 = 0x01;
	pub const DOMAIN_NAME: u8 = 0x03;
}

#[derive(Copy, Clone, Debug)]
pub enum CommandReply {
	Success = 0x00,
	ConnectionNotAllowed = 0x02,
	NetworkUnreachable = 0x03,
	HostUnreachable = 0x04,
	ConnectionRefused = 0x05,
	CommandNotSupported = 0x07,
	AddressTypeNotSupported = 0x08,
}

impl CommandReply {
	pub const fn bytes(self) -> [u8; 10] {
		[
			ver::SOCKS5,             // ver
			self as u8,	             // rep
			0x00,                    // reserved

			// A dummy address and port, even for a success reply to a CONNECT command.
			// The client doesn’t need this information, though RFC 1928 doesn’t say anything about an option to omit it.
			atyp::IPV4,              // atyp
			0x00, 0x00, 0x00, 0x00,  // bnd.addr
			0x00, 0x00,              // bnd.port
		]
	}
}
