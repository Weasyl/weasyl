from akismet import Akismet, SpamStatus

from weasyl import config
from weasyl import define as d


FILTERING_ENABLED = config.config_read_bool(setting='enabled', value=False, section='spam_filtering')
AKISMET_KEY = config.config_read_setting(setting='key', value=None, section='spam_filtering')

if all([FILTERING_ENABLED, AKISMET_KEY]):
    _akismet = Akismet(
        AKISMET_KEY,
        blog=d.absolutify_url('/'),
        application_user_agent="weasyl/+({0})".format(d.absolutify_url('/'))
    )
else:
    FILTERING_ENABLED = False


def _get_user_agent_from_id(id=None):
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
    is_test=False,
    recheck_reason=None,
):
    """
    Submits a piece of content to Akismet to check if the content is considered as spam.

    :param user_ip: The IP address of the submitter of the content. Required.
    :param user_agent_id: The user agent ID of the UA that submitted the content; see `login.get_user_agent_id`. Required.
    :param user_id: If provided, submits the user's login_name and email address to the Akismet backend as an
    additional set of data points, which can increase performance. Optional.
    :param comment_type: A string that describes the content being sent. Optional.
    :param comment_content: The submitted content.
    :param is_test: If set to True, indicates that this request is a test.
    :param recheck_reason: If the submitted content is being rechecked for some reason, a string that indicates why the
    content is being rechecked (e.g., "edit").
    :return: akismet.SpamStatus object (Ham, Unknown, ProbableSpam, DefiniteSpam). If the type is DefiniteSpam, the
    submission can be immediately dropped as it is blatant spam.
    """
    if user_id:
        login_name, email = d.engine.execute("""
            SELECT login_name, email
            FROM login
            WHERE user_id = %(id)s
        """, id=user_id)
    else:
        login_name = email = None
    payload = {
        "user_ip": user_ip,
        "user_agent": _get_user_agent_from_id(id=user_agent_id),
        "comment_author": login_name,
        "comment_author_email": email,
        "comment_type": comment_type,
        "comment_content": comment_content,
        "is_test": is_test,
        "recheck_reason": recheck_reason,
    }
    if FILTERING_ENABLED:
        return _akismet.check(**payload)
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
    is_test=False,
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
    :param is_test: If set to True, indicates that this request is a test.
    :return: akismet.SpamStatus object (Ham, Unknown, ProbableSpam, DefiniteSpam)
    """
    if all([is_spam, is_ham]):
        raise AttributeError("Either is_spam or is_ham must be set, not both.")
    if user_id:
        login_name, email = d.engine.execute("""
            SELECT login_name, email
            FROM login
            WHERE user_id = %(id)s
        """, id=user_id)
    else:
        login_name = email = None
    payload = {
        "user_ip": user_ip,
        "user_agent": _get_user_agent_from_id(id=user_agent_id),
        "comment_author": login_name,
        "comment_author_email": email,
        "comment_type": comment_type,
        "comment_content": comment_content,
        "is_test": is_test,
    }
    if is_ham:
        _akismet.submit_ham(**payload)
    elif is_spam:
        _akismet.submit_spam(**payload)
