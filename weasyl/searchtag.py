import base64
import enum
import re
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from struct import Struct
from typing import Iterable
from typing import NewType

import sqlalchemy as sa
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from sqlalchemy.sql.expression import any_

from libweasyl import staff
from libweasyl.cache import region
from libweasyl.constants import TAG_MAX_LENGTH

from weasyl import define as d
from weasyl import files
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl.config import config_obj
from weasyl.error import WeasylError
from weasyl.forms import NormalizedTag
from weasyl.forms import parse_tag


TagPattern = NewType("TagPattern", str)


_TAG_DELIMITER = re.compile(r"[\s,]+")
_NON_PATTERN = re.compile(r"[^\w*]", re.ASCII)

# limited so people can't give themselves every tag
# and hog the top of marketplace results
MAX_PREFERRED_TAGS = 50


class TaggableTarget:
    __slots__ = ("id",)

    id: int

    def __init__(self, id: int) -> None:
        self.id = id


class SubmissionTarget(TaggableTarget):
    __slots__ = ()

    table = "searchmapsubmit"
    history_table = "tag_updates"
    feedback_table = "tag_suggestion_feedback_submission"
    feature = "submit"
    arg_name = history_id_column = "submitid"
    path_component = "submission"
    type_code = b"s"


class CharacterTarget(TaggableTarget):
    __slots__ = ()

    table = "searchmapchar"
    history_table = None
    feedback_table = "tag_suggestion_feedback_character"
    feature = "char"
    arg_name = "charid"
    path_component = "character"
    type_code = b"c"


class JournalTarget(TaggableTarget):
    __slots__ = ()

    table = "searchmapjournal"
    history_table = None
    feedback_table = "tag_suggestion_feedback_journal"
    feature = "journal"
    arg_name = "journalid"
    path_component = "journal"
    type_code = b"j"


_TARGET_TYPES_BY_FEATURE = {
    t.feature: t
    for t in (
        SubmissionTarget,
        CharacterTarget,
        JournalTarget,
    )
}


def get_target(feature: str, targetid: int) -> TaggableTarget:
    t = _TARGET_TYPES_BY_FEATURE.get(feature)

    if t is None:
        raise WeasylError("Unexpected")

    return t(targetid)


def select(submitid=None, charid=None, journalid=None) -> list[str]:
    target = (
        SubmissionTarget(submitid) if submitid
        else CharacterTarget(charid) if charid
        else JournalTarget(journalid))

    return select_grouped(None, target).artist


@dataclass(frozen=True, slots=True)
class GroupedTags:
    artist: list[str]
    suggested: list[str]
    own_suggested: list[str]


def select_grouped(userid: int, target: TaggableTarget) -> GroupedTags:
    # 'a': artist-tag
    tags = d.engine.execute(
        "SELECT title, settings ~ 'a', added_by"
        f" FROM {target.table}"
        " INNER JOIN searchtag USING (tagid)"
        " WHERE targetid = %(target)s",
        target=target.id,
    ).fetchall()

    artist = []
    suggested = []
    own_suggested = []

    for tag, is_artist_tag, added_by in tags:
        if is_artist_tag:
            artist.append(tag)
        else:
            suggested.append(tag)

            if added_by == userid:
                own_suggested.append(tag)

    artist.sort()
    suggested.sort()
    own_suggested.sort()

    return GroupedTags(
        artist=artist,
        suggested=suggested,
        own_suggested=own_suggested,
    )


def select_list(map_table, targetids):
    if not targetids:
        return {}

    mt = map_table
    q = (
        sa
        .select([mt.c.targetid, sa.func.array_agg(mt.c.tagid)])
        .select_from(mt)
        .where(mt.c.targetid == any_(targetids))
        .group_by(mt.c.targetid))

    db = d.connect()
    return dict(list(db.execute(q)))


def _get_or_create(name: NormalizedTag) -> int:
    return get_or_create_many([name])[0]


def get_or_create_many(names: Iterable[NormalizedTag | TagPattern]) -> list[int]:
    """
    Map distinct normalized tag names to tag ids, creating new tag ids as necessary and returning a list of distinct tag ids in an arbitrary order.
    """
    ids = dict.fromkeys(names, None)
    ids |= get_ids(*ids.keys())
    missing_names = [key for key, value in ids.items() if value is None]

    if missing_names:
        d.engine.execute('''
            INSERT INTO searchtag (title)
            SELECT title
            FROM UNNEST(%(names)s::text[]) AS title
            ON CONFLICT (title) DO NOTHING
        ''', names=missing_names)

        ids |= get_ids(*missing_names)

    return list(ids.values())


def _get_id(name: NormalizedTag) -> int | None:
    return get_ids(name).get(name)


@region.cache_multi_on_arguments(asdict=True)
def get_ids(*names: NormalizedTag | TagPattern) -> dict[NormalizedTag, int]:
    """
    Map distinct normalized tag names to tag ids, returning a dict with entries only for those tags that exist.
    """
    result = d.engine.execute(
        "SELECT tagid, title FROM searchtag WHERE title = ANY (%(names)s)",
        names=list(names))

    return {row.title: row.tagid for row in result}


@region.cache_multi_on_arguments(asdict=True)
def get_names(*ids: int) -> dict[int, NormalizedTag]:
    """
    Map distinct tag ids to normalized tag names, returning a dict with entries only for those tag ids that exist.
    """
    result = d.engine.execute(
        "SELECT tagid, title FROM searchtag WHERE tagid = ANY (%(ids)s)",
        ids=list(ids))

    return {row.tagid: row.title for row in result}


def parse_tags(text: str) -> set[NormalizedTag]:
    return set(filter(None, map(parse_tag, _TAG_DELIMITER.split(text))))


def parse_restricted_tags(text: str) -> set[TagPattern]:
    """
    A custom implementation of ``parse_tags()`` for the restricted tag list.
    Enforces the desired characteristics of restricted tags, and allows an asterisk
    character, whereas ``parse_tags()`` would strip asterisks.

    Parameters:
        text: The string to parse for tags

    Returns:
        tags: A set() with valid tags.
    """
    return set(filter(None, map(_parse_pattern, _TAG_DELIMITER.split(text))))


def _parse_pattern(text: str) -> TagPattern | None:
    text = _NON_PATTERN.sub("", text)
    text = "_".join(filter(None, text.split("_")))

    if not text:
        return None

    if len(text) > TAG_MAX_LENGTH:
        raise WeasylError("tagTooLong")

    text = text.lower()

    match text.split("*", 1):
        case [_]:
            return TagPattern(text)
        case [prefix, suffix]:
            suffix = suffix.replace("*", "")  # limit one wildcard
            return TagPattern(f"{prefix}*{suffix}") if len(prefix) + len(suffix) >= 2 else None
        case _:
            assert False


def _update_submission_tags(tx, submitid: int) -> None:
    tx.execute(
        "WITH t AS ("
        " SELECT coalesce(array_agg(tagid), ARRAY[]::integer[]) AS tags FROM searchmapsubmit WHERE targetid = %(submission)s)"
        " INSERT INTO submission_tags (submitid, tags) SELECT %(submission)s, tags FROM t"
        " ON CONFLICT (submitid) DO UPDATE SET tags = (SELECT tags FROM t)",
        submission=submitid,
    )


def _get_ownerid(target: TaggableTarget) -> int | None:
    return d.get_ownerid(**{target.arg_name: target.id})


def _set_suggested_tags(
    *,
    userid: int,
    target: TaggableTarget,
    ownerid: int,
    tag_names: set[NormalizedTag],
) -> list[NormalizedTag]:
    can_suggest_tags = d.engine.scalar("SELECT can_suggest_tags FROM profile WHERE userid = %(user)s", user=userid)
    if not can_suggest_tags:
        raise WeasylError("InsufficientPermissions")

    if ignoreuser.check(ownerid, userid):
        raise WeasylError("contentOwnerIgnoredYou")

    # Track which tags fail to be added or removed to later notify the user
    is_restricted_tag = _get_restricted_tag_matcher({
        *query_user_restricted_tags(ownerid),
        *_query_global_restricted_tags(),
    })
    tags_not_added = set(filter(is_restricted_tag, tag_names))
    apply_tags = tag_names - tags_not_added
    apply_tagids = get_or_create_many(apply_tags)

    def transaction(tx):
        tx.execute(
            "WITH"
            f" removed AS (DELETE FROM {target.table}"
            " WHERE targetid = %(target)s"
            " AND settings !~ 'a'"
            " AND added_by = %(user)s"
            " AND tagid != ALL (%(tags)s) RETURNING tagid),"
            f" added AS (INSERT INTO {target.table} (targetid, tagid, added_by)"
            " SELECT %(target)s, tag, %(user)s"
            " FROM UNNEST (%(tags)s::integer[]) AS tag"
            " ON CONFLICT DO NOTHING"
            " RETURNING tagid)"
            + (
                f" INSERT INTO {target.history_table} ({target.history_id_column}, userid, added, removed)"
                if target.history_table else "")
            + " VALUES (%(target)s, %(user)s,"
            " (SELECT coalesce(array_agg(title), ARRAY[]::text[]) FROM searchtag INNER JOIN added USING (tagid)),"
            " (SELECT coalesce(array_agg(title), ARRAY[]::text[]) FROM searchtag INNER JOIN removed USING (tagid)))",
            target=target.id,
            user=userid,
            tags=apply_tagids,
        )

        if target.feature == "submit":
            _update_submission_tags(tx, submitid=target.id)

    files.append(
        "%stag.%s.%s.log" % (m.MACRO_SYS_LOG_PATH, target.feature, d.get_timestamp()),
        "-%sID %i  -T %i  -UID %i  -X %s\n" % (target.feature[0].upper(), target.id, d.get_time(), userid,
                                               " ".join(tag_names)))
    d.serializable_retry(transaction)

    return sorted(tags_not_added)


def _set_commission_tags(*, userid: int, tag_names: set[NormalizedTag], table: str) -> None:
    entered_tagids = get_or_create_many(tag_names)

    def transaction(tx):
        tx.execute(
            f"DELETE FROM {table}"
            " WHERE targetid = %(user)s"
            " AND tagid != ALL (%(tags)s)",
            user=userid,
            tags=entered_tagids,
        )
        tx.execute(
            f"INSERT INTO {table} (tagid, targetid)"
            " SELECT tagid, %(user)s FROM UNNEST (%(tags)s::integer[]) AS tagid"
            " ON CONFLICT DO NOTHING",
            user=userid,
            tags=entered_tagids,
        )

    d.serializable_retry(transaction)


def set_commission_preferred_tags(*, userid: int, tag_names: set[NormalizedTag]) -> None:
    # enforce the limit on artist preference tags
    if len(tag_names) > MAX_PREFERRED_TAGS:
        raise WeasylError("tooManyPreferenceTags")

    _set_commission_tags(userid=userid, tag_names=tag_names, table="artist_preferred_tags")


def set_commission_optout_tags(*, userid: int, tag_names: set[NormalizedTag]) -> None:
    _set_commission_tags(userid=userid, tag_names=tag_names, table="artist_optout_tags")


def associate(*, userid: int, target: TaggableTarget, tag_names: set[NormalizedTag]) -> list[NormalizedTag]:
    """
    Associates tags with a content item.

    Parameters:
        userid: The userid of the user associating tags
        target: The content item to associate ``tags`` to
        tag_names: A set of tags

    Returns:
        A list of tag names that weren't added because they were on the owner's or the global restricted tag list.
    """
    ownerid = _get_ownerid(target)

    if not ownerid:
        raise WeasylError("TargetRecordMissing")
    # TODO: check if target deleted

    if userid != ownerid and userid not in staff.MODS:
        return _set_suggested_tags(
            userid=userid,
            target=target,
            ownerid=ownerid,
            tag_names=tag_names,
        )

    # Retrieve tag titles and tagid pairs, for new (if any) and existing tags
    entered_tagids = get_or_create_many(tag_names)

    def transaction(tx):
        tx.execute(
            "WITH"
            f" removed AS (DELETE FROM {target.table}"
            " WHERE targetid = %(target)s"
            " AND settings ~ 'a'"
            " AND tagid != ALL (%(tags)s) RETURNING tagid),"
            f" added AS (INSERT INTO {target.table} AS ct (targetid, tagid, settings, added_by)"
            " SELECT %(target)s, tag, 'a', %(user)s"
            " FROM UNNEST (%(tags)s::integer[]) AS tag"
            " ON CONFLICT (targetid, tagid) DO UPDATE SET settings = ct.settings || 'a', added_by = %(user)s WHERE ct.settings !~ 'a'"
            " RETURNING tagid)"
            + (
                f" INSERT INTO {target.history_table} ({target.history_id_column}, userid, added, removed)"
                if target.history_table else "")
            + " VALUES (%(target)s, %(user)s,"
            " (SELECT coalesce(array_agg(title), ARRAY[]::text[]) FROM searchtag INNER JOIN added USING (tagid)),"
            " (SELECT coalesce(array_agg(title), ARRAY[]::text[]) FROM searchtag INNER JOIN removed USING (tagid)))",
            target=target.id,
            user=userid,
            tags=entered_tagids,
        )

        if target.feature == "submit":
            _update_submission_tags(tx, submitid=target.id)

    files.append(
        "%stag.%s.%s.log" % (m.MACRO_SYS_LOG_PATH, target.feature, d.get_timestamp()),
        "-%sID %i  -T %i  -UID %i  -X %s\n" % (target.feature[0].upper(), target.id, d.get_time(), userid,
                                               " ".join(tag_names)))
    d.serializable_retry(transaction)

    return []


@enum.unique
class SuggestionAction(enum.Enum):
    REJECT = enum.auto()
    APPROVE = enum.auto()


@dataclass(frozen=True, slots=True)
class SuggestionActionFailure:
    pass


@dataclass(frozen=True, slots=True)
class SuggestionActionSuccess:
    undo_token: bytes | None


SuggestionActionResult = (
    SuggestionActionFailure
    | SuggestionActionSuccess
)


_undo_key = ChaCha20Poly1305(base64.urlsafe_b64decode(config_obj.get("secret_keys", "suggested_tag_undo")))
"""
The secret key used to ensure the secrecy (suggestions are anonymous) and authenticity (the suggestion attribution that will be restored on undo is stored in the token) of the data in undo tokens.

Fernet is almost good enough for this (even though its tokens are needlessly long for short messages, and it forces base64), but it doesn’t expose AEAD, and additional authenticated data is something that makes sense when the PUT and DELETE requests use the same path.
"""

_UNDO_TOKEN_MAX_CLOCK_SKEW = 2
"""The maximum acceptable time into the future of token timestamps, in seconds. Weasyl server clocks should be in sync to well within this."""

_UNDO_TOKEN_VALIDITY = 60
"""The time the undo token for approval/rejection of a suggested tag remains valid, in seconds."""

_UNDO_ENCRYPTED_PART = Struct("<I")
"""
The structure of the encrypted part of an undo token:

- user id of suggester
"""

_POLY1305_TAG_SIZE = 16
_UNDO_TOKEN_NONCE_SIZE = 12
_UNDO_HEADER = Struct(f"<{_UNDO_TOKEN_NONCE_SIZE}sI")
_UNDO_AAD = Struct("<IIIc")
"""
The structure of the serialized additional associated data for an undo token:

- unsigned timestamp (revisit before 2106-02)
- target id
- tag id
- target type ('s', 'c', or 'j')
"""


class UndoExpired(Exception):
    pass


def _undo_token_create(*, target: TaggableTarget, tagid: int, added_by: int) -> bytes:
    nonce = secrets.token_bytes(_UNDO_TOKEN_NONCE_SIZE)
    now = int(time.time())
    aad = _UNDO_AAD.pack(now, target.id, tagid, target.type_code)

    return _UNDO_HEADER.pack(nonce, now) + _undo_key.encrypt(
        nonce,
        _UNDO_ENCRYPTED_PART.pack(added_by),
        aad,
    )


def _undo_token_validate(
    *,
    target: TaggableTarget,
    tagid: int,
    undo_token: bytes,
) -> int:
    """
    Validates a tag suggestion action undo token, returning the user id of the suggester to restore.

    Throws `UndoExpired` when the undo token has expired.

    Throws `WeasylError("Unexpected")` or `cryptography.exceptions.InvalidTag` on unexpected conditions.
    """
    if len(undo_token) != _UNDO_HEADER.size + _UNDO_ENCRYPTED_PART.size + _POLY1305_TAG_SIZE:
        raise WeasylError("Unexpected")

    nonce, timestamp = _UNDO_HEADER.unpack_from(undo_token)
    now = int(time.time())

    if timestamp < now - _UNDO_TOKEN_VALIDITY:
        raise UndoExpired()

    if timestamp > now + _UNDO_TOKEN_MAX_CLOCK_SKEW:
        raise WeasylError("Unexpected")

    aad = _UNDO_AAD.pack(timestamp, target.id, tagid, target.type_code)
    decrypted = _undo_key.decrypt(nonce, undo_token[_UNDO_HEADER.size:], aad)
    (added_by,) = _UNDO_ENCRYPTED_PART.unpack(decrypted)

    return added_by


def suggestion_arbitrate(
    *,
    userid: int,
    target: TaggableTarget,
    tag_name: NormalizedTag,
    action: SuggestionAction,
) -> SuggestionActionResult:
    """
    Approve or reject a suggested tag.
    """
    ownerid = _get_ownerid(target)

    if not ownerid:
        raise WeasylError("TargetRecordMissing")

    if userid != ownerid and userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    tagid = _get_id(tag_name)

    # there are inherent concurrency issues we’re calling acceptable with the undo token approach, so don’t bother with a transaction
    check = tagid and d.engine.execute(
        "SELECT added_by, settings"
        f" FROM {target.table}"
        " WHERE (targetid, tagid) = (%(target)s, %(tag)s)",
        target=target.id,
        tag=tagid,
    ).first()

    if check is None:
        # never suggested, or already rejected
        match action:
            case SuggestionAction.APPROVE:
                return SuggestionActionFailure()
            case SuggestionAction.REJECT:
                return SuggestionActionSuccess(undo_token=None)
            case _:
                raise TypeError()

    if "a" in check.settings:
        # already approved
        match action:
            case SuggestionAction.APPROVE:
                return SuggestionActionSuccess(undo_token=None)
            case SuggestionAction.REJECT:
                return SuggestionActionFailure()
            case _:
                raise TypeError()

    if check.added_by is None:
        undo_token = None
    else:
        undo_token = _undo_token_create(
            target=target,
            tagid=tagid,
            added_by=check.added_by,
        )

    match action:
        case SuggestionAction.APPROVE:
            d.engine.execute(
                f"UPDATE {target.table}"
                " SET settings = settings || 'a', added_by = %(user)s"
                " WHERE (targetid, tagid) = (%(target)s, %(tag)s)"
                " AND settings !~ 'a'",
                target=target.id,
                tag=tagid,
                user=userid,
            )

        case SuggestionAction.REJECT:
            with d.engine.begin() as tx:
                tx.execute(
                    f"DELETE FROM {target.table}"
                    " WHERE (targetid, tagid) = (%(target)s, %(tag)s)",
                    target=target.id,
                    tag=tagid,
                )
                tx.execute(
                    f"INSERT INTO {target.feedback_table} (targetid, tagid, userid, incorrect, unwanted, abusive)"
                    " VALUES (%(target)s, %(tag)s, %(user)s, FALSE, FALSE, FALSE)"
                    " ON CONFLICT (targetid, tagid, userid) DO NOTHING",
                    target=target.id,
                    tag=tagid,
                    user=userid,
                )

        case _:
            raise TypeError()

    return SuggestionActionSuccess(undo_token=undo_token)


def suggestion_action_undo(
    *,
    userid: int,
    target: TaggableTarget,
    tag_name: NormalizedTag,
    undo_token: bytes,
) -> None:
    tagid = _get_id(tag_name)
    if tagid is None:
        raise WeasylError("Unexpected")

    restore_added_by = _undo_token_validate(
        target=target,
        tagid=tagid,
        undo_token=undo_token,
    )

    ownerid = _get_ownerid(target)

    # sanity check + limit the damage of a compromised key to the authenticated account
    if not ownerid or (userid != ownerid and userid not in staff.MODS):
        raise WeasylError("Unexpected")

    with d.engine.begin() as tx:
        tx.execute(
            f"INSERT INTO {target.table} AS ct (targetid, tagid, added_by)"
            " VALUES (%(target)s, %(tag)s, %(restore)s)"
            " ON CONFLICT (tagid, targetid) DO UPDATE SET settings = replace(ct.settings, 'a', ''), added_by = %(restore)s"
            " WHERE (ct.targetid, ct.tagid) = (%(target)s, %(tag)s)",
            target=target.id,
            tag=tagid,
            restore=restore_added_by,
        )
        tx.execute(
            f"DELETE FROM {target.feedback_table}"
            " WHERE (targetid, tagid, userid) = (%(target)s, %(tag)s, %(user)s)",
            target=target.id,
            tag=tagid,
            user=userid,
        )


@dataclass(frozen=True, slots=True)
class SuggestionFeedback:
    incorrect: bool
    unwanted: bool
    abusive: bool


def set_tag_feedback(
    *,
    userid: int,
    target: TaggableTarget,
    tag_name: NormalizedTag,
    feedback: SuggestionFeedback,
) -> None:
    ownerid = _get_ownerid(target)

    if userid != ownerid and userid not in staff.MODS:
        raise WeasylError("Unexpected")

    tagid = _get_or_create(tag_name)

    d.engine.execute(
        f"INSERT INTO {target.feedback_table}"
        " (targetid, tagid, userid, incorrect, unwanted, abusive)"
        " VALUES (%(target)s, %(tag)s, %(user)s, %(incorrect)s, %(unwanted)s, %(abusive)s)"
        " ON CONFLICT (targetid, tagid, userid) DO UPDATE SET"
        " incorrect = %(incorrect)s, unwanted = %(unwanted)s, abusive = %(abusive)s,"
        " last_modified = now()",
        target=target.id,
        tag=tagid,
        user=userid,
        incorrect=feedback.incorrect,
        unwanted=feedback.unwanted,
        abusive=feedback.abusive,
    )


def tag_history(submitid):
    db = d.connect()
    tu = d.meta.tables['tag_updates']
    pr = d.meta.tables['profile']
    return db.execute(
        sa.select([pr.c.username, tu.c.updated_at, tu.c.added, tu.c.removed])
        .select_from(tu.join(pr, tu.c.userid == pr.c.userid))
        .where(tu.c.submitid == submitid)
        .order_by(tu.c.updated_at.desc()))


def edit_user_tag_restrictions(userid: int, tags: set[TagPattern]) -> None:
    """
    Edits the user's restricted tag list, replacing all existing restricted tags with the specified set.

    Parameters:
        userid: The userid of the user submitting the request.

        tags: A set() object of tags; must have been passed through ``parse_restricted_tags()``
        (occurs in the the controllers/settings.py controller)
    """
    pattern_tagids = get_or_create_many(tags)

    def transaction(tx):
        # remove tags not being kept
        tx.execute("""
            DELETE FROM user_restricted_tags
            WHERE userid = %(uid)s
            AND tagid != ALL (%(replacement_set)s)
        """, uid=userid, replacement_set=pattern_tagids)

        # add new tags
        if pattern_tagids:
            tx.execute("""
                INSERT INTO user_restricted_tags (tagid, userid)
                    SELECT tag, %(uid)s
                    FROM UNNEST (%(replacement_set)s) AS tag
                    ON CONFLICT (userid, tagid) DO NOTHING
            """, uid=userid, replacement_set=pattern_tagids)

    d.serializable_retry(transaction)

    # Clear the cache for ``userid``'s restricted tags, since we made changes
    query_user_restricted_tags.invalidate(userid)


def edit_global_tag_restrictions(userid: int, tags: set[TagPattern]) -> None:
    """
    Edits the globally restricted tag list, adding or removing tags as appropriate.

    Parameters:
        userid: The userid of the director submitting the request.

        tags: A set() object of tags; must have been passed through ``parse_restricted_tags()``
        (occurs in the the controllers/director.py controller)
    """
    pattern_tagids = get_or_create_many(tags)

    def transaction(tx):
        # remove tags not being kept
        tx.execute("""
            DELETE FROM globally_restricted_tags
            WHERE tagid != ALL (%(replacement_set)s)
        """, replacement_set=pattern_tagids)

        # add new tags
        if pattern_tagids:
            tx.execute("""
                INSERT INTO globally_restricted_tags (tagid, userid)
                    SELECT tag, %(uid)s
                    FROM UNNEST (%(replacement_set)s) AS tag
                    ON CONFLICT (tagid) DO NOTHING
            """, uid=userid, replacement_set=pattern_tagids)

    d.serializable_retry(transaction)

    # Clear the globally restricted tags cache
    _query_global_restricted_tags.invalidate()


def get_global_tag_restrictions() -> dict[TagPattern, str]:
    """
    Retrieves a list of tags on the globally restricted tag list for display to a director.

    Returns:
        A dict mapping from globally restricted tag titles to the name of the director who added the tag.
    """
    query = d.engine.execute("""
        SELECT st.title, lo.login_name
        FROM globally_restricted_tags
        INNER JOIN searchtag AS st USING (tagid)
        INNER JOIN login AS lo USING (userid)
    """).fetchall()
    return {r.title: r.login_name for r in query}


@region.cache_on_arguments()
def query_user_restricted_tags(ownerid: int) -> list[TagPattern]:
    """
    Gets and returns restricted tags for users.

    Parameters:
        ownerid: The userid of the user who owns the content tags are being added to.

    Returns:
        A list of user restricted tag titles, in no particular order.
    """
    return d.engine.execute("""
        SELECT title
        FROM user_restricted_tags
        INNER JOIN searchtag USING (tagid)
        WHERE userid = %(ownerid)s
    """, ownerid=ownerid).scalars().all()


@region.cache_on_arguments()
def _query_global_restricted_tags() -> list[TagPattern]:
    """
    Gets and returns globally restricted tags.

    Parameters:
        None. Retrieves all global tag restriction entries.

    Returns:
        A list of global restricted tag titles, in no particular order.
    """
    return d.engine.execute("""
        SELECT title
        FROM globally_restricted_tags
        INNER JOIN searchtag USING (tagid)
    """).scalars().all()


def _get_restricted_tag_matcher(patterns: Iterable[TagPattern]) -> Callable[[NormalizedTag], object | None]:
    return re.compile("|".join(pattern.replace("*", ".*") for pattern in patterns)).fullmatch
