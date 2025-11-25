from collections.abc import Collection
from typing import Literal

from libweasyl.exceptions import WeasylError as _WeasylError


LogLevel = Literal["info"]


class WeasylError(_WeasylError):

    level: LogLevel | None = None
    """
    A log level. `None` indicates no logging.

    The specific level is currently unused: any request with a non-`None` `level` is logged to stdout without further distinctions.
    """

    def __init__(
        self,
        value: str | None = None,
        *,
        level: LogLevel | None = None,
        links: Collection[tuple[str, str]] = (),
    ):
        # Avoid assigning attributes not provided as arguments so subclasses can define them at class level.
        # TODO: refactor places that catch `WeasylError` to catch libweasyl’s base `WeasylError`, and make this the only subclass with a constructor that takes `value` at all.
        if value is None:
            if not hasattr(self, "value"):
                raise ValueError("error id required")  # pragma: no cover
        else:
            self.value = value

        self.errorpage_kwargs = {"links": links} if links else {}
        self.error_suffix = ''
        self.render_as_json = False

        if level is not None:
            self.level = level

    def __str__(self):
        return repr(self.value)


__all__ = ['WeasylError']
