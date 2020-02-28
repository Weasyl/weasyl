"""
Exceptions raised by libweasyl.

This is not an exhaustive list; some functions in libweasyl will raise
exceptions not listed in this module. Most of the exceptions defined here will
derive from :py:exc:`ExpectedWeasylError`.
"""


class WeasylError(Exception):
    """
    The base class for all custom exceptions raised by libweasyl.
    """


class ExpectedWeasylError(WeasylError):
    """
    The base class for custom libweasyl exceptions which are not an unexpected
    failure. That is, something exceptional happened, but nothing that
    indicates a problem in program logic, and recovery should be easy. A good
    example of this is form validation failure: bad user input is easy to
    recover from.

    Exceptions raised which derive from this class should include an error
    message, but should not include any sensitive information in this error
    message, as it will likely be shown to a user.
    """

    code = 403
    """
    The HTTP error code which should be returned when rendering an error page
    for this exception type.

    403 actually works as a generic catchall error code. RFC 2616 says about
    403: "The server understood the request, but is refusing to fulfill it."
    While it also has connotations regarding the Authorization header
    (specifically, "Authorization will not help and the request SHOULD NOT be
    repeated."), it still fits.
    """


class InvalidFileFormat(ExpectedWeasylError):
    """
    The file that was uploaded was of a recognized file format, but is
    explicitly disallowed from being uploaded. Uses code 422.
    """
    code = 422


class UnknownFileFormat(ExpectedWeasylError):
    """
    The file that was uploaded was not of a recognized file format, and as such
    is disallowed from being uploaded. Uses code 422.
    """
    code = 422


class ThumbnailingError(WeasylError):
    """
    Thumbnailing an image produced bad results; e.g. an image with a size not
    equal to the requested size of the thumbnail.
    """
