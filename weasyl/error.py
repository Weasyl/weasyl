from sqlalchemy.exc import DBAPIError as PostgresError

from libweasyl.exceptions import WeasylError as _WeasylError


class WeasylError(_WeasylError):
    def __init__(self, value, level=None, **kwargs):
        self.value = value
        self.errorpage_kwargs = kwargs
        self.error_suffix = ''
        self.render_as_json = False
        self.level = level

    def __str__(self):
        return repr(self.value)


__all__ = ['WeasylError', 'PostgresError']
