import urllib

import arrow
import pyramid_jinja2.filters
from jinja2 import Markup, contextfilter
from pyramid.threadlocal import get_current_request
from pyramid.traversal import PATH_SAFE

from libweasyl import text, staff, ratings
from libweasyl.legacy import get_sysname

from weasyl import define, macro, profile


def sfw():
    mode = get_current_request().cookies.get('sfwmode', 'nsfw')
    if mode == 'nsfw':
        return False
    else:
        return True


@contextfilter
def route_path_filter(ctx, route_name, *elements, **kw):
    url = pyramid_jinja2.filters.route_path_filter(ctx, route_name, *elements, **kw)

    # Fixes urls returned from pyramids route_path so that that tildes are not url quoted.
    url = urllib.quote(urllib.unquote(url), safe=PATH_SAFE)

    return url


jinja2_globals = {
    'arrow': arrow,
    'CAPTCHA': define.captcha_public,
    'ISO8601_DATE': define.iso8601_date,
    'LOCAL_ARROW': define.local_arrow,
    'M': macro,
    'NOW': define.get_time,
    'page_header_info': define.page_header_info,
    'QUERY_STRING': define.query_string,
    'R': ratings,
    'select_myself': profile.select_myself,
    'sfw': sfw,
    'SHA': define.CURRENT_SHA,
    'staff': staff,
    'SYMBOL': define.text_price_symbol,
    'THUMB': define.thumb_for_sub,
    'TOKEN': define.get_token,
    'USER_TYPE': define.user_type,
    'WEBP_THUMB': define.webp_thumb_for_sub,
}

filters = {
    'DATE': define.convert_date,
    'LOGIN': get_sysname,
    'MARKDOWN': lambda x: Markup(text.markdown(x)),
    'MARKDOWN_EXCERPT': lambda x: Markup(text.markdown_excerpt(x)),
    'route_path': route_path_filter,
    'SLUG': text.slug_for,
    'TIME': define.convert_time,
}
