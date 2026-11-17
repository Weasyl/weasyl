use std::io;

/// Reads a fixed number of bytes.
pub fn read_n<const N: usize>(mut r: impl io::Read) -> io::Result<[u8; N]> {
	let mut result = [0; N];
	r.read_exact(&mut result)?;
	Ok(result)
}
