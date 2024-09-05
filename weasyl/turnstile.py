import enum
import logging
import requests

from weasyl.config import config_obj
from weasyl.error import WeasylError


logger = logging.getLogger(__name__)


SITE_KEY = config_obj.get("turnstile", "site_key", fallback=None)

_SECRET_KEY = None if SITE_KEY is None else config_obj.get("turnstile", "secret_key")

ENFORCE = None if SITE_KEY is None else config_obj.getboolean("turnstile", "enforce")
"""
To allow a grace period for forms loaded before Turnstile was served, first deploy with `enforce = false`, then `enforce = true` later.
"""


@enum.unique
class Result(enum.Enum):
    NOT_LOADED = enum.auto()
    NOT_COMPLETED = enum.auto()
    INVALID = enum.auto()
    SUCCESS = enum.auto()


def _check(request) -> Result:
    turnstile_response = request.POST.get("cf-turnstile-response")

    if turnstile_response is None:
        return Result.NOT_LOADED

    if not turnstile_response:
        return Result.NOT_COMPLETED

    turnstile_validation = requests.post("https://challenges.cloudflare.com/turnstile/v0/siteverify", data={
        "secret": _SECRET_KEY,
        "response": turnstile_response,
        "remoteip": request.client_addr,
    }).json()

    if not turnstile_validation["success"]:
        error_codes = turnstile_validation["error-codes"]

        if not {"invalid-input-response", "timeout-or-duplicate"}.issuperset(error_codes):
            logger.warn("Unexpected Turnstile error codes: %r", error_codes)  # pragma: no cover

        return Result.INVALID

    return Result.SUCCESS


def require(request) -> None:
    if SITE_KEY is None:
        return

    result = _check(request)

    if result == Result.SUCCESS:
        return

    if ENFORCE:
        raise WeasylError("turnstileMissing")

    if result == Result.NOT_LOADED:
        logger.info("Form submitted without Turnstile field in non-enforcing mode")
    else:
        logger.warn("Turnstile validation failed in non-enforcing mode: %s", result)
