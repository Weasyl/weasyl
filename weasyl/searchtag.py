import base64
import enum
import re
import secrets
import time
from dataclasses import dataclass
from struct import Struct

import sqlalchemy as sa
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from sqlalchemy.sql.expression import any_

from libweasyl import staff
from libweasyl.cache import region

from weasyl import define as d
from weasyl import files
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl.config import config_obj
from weasyl.error import WeasylError


_TAG_DELIMITER = re.compile(r"[\s,]+")
# limited so people can't give themselves every tag
# and hog the top of marketplace results
MAX_PREFERRED_TAGS = 50


class TaggableTarget:
    __slots__ = ("id",)

    id: int

    def __init__(self, id: int) -> None:
        self.id = id


class SubmissionTarget(TaggableTarget):
    table = "searchmapsubmit"
    history_table = "tag_updates"
    feedback_table = "tag_suggestion_feedback_submission"
    feature = "submit"
    arg_name = history_id_column = "submitid"
    path_component = "submission"
    type_code = b"s"


class CharacterTarget(TaggableTarget):
    table = "searchmapchar"
    history_table = None
    feedback_table = "tag_suggestion_feedback_character"
    feature = "char"
    arg_name = "charid"
    path_component = "character"
    type_code = b"c"


class JournalTarget(TaggableTarget):
    table = "searchmapjournal"
    history_table = None
    feedback_table = "tag_suggestion_feedback_journal"
    feature = "journal"
    arg_name = "journalid"
    path_component = "journal"
    type_code = b"j"


_TARGET_TYPES_BY_CODE = {
    t.type_code: t
    for t in (
        SubmissionTarget,
        CharacterTarget,
        JournalTarget,
    )
}

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


@region.cache_multi_on_arguments()
def _get_or_create(*names: str) -> list[int]:
    names_list = list(names)

    d.engine.execute('''
        INSERT INTO searchtag (title)
        SELECT title
        FROM UNNEST(%(names)s::text[]) AS title
        ON CONFLICT (title) DO NOTHING
    ''', names=names_list)

    result = d.engine.execute(
        'SELECT tagid FROM searchtag WHERE title = ANY (%(names)s)',
        names=names_list)

    return result.scalars().all()


def get_or_create(name):
    return _get_or_create(d.get_search_tag(name))


def get_or_create_many(names: list[str]) -> list[int]:
    normalized_names = map(d.get_search_tag, names)
    return _get_or_create(*normalized_names)


def get_ids(names):
    result = d.engine.execute(
        "SELECT tagid, title FROM searchtag WHERE title = ANY (%(names)s)",
        names=list(names))

    return {row.title: row.tagid for row in result}


def parse_tags(text: str) -> set[str]:
    tags = set()

    for i in _TAG_DELIMITER.split(text):
        tag = d.get_search_tag(i)

        if tag:
            tags.add(tag)

    return tags


def parse_restricted_tags(text):
    """
    A custom implementation of ``parse_tags()`` for the restricted tag list.
    Enforces the desired characteristics of restricted tags, and allows an asterisk
    character, whereas ``parse_tags()`` would strip asterisks.

    Parameters:
        text: The string to parse for tags

    Returns:
        tags: A set() with valid tags.
    """
    tags = set()

    for i in _TAG_DELIMITER.split(text):
        target = "".join([c for c in i if ord(c) < 128])
        target = "".join(i for i in target if i.isalnum() or i in "_*")
        target = target.strip("_")
        target = "_".join(i for i in target.split("_") if i)

        if is_tag_restriction_pattern_valid(target):
            tags.add(target.lower())

    return tags


def is_tag_restriction_pattern_valid(text):
    """
    Determines if a given piece of text is considered a valid restricted tag pattern.

    Valid patterns:
    - Length: 0 < x <= 100 -- Prevents absurd tag lengths.
    - If string contains a ``*``, must only contain one *, and be three characters or more.

    Parameters:
        text: A single candidate restricted tag entry.

    Returns:
        Boolean True if the tag is considered to be a valid pattern. Boolean False otherwise.
    """
    if len(text) > 100:
        return False
    elif text.count("*") == 1 and len(text) > 2:
        return True
    elif text and "*" not in text:
        return True
    return False


def _update_submission_tags(tx, submitid):
    tx.execute(
        "WITH t AS ("
        " SELECT coalesce(array_agg(tagid), ARRAY[]::integer[]) AS tags FROM searchmapsubmit WHERE targetid = %(submission)s)"
        " INSERT INTO submission_tags (submitid, tags) SELECT %(submission)s, tags FROM t"
        " ON CONFLICT (submitid) DO UPDATE SET tags = (SELECT tags FROM t)",
        submission=submitid,
    )


def _target_unpack(type_code: bytes, id: int) -> TaggableTarget:
    t = _TARGET_TYPES_BY_CODE.get(type_code)

    if t is None:
        raise WeasylError("Unexpected")

    return t(id)


def _get_ownerid(target: TaggableTarget) -> int | None:
    return d.get_ownerid(**{target.arg_name: target.id})


def _set_suggested_tags(
    *,
    userid: int,
    target: TaggableTarget,
    ownerid: int,
    tag_names: set[str],
) -> list[str]:
    tagging_privileges_revoked = "g" in d.get_config(userid)
    if tagging_privileges_revoked:
        raise WeasylError("InsufficientPermissions")

    if ignoreuser.check(ownerid, userid):
        raise WeasylError("contentOwnerIgnoredYou")

    # Track which tags fail to be added or removed to later notify the user
    is_restricted_tag = _get_restricted_tag_matcher({
        *query_user_restricted_tags(ownerid),
        *query_global_restricted_tags(),
    })
    tags_not_added = set(filter(is_restricted_tag, tag_names))
    apply_tags = tag_names - tags_not_added
    apply_tagids = [t.tagid for t in add_and_get_searchtags(apply_tags)]

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


def _set_commission_tags(*, userid: int, tag_names: set[str], table: str) -> None:
    query = add_and_get_searchtags(tag_names)
    entered_tagids = [t.tagid for t in query]

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


def set_commission_preferred_tags(*, userid: int, tag_names: set[str]) -> None:
    # enforce the limit on artist preference tags
    if len(tag_names) > MAX_PREFERRED_TAGS:
        raise WeasylError("tooManyPreferenceTags")

    _set_commission_tags(userid=userid, tag_names=tag_names, table="artist_preferred_tags")


def set_commission_optout_tags(*, userid: int, tag_names: set[str]) -> None:
    _set_commission_tags(userid=userid, tag_names=tag_names, table="artist_optout_tags")


def associate(*, userid: int, target: TaggableTarget, tag_names: set[str]) -> list[str]:
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
    query = add_and_get_searchtags(tag_names)
    entered_tagids = [t.tagid for t in query]

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
    tag_name: str,
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

    tagid = get_or_create(tag_name)

    # there are inherent concurrency issues we’re calling acceptable with the undo token approach, so don’t bother with a transaction
    check = d.engine.execute(
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
    tag_name: str,
    undo_token: bytes,
) -> None:
    tagid = get_or_create(tag_name)

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
    tag_name: int,
    feedback: SuggestionFeedback,
) -> None:
    ownerid = _get_ownerid(target)

    if userid != ownerid and userid not in staff.MODS:
        raise WeasylError("Unexpected")

    tagid = get_or_create(tag_name)

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


def add_and_get_searchtags(tags):
    """
    Get tag ids for the provided tag names, creating ids for new tags as necessary.

    Parameters:
        tags: A set of tag names, already validated and normalized.

    Returns:
        A list of `(tagid, title)` `RowProxy` objects: one for each tag name.
    """
    # Get the tag titles/ids out of the searchtag table
    query = d.engine.execute("""
        SELECT tagid, title FROM searchtag WHERE title = ANY (%(title)s)
    """, title=list(tags)).fetchall()

    # Determine which (if any) of the valid tags are new; add them to the searchtag table if so.
    newtags = list(tags - {x.title for x in query})
    if newtags:
        query.extend(
            d.engine.execute(
                "INSERT INTO searchtag (title) SELECT * FROM UNNEST (%(newtags)s) AS title RETURNING tagid, title",
                newtags=newtags
            ).fetchall())
    return query


def edit_user_tag_restrictions(userid, tags):
    """
    Edits the user's restricted tag list, by dropping all rows for ``userid`` and reinserting
    any ``tags`` passed in to the function.

    Parameters:
        userid: The userid of the user submitting the request.

        tags: A set() object of tags; must have been passed through ``parse_restricted_tags()``
        (occurs in the the controllers/settings.py controller)

    Returns:
        Nothing.
    """
    # First, drop all rows from the user_restricted_tags table for userid
    d.engine.execute("""
        DELETE FROM user_restricted_tags
        WHERE userid = %(uid)s
    """, uid=userid)

    # Retrieve tag titles and tagid pairs, for new (if any) and existing tags
    query = add_and_get_searchtags(tags)

    # Insert the new restricted tag for ``userid`` entries into the table (if we have any tags to add)
    if query:
        d.engine.execute("""
            INSERT INTO user_restricted_tags (tagid, userid)
                SELECT tag, %(uid)s
                FROM UNNEST (%(added)s) AS tag
        """, uid=userid, added=[tag.tagid for tag in query])

    # Clear the cache for ``userid``'s restricted tags, since we made changes
    query_user_restricted_tags.invalidate(userid)


def edit_global_tag_restrictions(userid, tags):
    """
    Edits the globally restricted tag list, adding or removing tags as appropriate.

    Parameters:
        userid: The userid of the director submitting the request.

        tags: A set() object of tags; must have been passed through ``parse_restricted_tags()``
        (occurs in the the controllers/director.py controller)

    Returns:
        Nothing.
    """
    # Only directors can edit the global restriction list; sanity check against the @director_only decorator
    if userid not in staff.DIRECTORS:
        raise WeasylError("InsufficientPermissions")

    existing = d.engine.execute("""
        SELECT tagid FROM globally_restricted_tags
    """).fetchall()

    # Retrieve tag titles and tagid pairs, for new and existing tags
    query = add_and_get_searchtags(tags)

    existing_tagids = {t.tagid for t in existing}
    entered_tagids = {t.tagid for t in query}

    # Assign added and removed
    added = entered_tagids - existing_tagids
    removed = existing_tagids - entered_tagids

    if added:
        d.engine.execute("""
            INSERT INTO globally_restricted_tags (tagid, userid)
                SELECT tag, %(uid)s
                FROM UNNEST (%(added)s) AS tag
        """, uid=userid, added=list(added))

    if removed:
        d.engine.execute("""
            DELETE FROM globally_restricted_tags
            WHERE tagid = ANY (%(removed)s)
        """, removed=list(removed))

    # Clear the globally restricted tags cache if any changes were made
    if added or removed:
        query_global_restricted_tags.invalidate()


def get_global_tag_restrictions(userid):
    """
    Retrieves a list of tags on the globally restricted tag list for display to a director.

    Parameters:
        userid: The userid of the director requesting the list of tags.

    Returns:
        A dict mapping from globally restricted tag titles to the name of the director who added the tag.
    """
    # Only directors can view the globally restricted tag list; sanity check against the @director_only decorator
    if userid not in staff.DIRECTORS:
        raise WeasylError("InsufficientPermissions")

    query = d.engine.execute("""
        SELECT st.title, lo.login_name
        FROM globally_restricted_tags
        INNER JOIN searchtag AS st USING (tagid)
        INNER JOIN login AS lo USING (userid)
    """).fetchall()
    return {r.title: r.login_name for r in query}


@region.cache_on_arguments()
def query_user_restricted_tags(ownerid):
    """
    Gets and returns restricted tags for users.

    Parameters:
        ownerid: The userid of the user who owns the content tags are being added to.

    Returns:
        A list of user restricted tag titles, in no particular order.
    """
    query = d.engine.execute("""
        SELECT title
        FROM user_restricted_tags
        INNER JOIN searchtag USING (tagid)
        WHERE userid = %(ownerid)s
    """, ownerid=ownerid).fetchall()
    return [tag.title for tag in query]


@region.cache_on_arguments()
def query_global_restricted_tags():
    """
    Gets and returns globally restricted tags.

    Parameters:
        None. Retrieves all global tag restriction entries.

    Returns:
        A list of global restricted tag titles, in no particular order.
    """
    query = d.engine.execute("""
        SELECT title
        FROM globally_restricted_tags
        INNER JOIN searchtag USING (tagid)
    """).fetchall()
    return [tag.title for tag in query]


def _get_restricted_tag_matcher(patterns):
    return re.compile("|".join(pattern.replace("*", ".*") for pattern in patterns)).fullmatch
