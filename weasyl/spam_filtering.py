import logging
import os

from akismet import Akismet, SpamStatus
# Imported as RequestsConnectionError to not conflict with Python 3's built-in ConnectionError exception
from requests.exceptions import ConnectionError as RequestsConnectionError

from weasyl import config
from weasyl import define as d
from weasyl.error import WeasylError


FILTERING_ENABLED = config.config_read_bool(setting='enabled', value=False, section='spam_filtering')
AKISMET_KEY = config.config_read_setting(setting='key', value=None, section='spam_filtering')
# Used to set the `is_spam` flag on requests sent to the backend
_IS_ENVIRONMENT_TESTING = True if os.environ.get("WEASYL_TESTING_ENV") else False
# AKA, the link to the main page of the web application
AKISMET_BLOG_URL = "http://lo.weasyl.com" if _IS_ENVIRONMENT_TESTING else "https://www.weasyl.com"


if all([FILTERING_ENABLED, AKISMET_KEY]):
    _akismet = Akismet(
        AKISMET_KEY,
        blog=AKISMET_BLOG_URL,
        application_user_agent="weasyl/+({0})".format("https://github.com/weasyl/weasyl")
    )
else:
    FILTERING_ENABLED = False


def _get_user_agent_from_id(id=None):
    """
    Converts a user agent ID number to a textual user agent string.
    :param id: The user agent id number.
    :return: A string assigned to the specified user agent.
    """
    return d.engine.scalar("""
        SELECT user_agent
        FROM user_agents
        WHERE user_agent_id = %(ua_id)s
    """, ua_id=id)


def check(
    user_ip=None,
    user_agent_id=None,
    user_id=None,
    comment_type=None,
    comment_content=None,
):
    """
    Submits a piece of content to Akismet to check if the content is considered as spam.

    :param user_ip: The IP address of the submitter of the content. Required.
    :param user_agent_id: The user agent ID of the UA that submitted the content; see `login.get_user_agent_id`. Required.
    :param user_id: If provided, submits the user's login_name and email address to the Akismet backend as an
    additional set of data points, which can increase performance. Optional.
    :param comment_type: A string that describes the content being sent. Optional.
    :param comment_content: The submitted content.
    :return: akismet.SpamStatus object (Ham, Unknown, ProbableSpam, DefiniteSpam). If the type is DefiniteSpam, the
    submission can be immediately dropped as it is blatant spam. If spam filtering is disabled, SpamStatus.Ham
    is always returned.
    """
    if user_id:
        login_name, email = d.engine.execute("""
            SELECT login_name, email
            FROM login
            WHERE userid = %(id)s
        """, id=user_id).first()
    else:
        login_name = email = None
    payload = {
        "user_ip": user_ip,
        "user_agent": _get_user_agent_from_id(id=user_agent_id),
        "comment_author": login_name,
        "comment_author_email": email,
        "comment_type": comment_type,
        "comment_content": comment_content,
        "is_test": _IS_ENVIRONMENT_TESTING,
    }
    if FILTERING_ENABLED:
        try:
            return _akismet.check(**payload)
        except RequestsConnectionError:
            # Don't fail just because of a connection issue to the Akismet backend; but log that we failed.
            d.log_exc(level=logging.WARNING)
            return SpamStatus.Ham
    else:
        return SpamStatus.Ham


def submit(
    is_ham=False,
    is_spam=False,
    user_ip=None,
    user_agent_id=None,
    user_id=None,
    comment_type=None,
    comment_content=None,
):
    """
    Submits a correction to Akismet, indicating that it was either ham (good), or missed spam.

    One of `is_ham` or `is_spam` must be provided.

    :param is_ham: Indicates that the content being submitted was ham (incorrectly classified as spam).
    :param is_spam: Indicates that the content being submitted was missed spam (incorrectly classified as ham).
    :param user_ip: The IP address of the submitter of the content. Required.
    :param user_agent_id: The user agent ID of the UA that submitted the content; see `login.get_user_agent_id`. Required.
    :param user_id: If provided, submits the user's login_name and email address to the Akismet backend as an
    additional set of data points, which can increase performance. Optional.
    :param comment_type: A string that describes the content being sent. Optional.
    :param comment_content: The submitted content.
    """
    if not FILTERING_ENABLED:
        raise WeasylError("SpamFilteringDisabled")

    if all([is_spam, is_ham]):
        raise AttributeError("Either is_spam or is_ham must be set, not both.")
    if user_id:
        login_name, email = d.engine.execute("""
            SELECT login_name, email
            FROM login
            WHERE userid = %(id)s
        """, id=user_id).first()
    else:
        login_name = email = None
    payload = {
        "user_ip": user_ip,
        "user_agent": _get_user_agent_from_id(id=user_agent_id),
        "comment_author": login_name,
        "comment_author_email": email,
        "comment_type": comment_type,
        "comment_content": comment_content,
        "is_test": _IS_ENVIRONMENT_TESTING,
    }
    if is_ham:
        _akismet.submit_ham(**payload)
    elif is_spam:
        _akismet.submit_spam(**payload)
