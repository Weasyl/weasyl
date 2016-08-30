# api.py

from __future__ import absolute_import

from pyramid.threadlocal import get_current_request

from libweasyl.models.meta import Base
from libweasyl.models.api import APIToken
from libweasyl import security
from weasyl import define as d


def is_api_user():
    request = get_current_request()
    return 'X_WEASYL_API_KEY' in request.headers or 'AUTHORIZATION' in request.headers


def get_api_keys(userid):
    with Base.dbsession().connection() as db:
        return db.execute("SELECT token, description FROM api_tokens WHERE userid = %s", userid)


def add_api_key(userid, description):
    db = Base.dbsession()
    db.add(APIToken(userid=userid, token=security.generate_key(48), description=description))
    db.flush()


def delete_api_keys(userid, keys):
    if not keys:
        return
    (APIToken.query
             .filter(APIToken.userid == userid)
             .filter(APIToken.token.in_(keys))
             .delete(synchronize_session='fetch'))


def tidy_media(item):
    ret = {
        'url': d.absolutify_url(item['display_url']),
        'mediaid': item.get('mediaid'),
    }
    if item.get('described'):
        ret['links'] = tidy_all_media(item['described'])
    return ret


def tidy_all_media(d):
    # We suppress thumbnail-legacy currently.
    hidden_keys = ['thumbnail-legacy']
    ret = {k: map(tidy_media, v) for k, v in d.iteritems() if k not in hidden_keys}
    thumbnail_value = ret.get('thumbnail-custom') or ret.get('thumbnail-generated')
    if thumbnail_value:
        ret['thumbnail'] = thumbnail_value
    return ret
