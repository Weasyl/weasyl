#!/usr/bin/env python3
# This can be adapted to work with streams instead of making several in-memory copies of everything, but it isn’t currently worth the complexity since the files only go up to hundreds of kilobytes.
import argparse
import gzip
import hashlib
import json
import tarfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tarfile import TarInfo


parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path, help="A path to a new (not yet existing) directory for the container image. If omitted, no output will be written.")
parser.add_argument("executable", type=Path, help="The path to the netferret executable.")


@dataclass(frozen=True, slots=True)
class Blob:
	sha256: str
	size: int

	@property
	def digest(self) -> str:
		return f"sha256:{self.sha256}"


def hash_blob(data) -> Blob:
	return Blob(
		sha256=hashlib.sha256(data).hexdigest(),
		size=len(data),
	)


class ContainerImageDirectory:
	root: Path | None

	def __init__(self, root: Path | None) -> None:
		self.root = root

	def write_blob(self, data) -> Blob:
		blob = hash_blob(data)

		if self.root is not None:
			with open(self.root / "blobs" / "sha256" / blob.sha256, "wb") as f:
				f.write(data)

		return blob

	def write_json(self, data) -> Blob:
		return self.write_blob(json.dumps(data).encode())


def main() -> None:
	args = parser.parse_args()
	image = ContainerImageDirectory(args.out)

	with args.executable.open("rb") as f:
		netferret = f.read()

	if image.root is not None:
		image.root.mkdir()
		(image.root / "blobs").mkdir()
		(image.root / "blobs" / "sha256").mkdir()

	rootfs_file = BytesIO()

	with tarfile.open(fileobj=rootfs_file, mode="w") as tar:
		ti = TarInfo("netferret")
		ti.size = len(netferret)
		ti.mode = 0o755
		tar.addfile(ti, BytesIO(netferret))

	rootfs = hash_blob(rootfs_file.getbuffer())
	gzip_rootfs = image.write_blob(gzip.compress(rootfs_file.getbuffer(), mtime=0))

	config = image.write_json({
		"schemaVersion": 2,
		"architecture": "amd64",
		"os": "linux",
		"config": {
			"Entrypoint": ["/netferret"],
		},
		"rootfs": {
			"type": "layers",
			"diff_ids": [
				rootfs.digest,
			],
		},
	})

	manifest = image.write_json({
		"schemaVersion": 2,
		"mediaType": "application/vnd.oci.image.manifest.v1+json",
		"config": {
			"mediaType": "application/vnd.oci.image.config.v1+json",
			"digest": config.digest,
			"size": config.size,
		},
		"layers": [
			{
				"mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
				"digest": gzip_rootfs.digest,
				"size": gzip_rootfs.size,
			},
		],
		"annotations": {
			"org.opencontainers.image.source": "https://github.com/Weasyl/weasyl",
		},
	})

	index = {
		"schemaVersion": 2,
		"mediaType": "application/vnd.oci.image.index.v1+json",
		"manifests": [
			{
				"mediaType": "application/vnd.oci.image.manifest.v1+json",
				"digest": manifest.digest,
				"size": manifest.size,
				"platform": {
					"architecture": "amd64",
					"os": "linux",
				},
				"annotations": {
					"org.opencontainers.image.ref.name": "0.1.0",
				},
			},
		],
	}

	print("Digest:", manifest.digest)

	if image.root is not None:
		with open(image.root / "index.json", "w", newline="") as f:
			json.dump(index, f)

		with open(image.root / "oci-layout", "w", newline="") as f:
			json.dump({"imageLayoutVersion": "1.0.0"}, f)


if __name__ == "__main__":
	main()
