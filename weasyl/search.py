import re
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import chain
from typing import Any
from typing import Literal
from typing import NamedTuple

from libweasyl.ratings import GENERAL, MATURE, EXPLICIT

from weasyl import character, journal, media, searchtag, submission
from weasyl import define as d
from weasyl.forms import NormalizedTag
from weasyl.forms import parse_sysname
from weasyl.forms import parse_tag
from weasyl.users import Username


PostType = Literal["submit", "char", "journal"]
SearchType = PostType | Literal["user"]

_QUERY_FIND_MODIFIERS: Mapping[str, SearchType] = {
    "#submission": "submit",
    "#character": "char",
    "#journal": "journal",
    "#user": "user",
}

_QUERY_RATING_MODIFIERS = {
    "#general": GENERAL.code,
    "#mature": MATURE.code,
    "#explicit": EXPLICIT.code,
}

_QUERY_DELIMITER = re.compile(r"[\s,;]+")

_TABLE_INFORMATION: Mapping[PostType, tuple[int, str, str, str, str | int]] = {
    "submit": (10, "s", "submission", "submitid", "subtype"),
    # The subtype values for characters and journals are fake
    # and set to permit us to reuse the same sql query.
    "char": (20, "f", "character", "charid", 3999),
    "journal": (30, "j", "journal", "journalid", 3999),
}


class Query:
    possible_includes: set[NormalizedTag]
    required_includes: set[NormalizedTag]
    required_excludes: set[NormalizedTag]
    required_user_includes: set[str]
    required_user_excludes: set[str]
    ratings: set[int]
    find: SearchType

    def __init__(self):
        self.possible_includes = set()
        self.required_includes = set()
        self.required_excludes = set()
        self.required_user_includes = set()
        self.required_user_excludes = set()
        self.ratings = set()
        self.find = None

    def add_criterion(self, criterion):
        def add_nonempty(s, item):
            if item:
                s.add(item)

        find_modifier = _QUERY_FIND_MODIFIERS.get(criterion)

        if find_modifier:
            self.find = find_modifier
            return

        rating_modifier = _QUERY_RATING_MODIFIERS.get(criterion)

        if rating_modifier:
            self.ratings.add(rating_modifier)
            return

        if criterion.startswith(("user:", "+user:")):
            user = parse_sysname(criterion.split(":", 1)[1])
            add_nonempty(self.required_user_includes, user)
        elif criterion.startswith("-user:"):
            user = parse_sysname(criterion.split(":", 1)[1])
            add_nonempty(self.required_user_excludes, user)
        elif criterion.startswith("+"):
            tag = parse_tag(criterion[1:])
            add_nonempty(self.required_includes, tag)
        elif criterion.startswith("-"):
            tag = parse_tag(criterion[1:])
            add_nonempty(self.required_excludes, tag)
        elif criterion.startswith("|"):
            tag = parse_tag(criterion[1:])
            add_nonempty(self.possible_includes, tag)
        else:
            tag = parse_tag(criterion)
            add_nonempty(self.required_includes, tag)

    def __bool__(self):
        return bool(
            self.possible_includes or
            self.required_includes or
            self.required_excludes or
            self.required_user_includes or
            self.required_user_excludes or
            self.ratings)

    def get_terms_string(self) -> str:
        return " ".join(chain(
            sorted(self.required_includes),
            (f"|{t}" for t in sorted(self.possible_includes)),
            (f"-{t}" for t in sorted(self.required_excludes)),
            (f"user:{u}" for u in sorted(self.required_user_includes)),
            (f"-user:{u}" for u in sorted(self.required_user_excludes)),
        ))

    @classmethod
    def parse(cls, query_string, find_default):
        """
        Parses a search query string into collections of tags and users.
        """
        query = Query()

        for criterion in _QUERY_DELIMITER.split(query_string.strip()):
            if criterion:
                query.add_criterion(criterion)

        query.possible_includes.difference_update(query.required_includes)
        query.required_excludes.difference_update(query.required_includes)
        query.possible_includes.difference_update(query.required_excludes)

        if len(query.possible_includes) == 1:
            query.required_includes.add(query.possible_includes.pop())

        if query.find is None:
            query.find = find_default

        query.text = query_string

        return query

    def as_simple(self) -> str | None:
        """
        Get the single normalized tag name, if this query is for one tag with no other criteria.
        """
        if (
            len(self.required_includes) == 1
            and not self.possible_includes
            and not self.required_excludes
            and not self.required_user_includes
            and not self.required_user_excludes
            and not self.ratings
        ):
            [tag_name] = self.required_includes
            return tag_name

        return None


def select_users(q):
    terms = q.lower().split()
    statement = """
        SELECT userid, full_name, created_at, username FROM profile
        WHERE LOWER(username) SIMILAR TO ('%%(' || %(terms)s || ')%%') ESCAPE ''
            OR LOWER(full_name) SIMILAR TO ('%%(' || %(terms)s || ')%%') ESCAPE ''
        ORDER BY username
        LIMIT 100
    """

    query = d.engine.execute(statement, terms="|".join(terms))

    ret = [{
        "contype": 50,
        "userid": i.userid,
        "title": i.full_name,
        "rating": "",
        "unixtime": i.created_at,
        "username": i.username,
    } for i in query]
    media.populate_with_user_media(ret)
    return ret


Results = list[dict[str, Any]]


class _FirstPage:
    __slots__ = ()


FIRST_PAGE = _FirstPage()


class PrevFilter(NamedTuple):
    backid: int


class NextFilter(NamedTuple):
    nextid: int


@dataclass(frozen=True, slots=True)
class ResolvedQuery:
    possible_includes: set[int]
    required_includes: set[int]
    required_excludes: set[int]
    required_user_includes: set[int]
    required_user_excludes: set[int]
    ratings: set[int]
    find: PostType


def resolve(search: Query) -> ResolvedQuery | None:
    if search.find == "user":
        raise TypeError("user searches not supported")  # pragma: no cover

    all_names = (
        search.possible_includes
        | search.required_includes
        | search.required_excludes
    )

    all_user_sysnames = (
        search.required_user_includes
        | search.required_user_excludes
    )

    tag_ids = searchtag.get_ids(*all_names)

    def get_tag_ids(names: set[NormalizedTag]) -> set[int]:
        return {tag_ids.get(name, 0) for name in names}

    user_ids = d.get_userids(all_user_sysnames)

    def get_user_ids(names: set[str]) -> set[int]:
        return {user_ids[name] for name in names}

    required_includes = get_tag_ids(search.required_includes)
    required_user_includes = get_user_ids(search.required_user_includes)

    if 0 in required_includes or 0 in required_user_includes:
        return None

    possible_includes = get_tag_ids(search.possible_includes)
    possible_includes.discard(0)

    required_excludes = get_tag_ids(search.required_excludes)
    required_excludes.discard(0)

    required_user_excludes = get_user_ids(search.required_user_excludes)
    required_user_excludes.discard(0)

    return ResolvedQuery(
        possible_includes=possible_includes,
        required_includes=required_includes,
        required_excludes=required_excludes,
        required_user_includes=required_user_includes,
        required_user_excludes=required_user_excludes,
        ratings=search.ratings,
        find=search.find,
    )


def _prepare_search(
    *,
    userid,
    rating,
    resolved: ResolvedQuery,
    within,
    cat,
    subcat,
):
    _type_code, type_letter, table, select, subtype = _TABLE_INFORMATION[resolved.find]

    # Begin statement
    statement_with = ""
    statement_from_base = "FROM {table} content"
    statement_from_join = ["INNER JOIN profile ON content.userid = profile.userid"]
    statement_where = ["WHERE content.rating <= %(rating)s AND NOT content.friends_only AND NOT content.hidden"]
    statement_group = []

    # Use the `searchmap*` table, even for submissions, for the fastest possible search if looking for exactly one tag
    is_single_tag = (
        not userid  # with no blocktags
        and len(resolved.required_includes) == 1
        and not resolved.possible_includes
        and not resolved.required_excludes
    )

    if not is_single_tag and resolved.find == "submit":
        statement_from_join.append("INNER JOIN submission_tags ON content.submitid = submission_tags.submitid")

    if resolved.required_includes:
        if not is_single_tag and resolved.find == "submit":
            statement_from_join.append("AND submission_tags.tags @> %(required_includes)s")
        else:
            statement_from_join.append("INNER JOIN searchmap{find} ON targetid = content.{select}")
            statement_where.append("AND searchmap{find}.tagid = ANY (%(required_includes)s)")

            if not is_single_tag:
                statement_group.append(
                    "GROUP BY content.{select}, profile.username HAVING COUNT(searchmap{find}.tagid) = %(required_include_count)s")

    # Submission category or subcategory
    if resolved.find == "submit":
        if subcat:
            statement_where.append("AND content.subtype = %(subcategory)s")
        elif cat:
            statement_where.append("AND content.subtype >= %(category)s AND content.subtype < %(category)s + 1000")

    if userid:
        if within == "notify":
            # Search within notifications
            statement_from_join.append("INNER JOIN welcome ON welcome.targetid = content.{select}")
            statement_where.append("AND welcome.userid = %(userid)s")
            statement_where.append({
                "submit": "AND welcome.type IN (2010, 2030)",
                "char": "AND welcome.type = 2050",
                "journal": "AND welcome.type = 1010",
            }[resolved.find])
        elif within == "fave":
            # Search within favorites
            statement_from_join.append("INNER JOIN favorite ON favorite.targetid = content.{select}")
            statement_where.append("AND favorite.userid = %(userid)s AND favorite.type = %(type)s")
        elif within == "friend":
            # Search within friends content
            statement_from_join.append(
                "INNER JOIN frienduser ON ((frienduser.userid, frienduser.otherid) = (%(userid)s, content.userid)"
                " OR (frienduser.userid, frienduser.otherid) = (content.userid, %(userid)s))"
                " AND frienduser.settings !~ 'p'")
        elif within == "follow":
            # Search within following content
            statement_from_join.append(
                "INNER JOIN watchuser ON (watchuser.userid, watchuser.otherid) = (%(userid)s, content.userid)")

        # Search within rating
        if resolved.ratings:
            statement_where.append("AND content.rating = ANY (%(ratings)s)")

        # Blocked tags and ignored users
        statement_where.append("""
            AND NOT EXISTS (
                SELECT 0 FROM ignoreuser
                WHERE userid = %(userid)s
                    AND otherid = content.userid)
        """)

        if resolved.find == "submit":
            statement_with = """
                WITH
                    bg AS (SELECT COALESCE(array_agg(tagid), ARRAY[]::INTEGER[]) AS tags FROM blocktag WHERE userid = %(userid)s AND rating = 10),
                    ba AS (SELECT COALESCE(array_agg(tagid), ARRAY[]::INTEGER[]) AS tags FROM blocktag WHERE userid = %(userid)s AND rating = 30),
                    bp AS (SELECT COALESCE(array_agg(tagid), ARRAY[]::INTEGER[]) AS tags FROM blocktag WHERE userid = %(userid)s AND rating = 40)
            """

            statement_where.append("""
                AND NOT submission_tags.tags && (SELECT tags FROM bg)
                AND (content.rating < 30 OR NOT submission_tags.tags && (SELECT tags FROM ba))
                AND (content.rating < 40 OR NOT submission_tags.tags && (SELECT tags FROM bp))
            """)
        else:
            statement_where.append("""
                AND NOT EXISTS (
                    SELECT 0 FROM searchmap{find}
                    WHERE targetid = content.{select}
                        AND tagid IN (SELECT tagid FROM blocktag WHERE userid = %(userid)s AND rating <= content.rating))
            """)

    if resolved.possible_includes:
        if resolved.find == "submit":
            statement_where.append("AND submission_tags.tags && %(possible_includes)s")
        else:
            statement_where.append("""
                AND EXISTS (
                    SELECT 0 FROM searchmap{find}
                    WHERE targetid = content.{select}
                        AND tagid = ANY (%(possible_includes)s)
                )
            """)

    if resolved.required_excludes:
        if resolved.find == "submit":
            statement_where.append("AND NOT submission_tags.tags && %(required_excludes)s")
        else:
            statement_where.append("""
                AND NOT EXISTS (
                    SELECT 0 FROM searchmap{find}
                    WHERE targetid = content.{select}
                        AND tagid = ANY (%(required_excludes)s)
                )
            """)

    if resolved.required_user_includes:
        statement_where.append("AND content.userid = ANY (%(required_user_includes)s)")

    if resolved.required_user_excludes:
        statement_where.append("AND content.userid != ALL (%(required_user_excludes)s)")

    title_field = "title"

    match resolved.find:
        case "char":
            title_field = "char_name"
            extra_fields = ", content.settings"
        case "journal":
            extra_fields = ", content.content"
        case _:
            extra_fields = ""

    def make_statement(
        statement_select,
        statement_additional_where,
        statement_order,
        *,
        tablesample="",
    ):
        return " ".join([
            statement_with,
            statement_select,
            statement_from_base,
            tablesample,
            " ".join(statement_from_join),
            " ".join(statement_where),
            statement_additional_where,
            " ".join(statement_group),
            statement_order,
        ]).format(
            table=table,
            find=resolved.find,
            select=select,
            subtype=subtype,
            title_field=title_field,
            extra_fields=extra_fields,
        )

    params = {
        "possible_includes": list(resolved.possible_includes),
        "required_includes": list(resolved.required_includes),
        "required_excludes": list(resolved.required_excludes),
        "required_user_includes": list(resolved.required_user_includes),
        "required_user_excludes": list(resolved.required_user_excludes),
        "type": type_letter,
        "userid": userid,
        "rating": rating,
        "ratings": list(resolved.ratings),
        "category": cat,
        "subcategory": subcat,
        "required_include_count": len(resolved.required_includes),
    }

    return make_statement, params


def _find_without_media(
    *,
    userid,
    rating,
    limit: int,
    resolved: ResolvedQuery,
    within,
    cat,
    subcat,
    page: _FirstPage | PrevFilter | NextFilter,
) -> tuple[Results, PrevFilter | None, NextFilter | None]:
    type_code, _type_letter, _table, select, _subtype = _TABLE_INFORMATION[resolved.find]
    make_statement, params = _prepare_search(
        userid=userid,
        rating=rating,
        resolved=resolved,
        within=within,
        cat=cat,
        subcat=subcat,
    )

    match page:
        case PrevFilter(backid):
            pagination_filter = "AND content.{select} > %(backid)s"
            params["backid"] = backid
            is_back = True
        case NextFilter(nextid):
            pagination_filter = "AND content.{select} < %(nextid)s"
            params["nextid"] = nextid
            is_back = False
        case _:
            assert page is FIRST_PAGE
            pagination_filter = ""
            is_back = False

    statement = make_statement(
        """
        SELECT
            content.{select}, content.{title_field} AS title, content.rating, content.unixtime, content.userid,
            profile.username, {subtype} as subtype
            {extra_fields}
        """,
        pagination_filter,
        (
            "ORDER BY content.{select}"
            f"{'' if is_back else ' DESC'}"
            f" LIMIT {limit + 1}"
        ),
    )

    query = d.engine.execute(statement, params)

    ret = [{"contype": type_code, **i} for i in query]

    # Selected one more result than will be returned to check if there’s a next page in the queried direction.
    has_more = len(ret) == limit + 1
    if has_more:
        del ret[-1]

    if is_back:
        ret.reverse()

    # A surrounding page is absent in any of these cases:
    # - there are no results
    # - `has_more` checked in that direction and returned a negative
    # - it’s the back page of the first page
    prev_page = (
        None if page is FIRST_PAGE or ((not has_more) and is_back) or not ret
        else PrevFilter(ret[0][select])
    )
    next_page = (
        None if ((not has_more) and (not is_back)) or not ret
        else NextFilter(ret[-1][select])
    )
    return ret, prev_page, next_page


def select_count(*, page: PrevFilter | NextFilter, **kwargs) -> int:
    """
    Get an approximate count of search results starting at some page.
    """
    make_statement, params = _prepare_search(**kwargs)

    cont_key: Literal["backid", "nextid"]

    # The PostgreSQL function that determines, from a result set of ids, the anchor for the next page in the same direction.
    cont_func: Literal["max", "min"]

    match page:
        case PrevFilter(backid):
            filter = "AND content.{select} > %(backid)s"
            params[cont_key := "backid"] = backid
            cont_func = "max"
            order = ""
        case NextFilter(nextid):
            filter = "AND content.{select} < %(nextid)s"
            params[cont_key := "nextid"] = nextid
            cont_func = "min"
            order = "DESC"
        case _:  # pragma: no cover
            raise TypeError("invalid page")

    total_count = 0

    # Count up to 100 results precisely.
    count_limit = 100

    for sample_percent in [100, 10, 1]:
        sample_count, continuation = d.engine.execute(
            make_statement(
                (
                    f"SELECT COUNT(*), {cont_func}(postid)"
                    " FROM (SELECT content.{select} AS postid"
                ),
                filter,
                (
                    "ORDER BY content.{select}"
                    f" {order} LIMIT {count_limit}"
                    ") _"
                ),
                # Use REPEATABLE to prevent the user from seeing different counts on refresh.
                tablesample=f" TABLESAMPLE SYSTEM ({sample_percent}) REPEATABLE (0)" if sample_percent < 100 else "",
            ),
            params,
        ).one()

        total_count += sample_count * (100 // sample_percent)

        if sample_count < count_limit:
            break

        params[cont_key] = continuation

        # Count up to 10 times as many results in total next round. The results so far will be 10% of that, and the next round will be the remaining 90% (100 * 10% + 90 = 100).
        count_limit = 90

    return total_count


def select(**kwargs) -> tuple[Results, PrevFilter | None, NextFilter | None]:
    find = kwargs['resolved'].find
    results, prev_page, next_page = _find_without_media(**kwargs)

    if find == 'submit':
        media.populate_with_submission_media(results)
    elif find == 'char':
        for r in results:
            r['sub_media'] = character.fake_media_items(
                r['charid'], r['userid'], Username.from_stored(r['username']).sysname, r['settings'])
    elif find == 'journal':
        media.populate_with_user_media(results)

    return results, prev_page, next_page


def browse(
    userid,
    rating,
    limit,
    find: Literal["submit", "char", "journal", "critique"],
    cat,
    backid,
    nextid,
):
    if find == "char":
        return character.select_list(userid, rating, limit, backid=backid, nextid=nextid)
    elif find == "journal":
        return journal.select_user_list(userid, rating, limit, backid=backid, nextid=nextid)
    else:
        return submission.select_list(userid, rating, limit=limit, backid=backid, nextid=nextid,
                                      subcat=d.get_int(cat) if d.get_int(cat) in [1000, 2000, 3000] else None,
                                      critique_only=find == "critique")
