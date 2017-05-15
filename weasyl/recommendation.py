"""
This module contains functionality related to generating submission
recommendations.

The heart of the logic is currently a user-to-user collaborative
filtering algorithm built on top of numpy. It's similar to an
approach detailed in
http://blog.ethanrosenthal.com/2015/11/02/intro-to-collaborative-filtering/
but modified to use sparse arrays.
"""


from __future__ import absolute_import

from collections import namedtuple

from enum import Enum
import numpy as np
from pandas import DataFrame
import scipy.sparse as sparse

from libweasyl.cache import region

from weasyl import define as d
from weasyl.error import WeasylError
from weasyl.errorcode import unexpected


class RecommendationRating(Enum):
    """Gives meaningful names to different rating constants."""
    DISLIKE = -1
    NEUTRAL = 0
    LIKE = 1
    FAVORITE = 2


# TODO(hyena): Combine tables of favorites with likes/dislikes
# If submissions ever swallow characters and journals (and one
# can certainly hope), we should consolidate the tables into one.
# This will ease complexity of keeping them up to date.


# A named tuple representing everything we need for generating user-to-user similarities.
# Updated periodically.
_Similarities = namedtuple('_Similarities', 'user_similarity, ratings, user_map, submit_map')


def clear_user_rating(userid, submitid):
    """
    Clears a user's rating for an item.

    Note that this is not quite the same as rating it zero: An item rating zero will not
    show up in recommendations.
    @param userid:
    @param submitid:
    @return: The number of rows cleared (1 or 0).
    """
    return d.engine.execute(
        "DELETE FROM recommendation_rating WHERE (userid, submitid) = (%s, %s)",
        [userid, submitid]).rowcount


def set_user_rating(userid, submitid, rating):
    """
    Sets a user's rating for an item.

    Throws an exception if rating isn't valid.
    @param userid:
    @param submitid:
    @param rating:
    @return:
    """
    if not rating in RecommendationRating:
        raise WeasylError(unexpected)
    return d.engine.execute("""
        INSERT INTO recommendation_rating
            VALUES (%(userid)s, %(submitid)s, %(rating)s)
            ON CONFLICT (userid, submitid) DO UPDATE SET rating = %(rating)s
        """, userid=userid, submitid=submitid, rating=rating.value).rowcount


def get_user_rating(userid, submitid):
    rating = d.engine.scalar(
        "SELECT rating FROM recommendation_rating WHERE userid=%(userid)s AND submitid=%(submitid)s",
        userid=userid, submitid=submitid)
    if rating is None:
        return rating
    return RecommendationRating(rating)


@region.cache_on_arguments()
@d.record_timing
def get_recommendation_data():
    """
    Generates a sparse matrix of user to user similarities, a matrix of ratings, and maps of
    user and submission ids to indices in them.

    Presently this is calculated as follows:
        1. Read in the contents of the favorites table (and eventually the likes/dislikes/neutral table)
        2. Construct the user_map and submit_map
        3. Create a sparse rating matrix
        4. Use the sparse rating matrix to calculate pairwise cosine similarities between users.

    This can be a memory and computationally expensive operation and should only be run periodically.

    Returns:
        A _Similarities namedtuple with these fields:
            user_similarity: A sparse matrix of user-to-user similarities
            ratings: A sparse matrix of how users have favorited, liked, or disliked submissions
            user_map: A dictionary matching Weasyl user ids to indices in the matrices
            submit_map: A dictionary matching Weasyl submission ids to indices in the matrices
    """
    q = d.execute("SELECT userid, targetid FROM favorite WHERE type='s'")
