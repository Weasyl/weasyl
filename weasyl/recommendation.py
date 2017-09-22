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

from dogpile.cache import make_region
from enum import Enum
import numpy as np
import pandas
import scipy.sparse as sparse

from libweasyl import ratings

from weasyl import define as d
from weasyl.error import WeasylError
from weasyl.errorcode import unexpected
from weasyl import media
from weasyl import submission


# Unfortunately dogpile memcache chokes on large numpy matrices.
# So we make our own in-memory representation for them.
_region = make_region().configure('dogpile.cache.memory')


class RecommendationRating(Enum):
    """Gives meaningful names to different rating constants."""
    DISLIKE = -1
    NEUTRAL = 0
    LIKE = 1
    FAVORITE = 2


_MINIMUM_RATING_COUNT = 1  # How many ratings an item needs to be recommended


# TODO(hyena): Combine tables of favorites with likes/dislikes
# If submissions ever swallow characters and journals (and one
# can certainly hope), we should consolidate the tables into one.
# This will ease complexity of keeping them up to date.


# A named tuple representing everything we need for generating user-to-user similarities.
# Updated periodically.
Similarities = namedtuple('Similarities', 'user_similarity, ratings, user_map, submit_map, reverse_submit_map')


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


def get_user_ratings(userid):
    ratings = d.engine.execute(
        "SELECT submitid, rating FROM recommendation_rating WHERE userid=%(userid)s",
        userid=userid)
    return {i['submitid']: i['rating'] for i in ratings}


def _fast_similarity(ratings, kind='user'):
    """
    Calculate user to user or item to item similarities.
    This function can take a few seconds to run.
    """
    # The function below was adapted from the blog post linked above. See:
    # http://blog.ethanrosenthal.com/2015/11/02/intro-to-collaborative-filtering/#Collaborative-filtering
    #
    # With some minor alterations:
    #   - We don't use epsilon because scipy dies when we try to add a scalar to a sparse matrix.
    #     This shouldn't be matter because all users in the matrix have at least one favorite.
    #   - I use sim.diagonal() instead of np.diag() because sparse matrices complain mightily when
    #     it comes to np.diag().
    #   - Things die if we try to do regular division. Instead, we construct a diagonal matrix with
    #     the reciprocals of everything we would have divided with and both pre-multiply (to scale
    #     every row by the first user) and post multiply (to scale every column by the second user).
    if kind == 'user':
        sim = ratings.dot(ratings.T)
    elif kind == 'item':
        sim = ratings.T.dot(ratings)
    norms = np.array([np.sqrt(sim.diagonal())])
    norms_sparse_diag = sparse.diags(1/norms.ravel(), format='csr')
    return (norms_sparse_diag * sim * norms_sparse_diag)


def select_list(userid, rating):
    """
    Get the top recommendations for a user and select their submission info. Doesn't show hidden
    content or content that violates friends rules.
    """
    submitids = recs_for_user(userid)
    if not submitids:
        return submitids

    # Throw out anything with not enough ratings.
    q = d.engine.execute("""
        SELECT su.submitid, COUNT(rr.*) as rating_count
        FROM submission su
        LEFT JOIN recommendation_rating rr ON su.submitid = rr.submitid
        WHERE su.submitid IN %(recs)s
        GROUP BY su.submitid
        """,
        recs=tuple(submitids))
    rating_counts = {row['submitid']: row['rating_count'] for row in q}
    submitids = [x for x in submitids if rating_counts[x] > _MINIMUM_RATING_COUNT]


    # TODO(hyena): This is grossly adapted from submission.py. Commit less SQL violence.
    statement = [
        "SELECT su.submitid, su.title, su.rating, su.unixtime, "
        "su.userid, pr.username, su.settings, su.subtype "]
    statement.extend(submission.select_query(userid=userid, rating=rating))
    statement.append(" AND su.submitid IN %(recs)s")


    items = {i[0]: {
                 "contype": 10,
                 "submitid": i[0],
                 "title": i[1],
                 "rating": i[2],
                 "unixtime": i[3],
                 "userid": i[4],
                 "username": i[5],
                 "subtype": i[7],
             } for i in d.engine.execute("".join(statement), recs=tuple(submitids))}
    # Re-sort and throw out anything
    query = [items[x] for x in submitids if x in items]  # Re-sort.
    media.populate_with_submission_media(query)

    return query


@d.record_timing
def recs_for_user(userid, k=20, count=100):
    """
    Generates recommendations for a weasyl user.
    Will not include the user's own submissions or items they've rated.

    Args:
        userid (int): The weasyl userid.
        k (int, optional): How many closest other users to use. Defaults to 20.
        count (int, optional): How many items to return for the user. Defaults to 10.

    Returns:
        An array of weasyl submission ids for the user.
    """
    rec_info = get_recommendation_data()

    # Don't recommend our own content or things we've rated.
    user_submissions = d.engine.execute("SELECT submitid FROM submission WHERE userid=%(userid)s",
                                        userid=userid).fetchall()
    blacklist = set(get_user_ratings(userid).keys() + [x['submitid'] for x in user_submissions])
    blacklist_indices = [rec_info.submit_map[x] for x in blacklist if x in rec_info.submit_map]

    if userid not in rec_info.user_map:
        # User has no favorites.
        return []
    user_index = rec_info.user_map[userid]
    top_friends = np.argpartition(rec_info.user_similarity[:, user_index].toarray().ravel(), -k)[-2:-k - 2:-1]

    # Don't use ourselves for recommendations.
    top_friends = top_friends[top_friends != user_index]  # Don't use ourselves for recommendations.

    preds = rec_info.user_similarity[user_index, top_friends].dot(rec_info.ratings[top_friends, :])
    pred_array = preds.toarray().ravel()
    pred_array[blacklist_indices] = -100
    # TODO: Use argpartition to speed this up
    return [rec_info.reverse_submit_map[x] for x in np.argsort(pred_array)[:-count - 1:-1]]


@_region.cache_on_arguments()
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
        A Similarities namedtuple with these fields:
            user_similarity: A sparse matrix of user-to-user similarities
            ratings: A sparse matrix of how users have favorited, liked, or disliked submissions
            user_map: A dictionary matching Weasyl user ids to indices in the matrices
            submit_map: A dictionary matching Weasyl submission ids to indices in the matrices
            reverse_submit_map: A reverse dictionary of the submit_map
    """
    # TODO(hyena): This construction is extremely slow. Testing indicates that most of the time
    # is spent reading out the entirety of the recommendation_rating table.
    # df = pandas.read_sql("recommendation_rating", d.engine)  # This command is extremely slow.
    df = pandas.read_csv("/tmp/favorites.csv")

    user_map = {x[1]: x[0] for x in enumerate(df.userid.unique())}
    item_map = {x[1]: x[0] for x in enumerate(df.submitid.unique())}
    rev_item_map = {v: k for k, v in item_map.iteritems()}

    n_users = df.userid.unique().shape[0]
    n_items = df.submitid.unique().shape[0]

    ratings = sparse.csr_matrix((df['rating'], (df.userid.map(user_map), df.submitid.map(item_map))),
                                shape=(n_users, n_items))
    user_similarity = _fast_similarity(ratings, kind='user')

    return Similarities(user_similarity=user_similarity,
                        ratings=ratings,
                        user_map=user_map,
                        submit_map=item_map,
                        reverse_submit_map=rev_item_map)
