"""
libweasyl common code.

The contents of this module should not depend on any other libweasyl module; it
is intended to be the base-most module that every other module can depend on.
"""
from urllib.parse import urljoin


def minimize_media(request, obj):
    """
    Given :py:meth:`serialized <libweasyl.models.media.MediaItem.serialize>`
    media, return a subset of its contents (reduced to only ``mediaid``,
    ``url``, and ``links``).

    If *obj* is ``None``, ``None`` will be returned.

    As a quick reminder, serialized media looks like this:

    .. code-block:: json

      {
        "thumbnail": [
          {
            "display_url": "/static/media/34/44/8e/[...].png",
            "sha256": "34448e4d8191351f080e3e9d0f633ccd1a569acf50f93c18ac164d9e0b553b0d",
            "attributes": {
              "height": 120,
              "width": 120
            },
            "full_file_path": "/home/vagrant/weasyl3/weasyl/static/static/media/34/44/8e/[...].png",
            "aspect_ratio": 1.0,
            "media_type": "disk",
            "file_type": "png",
            "mediaid": 2421833,
            "described": {},
            "file_path": "static/media/34/44/8e/[...].png",
            "file_url": "/static/media/34/44/8e/[...].png"
          }
        ]
      }

    Minimizing reduces each media object so that it contains only the keys
    ``mediaid``, ``url``, and ``links``. ``mediaid`` is taken from the media
    object verbatim; ``url`` is taken from the ``display_url`` key joined with
    the *request* base URL; and ``links`` is the result of running
    :py:func:`.minimize_media` on the ``described`` key.

    So, minimized, the above media would be:

    .. code-block:: json

      {
        "thumbnail": [
          {
            "mediaid": 2421833,
            "links": {},
            "url": "http://localhost/static/media/34/44/8e/[...].png"
          }
        ]
      }

    Parameters:
        request: The current pyramid :py:class:`~pyramid.request.Request`.
        obj: A :py:meth:`serialized
            <libweasyl.models.media.MediaItem.serialize>` media item to be
            reduced.

    Returns:
        A dict or ``None``.
    """
    if obj is None:
        return None
    base_url = request.resource_url(None)
    return {
        k: [
            {
                'mediaid': v['mediaid'],
                'url': urljoin(base_url, v['display_url']),
                'links': minimize_media(request, v['described']),
            } for v in vs]
        for k, vs in list(obj.items())}
