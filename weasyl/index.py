from __future__ import absolute_import

import collections
import itertools
import operator

from libweasyl import ratings
from libweasyl.cache import region

from weasyl import blocktag
from weasyl import character
from weasyl import define as d
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import profile
from weasyl import searchtag
from weasyl import siteupdate
from weasyl import submission


@region.cache_on_arguments()
@d.record_timing
def recent_submissions():
    submissions = []
    for category in m.ALL_SUBMISSION_CATEGORIES:
        submissions.extend(submission.select_list(
            userid=None, rating=ratings.EXPLICIT.code, limit=256, subcat=category,
            index_page_filter=True))

    tag_map = searchtag.select_list(
        d.meta.tables['searchmapsubmit'], [s['submitid'] for s in submissions])
    for s in submissions:
        s['tags'] = tag_map.get(s['submitid'], [])

    characters = character.select_list(
        userid=None, rating=ratings.EXPLICIT.code, limit=256)
    tag_map = searchtag.select_list(
        d.meta.tables['searchmapchar'], [c['charid'] for c in characters])
    for c in characters:
        c['tags'] = tag_map.get(c['charid'], [])

    submissions.extend(characters)
    submissions.sort(key=operator.itemgetter('unixtime'), reverse=True)
    return submissions


def filter_submissions(userid, submissions, incidence_limit=3):
    """
    Filters a list of submissions according to the user's preferences and
    optionally limits the number of items returned from one submitter.

    :param userid: The userid to use for blocked tags and rating. Usually the
        viewing user.
    :type userid: int.
    :param submissions: A list of submissions with appropriate fields (rating,
        userid, etc.)
    :type submissions: A list of submission dictionaries.
    :param incidence_limit: The maximum number of submissions to permit from
        one creator. Set to 0 or None for no limit.
    :type incidence_limit: int.
    :return: An iterator over the submissions after filtering by the user's
        settings and incidence limit.
    """
    blocked_tags = ignored_users = set()
    rating = ratings.GENERAL.code
    if userid:
        rating = d.get_rating(userid)
        blocked_tags = blocktag.select_ids(userid)
        ignored_users = set(ignoreuser.cached_list_ignoring(userid))

    submitter_incidence = collections.defaultdict(int)
    for s in submissions:
        if incidence_limit and submitter_incidence[s['userid']] >= incidence_limit:
            continue
        if s['rating'] > rating:
            continue
        if s['userid'] in ignored_users:
            continue
        tags = set(s['tags'])
        if blocktag.check_list(s['rating'], tags, blocked_tags):
            continue
        submitter_incidence[s['userid']] += 1
        yield s


def partition_submissions(submissions):
    buckets = collections.defaultdict(list)
    for s in submissions:
        if 'charid' in s:
            bucket = 'char'
        else:
            bucket = s['subtype'] // 1000
        buckets[bucket].append(s)
    ret = [
        submissions[:22],
        d.get_random_set(submissions, 11),
    ]
    for bucket in [1, 2, 3, 'char']:
        ret.append(buckets[bucket][:11])
    return ret


@region.cache_on_arguments(expiration_time=60)
@d.record_timing
def template_fields(userid):
    rating = d.get_rating(userid)
    submissions = list(filter_submissions(userid, recent_submissions()))
    ret = partition_submissions(submissions)
    data = {'latest': ret[0],
            'randomized': ret[1],
            'visual': ret[2],
            'literary': ret[3],
            'media': ret[4],
            'characters': ret[5],
            # Recent site news update
            'update': siteupdate.select_last(),
            # Recent critique submissions
            'critique': submission.select_list(userid, rating, 4, options=["critique"]),
            # Currently streaming users
            'streaming': profile.select_streaming(userid, rating, 4),
            # Recently popular submissions
            'popular': list(
                itertools.islice(filter_submissions(userid, submission.select_recently_popular(), incidence_limit=1),
                                 11))
            }
    return data
