"""
Configuration of libweasyl.

libweasyl depends on some global state to be set up in order for e.g. database
access to work correctly. This might be nicer if python had a way of
parameterizing modules, but we can't, so this is what we have. It does mean
that only one libweasyl configuration can exist in a running python process.
"""

from libweasyl.models.media import MediaItem
from libweasyl.models.meta import BaseQuery, _configure_dbsession
from libweasyl.staff import _init_staff


def configure_libweasyl(
        dbsession, not_found_exception, base_file_path,
        staff_config_dict, media_link_formatter_callback):
    """
    Configure libweasyl for the current application. This sets up some
    global state around libweasyl.

    This function can be called multiple times without issues; each call will
    replace the values set by the previous call.

    Parameters:
        dbsession: A SQLAlchemy ``scoped_session`` instance configured for the
            application's database usage.
        not_found_exception: An exception to be raised on the ``*_or_404``
            methods of queries.
        base_file_path: The path to where static content lives on disk.
        staff_config_dict: A dictionary of staff levels and user IDs.
        media_link_formatter_callback: A callback to format the URL for a media
            link. The callback will be called as ``callback(media_item, link)``
            and is expected to return a URL or ``None`` to use the default.
    """
    _configure_dbsession(dbsession)
    BaseQuery._not_found_exception = staticmethod(not_found_exception)
    MediaItem._base_file_path = staticmethod(base_file_path)
    _init_staff(**staff_config_dict)
    MediaItem._media_link_formatter_callback = staticmethod(media_link_formatter_callback)
