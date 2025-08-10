import itertools
import operator
import random
from collections import defaultdict

from prometheus_client import Histogram

from libweasyl import ratings
from libweasyl.cache import region

from weasyl import blocktag
from weasyl import character
from weasyl import define as d
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import profile
from weasyl import searchtag
from weasyl import siteupdate
from weasyl import submission
from weasyl.metrics import CachedMetric


recent_submissions_time = CachedMetric(Histogram("weasyl_recent_submissions_fetch_seconds", "recent submissions fetch time", ["cached"]))


@recent_submissions_time.cached
@region.cache_on_arguments(expiration_time=120)
@recent_submissions_time.uncached
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
    media.strip_non_thumbnail_media(submissions)
    return submissions


def filter_submissions(userid, submissions, incidence_limit=None):
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

    submitter_incidence: defaultdict[int, int] = defaultdict(int)
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
    buckets: defaultdict[int, list] = defaultdict(list)
    for s in submissions:
        if 'charid' in s:
            bucket = 'char'
        else:
            bucket = s['subtype'] // 1000
        buckets[bucket].append(s)

    return (
        submissions[:22],
        buckets[1][:11],
        buckets[2][:11],
        buckets[3][:11],
        buckets['char'][:11],
    )


@d.record_timing
def template_fields(userid):
    submissions = list(filter_submissions(userid, recent_submissions(), incidence_limit=1))
    ret = partition_submissions(submissions)

    critique = submission.select_critique()
    random.shuffle(critique)
    critique = list(itertools.islice(filter_submissions(userid, critique, incidence_limit=1), 11))
    critique.sort(key=lambda sub: sub['submitid'], reverse=True)
    viewer = d.get_card_viewer()

    return (
        *map(viewer.get_cards, ret),
        # Recent site news update
        siteupdate.select_last(),
        # Recent critique submissions
        viewer.get_cards(critique),
        # Currently streaming users
        profile.select_streaming_sample(userid),
        # Recently popular submissions
        viewer.get_cards(itertools.islice(filter_submissions(userid, submission.select_recently_popular(), incidence_limit=1), 11)),
    )
