from __future__ import annotations

import abc
import logging
import os
import socket
from abc import abstractmethod
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from weasyl.config import config_obj


logger = logging.getLogger(__name__)

_socket_timeout = float(config_obj.get("badgr", "socket_timeout"))


class _Remote(abc.ABC):

    @abstractmethod
    def validate(self) -> None:
        ...

    @abstractmethod
    def connect(self) -> socket.socket:
        ...


class _TcpRemote(_Remote):

    host: str
    port: int

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def validate(self) -> None:
        try:
            socket.getaddrinfo(self.host, self.port, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            logger.warning("badgr server %s:%d does not currently resolve", self.host, self.port)

    def connect(self) -> socket.socket:
        return socket.create_connection((self.host, self.port), timeout=_socket_timeout)


class _UnixRemote(_Remote):

    path: Path

    def __init__(self, path: os.PathLike):
        self.path = Path(path)

    def validate(self) -> None:
        if not self.path.is_socket():
            logger.warning("badgr server %s is not currently a Unix socket", self.path)

    def connect(self) -> socket.socket:
        sock = socket.socket(socket.AF_UNIX)
        sock.settimeout(_socket_timeout)
        try:
            sock.connect(bytes(self.path))
        except Exception:
            sock.close()
            raise
        return sock


def _parse_server(s: str) -> _Remote:
    parts = s.rsplit(":", 1)
    if len(parts) == 1:
        return _UnixRemote(parts[0])

    return _TcpRemote(parts[0], int(parts[1]))


def _validate_servers(servers) -> None:
    for server in servers:
        server.validate()


_servers = tuple(map(_parse_server, config_obj.get("badgr", "servers").split()))

if not _servers:
    raise RuntimeError("no badgr servers configured")

_validate_servers(_servers)  # TODO: might want to do this only for one process, and in the background

_FILE_TYPES = {
    b"GIF": "gif",
    b"JPEG": "jpg",
    b"PNG": "png",
    b"WEBP": "webp",
}
"""A mapping to the values used in `media.file_type`."""

_TERMINATOR = b"\n--END--\n"


class UnsupportedFormat(Exception):

    __slots__ = ()


@dataclass(eq=False, frozen=True, kw_only=True, slots=True)
class Result:

    original_file_type: str
    original_width: int
    original_height: int
    output_file_type: str
    output_width: int
    output_height: int
    output: bytes


def _expect_header(header: bytes, line: bytes) -> bytes:
    if line.startswith(header) and line.endswith(b"\n"):
        return line[len(header):-1]

    raise RuntimeError(f"Image worker returned {line!r} instead of expected header {header!r}")


def _check_dim(s: bytes) -> int:
    if 1 <= len(s) <= 5 and s.isdigit() and not s.startswith(b"0"):
        return int(s)

    raise RuntimeError(f"Image worker returned invalid dimension {s!r}")


def _create(header: bytes, image_bytes: bytes) -> Result:
    for ni, server in enumerate(_servers, start=-len(_servers)):
        try:
            sock = server.connect()
        except OSError:
            if ni == -1:
                raise

            logger.warning("Failed to connect to badgr server, trying next", exc_info=True)
        else:
            break

    with sock:
        sock.sendall(header)
        sock.sendall(image_bytes)
        sock.shutdown(socket.SHUT_WR)

        sock.settimeout(60)

        with sock.makefile("rb") as f:
            first_line = f.readline()
            if first_line.startswith(b"error="):
                if first_line == b"error=unsupported-format\n":
                    raise UnsupportedFormat

                raise RuntimeError(f"Image worker returned {first_line!r}")

            original_file_type = _FILE_TYPES[_expect_header(b"original_format=", first_line)]
            original_width = _check_dim(_expect_header(b"original_width=", f.readline(32)))
            original_height = _check_dim(_expect_header(b"original_height=", f.readline(32)))
            output_file_type = _FILE_TYPES[_expect_header(b"output_format=", f.readline(32))]
            output_width = _check_dim(_expect_header(b"output_width=", f.readline(32)))
            output_height = _check_dim(_expect_header(b"output_height=", f.readline(32)))
            match f.readline(32):
                case b"\n": pass
                case unexpected:
                    raise RuntimeError(f"Image worker returned unexpected data: {unexpected!r}")

            output = f.read()

    if not output.endswith(_TERMINATOR):
        raise RuntimeError("Image worker returned data without expected terminator")
    output = output[:-len(_TERMINATOR)]  # XXX: unsatisfying copy, but it's hard to avoid

    return Result(
        original_file_type=original_file_type,
        original_width=original_width,
        original_height=original_height,
        output_file_type=output_file_type,
        output_width=output_width,
        output_height=output_height,
        output=output,
    )


def _create_crop_fn(op: bytes):
    def create_crop(image_bytes: bytes, x1: int, y1: int, x2: int, y2: int) -> Result:
        if (
            0 <= x1 < x2 <= 0x3fff
            and 0 <= y1 < y2 <= 0x3fff
        ):
            w = x2 - x1
            h = y2 - y1
        else:
            x1 = y1 = w = h = 0

        return _create(b"%s %d %d %d %d\n" % (op, x1, y1, w, h), image_bytes)

    return create_crop


create_cover = partial(_create, b"cover\n")
create_thumbnail = partial(_create, b"thumbnail 0 0 0 0\n")
create_avatar_source = partial(_create, b"avatar-source\n")
create_banner = partial(_create, b"banner\n")

create_avatar = _create_crop_fn(b"avatar")
create_thumbnail_crop = _create_crop_fn(b"thumbnail")
