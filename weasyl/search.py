# encoding: utf-8

from __future__ import absolute_import

import re

from libweasyl.ratings import GENERAL, MATURE, EXPLICIT

from weasyl import character, journal, media, searchtag, submission
from weasyl import define as d


_QUERY_FIND_MODIFIERS = {
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

_TABLE_INFORMATION = {
    "submit": (10, "s", "submission", "submitid", "subtype"),
    # The subtype values for characters and journals are fake
    # and set to permit us to reuse the same sql query.
    "char": (20, "f", "character", "charid", 3999),
    "journal": (30, "j", "journal", "journalid", 3999),
}

COUNT_LIMIT = 10000


class Query:
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
            user = d.get_sysname(criterion.split(":", 1)[1])
            add_nonempty(self.required_user_includes, user)
        elif criterion.startswith("-user:"):
            user = d.get_sysname(criterion.split(":", 1)[1])
            add_nonempty(self.required_user_excludes, user)
        elif criterion.startswith("+"):
            tag = d.get_search_tag(criterion[1:])
            add_nonempty(self.required_includes, tag)
        elif criterion.startswith("-"):
            tag = d.get_search_tag(criterion[1:])
            add_nonempty(self.required_excludes, tag)
        elif criterion.startswith("|"):
            tag = d.get_search_tag(criterion[1:])
            add_nonempty(self.possible_includes, tag)
        else:
            tag = d.get_search_tag(criterion)
            add_nonempty(self.required_includes, tag)

    def __nonzero__(self):
        return bool(
            self.possible_includes or
            self.required_includes or
            self.required_excludes or
            self.required_user_includes or
            self.required_user_excludes or
            self.ratings)

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

        if query.find is None:
            query.find = find_default

        query.text = query_string

        return query


def select_users(q):
    terms = q.lower().split()
    statement = """
        SELECT userid, full_name, unixtime, username FROM profile
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
        "unixtime": i.unixtime,
        "username": i.username,
    } for i in query]
    media.populate_with_user_media(ret)
    return ret


def _find_without_media(userid, rating, limit,
                        search, within, cat, subcat, backid, nextid):
    type_code, type_letter, table, select, subtype = _TABLE_INFORMATION[search.find]

    # Begin statement
    statement_with = ""
    statement_from = ["FROM {table} content INNER JOIN profile ON content.userid = profile.userid"]
    statement_where = ["WHERE content.rating <= %(rating)s AND content.settings !~ '[fhm]'"]
    statement_group = []

    if search.find == "submit":
        statement_from.append("INNER JOIN submission_tags ON content.submitid = submission_tags.submitid")

    if search.required_includes:
        if search.find == "submit":
            statement_from.append("AND submission_tags.tags @> %(required_includes)s")
        else:
            statement_from.append("INNER JOIN searchmap{find} ON targetid = content.{select}")
            statement_where.append("AND searchmap{find}.tagid = ANY (%(required_includes)s)")
            statement_group.append(
                "GROUP BY content.{select}, profile.username HAVING COUNT(searchmap{find}.tagid) = %(required_include_count)s")

    # Submission category or subcategory
    if search.find == "submit":
        if subcat:
            statement_where.append("AND content.subtype = %(subcategory)s")
        elif cat:
            statement_where.append("AND content.subtype >= %(category)s AND content.subtype < %(category)s + 1000")

    if userid:
        if within == "notify":
            # Search within notifications
            statement_from.append("INNER JOIN welcome ON welcome.targetid = content.{select}")
            statement_where.append("AND welcome.userid = %(userid)s")
            statement_where.append({
                "submit": "AND welcome.type IN (2010, 2030, 2040)",
                "char": "AND welcome.type = 2050",
                "journal": "AND welcome.type IN (1010, 1020)",
            }[search.find])
        elif within == "fave":
            # Search within favorites
            statement_from.append("INNER JOIN favorite ON favorite.targetid = content.{select}")
            statement_where.append("AND favorite.userid = %(userid)s AND favorite.type = %(type)s")
        elif within == "friend":
            # Search within friends content
            statement_from.append(
                "INNER JOIN frienduser ON (frienduser.userid, frienduser.otherid) = (%(userid)s, content.userid)"
                " OR (frienduser.userid, frienduser.otherid) = (content.userid, %(userid)s)")
        elif within == "follow":
            # Search within following content
            statement_from.append(
                "INNER JOIN watchuser ON (watchuser.userid, watchuser.otherid) = (%(userid)s, content.userid)")

        # Search within rating
        if search.ratings:
            statement_where.append("AND content.rating = ANY (%(ratings)s)")

        # Blocked tags and ignored users
        statement_where.append("""
            AND NOT EXISTS (
                SELECT 0 FROM ignoreuser
                WHERE userid = %(userid)s
                    AND otherid = content.userid)
        """)

        if search.find == "submit":
            statement_with = """
                WITH
                    bg AS (SELECT COALESCE(array_agg(tagid), ARRAY[]::INTEGER[]) AS tags FROM blocktag WHERE userid = %(userid)s AND rating = 10),
                    bm AS (SELECT COALESCE(array_agg(tagid), ARRAY[]::INTEGER[]) AS tags FROM blocktag WHERE userid = %(userid)s AND rating = 20),
                    ba AS (SELECT COALESCE(array_agg(tagid), ARRAY[]::INTEGER[]) AS tags FROM blocktag WHERE userid = %(userid)s AND rating = 30),
                    bp AS (SELECT COALESCE(array_agg(tagid), ARRAY[]::INTEGER[]) AS tags FROM blocktag WHERE userid = %(userid)s AND rating = 40)
            """

            statement_where.append("""
                AND NOT submission_tags.tags && (SELECT tags FROM bg)
                AND (content.rating < 20 OR NOT submission_tags.tags && (SELECT tags FROM bm))
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

    if search.possible_includes:
        if search.find == "submit":
            statement_where.append("AND submission_tags.tags && %(possible_includes)s")
        else:
            statement_where.append("""
                AND EXISTS (
                    SELECT 0 FROM searchmap{find}
                    WHERE targetid = content.{select}
                        AND tagid = ANY (%(possible_includes)s)
                )
            """)

    if search.required_excludes:
        if search.find == "submit":
            statement_where.append("AND NOT submission_tags.tags && %(required_excludes)s")
        else:
            statement_where.append("""
                AND NOT EXISTS (
                    SELECT 0 FROM searchmap{find}
                    WHERE targetid = content.{select}
                        AND tagid = ANY (%(required_excludes)s)
                )
            """)

    if search.required_user_includes:
        statement_from.append("INNER JOIN login login_include ON content.userid = login_include.userid")
        statement_where.append("AND login_include.login_name = ANY (%(required_user_includes)s)")

    if search.required_user_excludes:
        statement_from.append("INNER JOIN login login_exclude ON content.userid = login_exclude.userid")
        statement_where.append("AND login_exclude.login_name != ALL (%(required_user_excludes)s)")

    def make_statement(statement_select, statement_additional_where, statement_order):
        return " ".join([
            statement_with,
            statement_select,
            " ".join(statement_from),
            " ".join(statement_where),
            statement_additional_where,
            " ".join(statement_group),
            statement_order,
        ]).format(
            table=table,
            find=search.find,
            select=select,
            subtype=subtype,
            title_field="char_name" if search.find == "char" else "title"
        )

    pagination_filter = (
        "AND content.{select} > %(backid)s" if backid else
        "AND content.{select} < %(nextid)s" if nextid else
        "")

    statement = make_statement(
        """
        SELECT
            content.{select}, content.{title_field} AS title, content.rating, content.unixtime, content.userid,
            content.settings, profile.username, {subtype} as subtype
        """,
        pagination_filter,
        "ORDER BY content.{{select}} {order} LIMIT %(limit)s".format(order="" if backid else "DESC"))

    all_names = (
        search.possible_includes |
        search.required_includes |
        search.required_excludes)

    tag_ids = searchtag.get_ids(all_names)

    def get_ids(names):
        return [tag_ids.get(name, -1) for name in names]

    params = {
        "possible_includes": get_ids(search.possible_includes),
        "required_includes": get_ids(search.required_includes),
        "required_excludes": get_ids(search.required_excludes),
        "required_user_includes": list(search.required_user_includes),
        "required_user_excludes": list(search.required_user_excludes),
        "type": type_letter,
        "userid": userid,
        "rating": rating,
        "ratings": list(search.ratings),
        "category": cat,
        "subcategory": subcat,
        "limit": limit,
        "count_limit": COUNT_LIMIT,
        "backid": backid,
        "nextid": nextid,
        "required_include_count": len(search.required_includes),
    }

    query = d.engine.execute(statement, params)

    ret = [{
        "contype": type_code,
        select: i[select],
        "title": i.title,
        "subtype": i.subtype,
        "rating": i.rating,
        "unixtime": i.unixtime,
        "userid": i.userid,
        "username": i.username,
        "settings": i.settings,
    } for i in query]

    if backid:
        # backid is the item after the last item (display-order-wise) on the
        # current page; the query will select items from there backwards,
        # including the current page. Subtract the number of items on the
        # current page to account for this, and add the maximum number of items
        # on a page to the count limit so it still comes out to the count limit
        # after subtracting if the limit is reached.
        back_count = d.engine.scalar(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", pagination_filter, " LIMIT %(count_limit)s + %(limit)s) _"),
            params) - len(ret)
    elif nextid:
        # nextid is the item before the first item (display-order-wise) on the
        # current page; the query will select items from there backwards, so
        # the current page is not included and no subtraction or modification
        # of the limit is necessary.
        back_count = d.engine.scalar(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", "AND content.{select} >= %(nextid)s", " LIMIT %(count_limit)s) _"),
            params)
    else:
        # The first page is being displayed; there’s nothing to go back to.
        back_count = 0

    if backid:
        # backid is the item after the last item (display-order-wise) on the
        # current page; the query will select items from there forwards, so the
        # current page is not included and no subtraction or modification of
        # the limit is necessary.
        next_count = d.engine.scalar(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", "AND content.{select} <= %(backid)s", " LIMIT %(count_limit)s) _"),
            params)

        # The ORDER BY is reversed when a backid is specified in order to LIMIT
        # to the nearest items with a larger backid rather than the smallest
        # ones, so reverse the items back to display order here.
        return list(reversed(ret)), next_count, back_count
    else:
        # This is either the first page or a page based on a nextid. In both
        # cases, the query will include the items in the current page in the
        # count, so subtract the number of items on the current page to give a
        # count of items after this page, and add the maximum number of items
        # on a page to the count limit so it still comes out to the count limit
        # after subtracting if the limit is reached.
        next_count = d.engine.scalar(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", pagination_filter, " LIMIT %(count_limit)s + %(limit)s) _"),
            params) - len(ret)

        return ret, next_count, back_count


def select(**kwargs):
    search = kwargs['search']
    results, next_count, back_count = _find_without_media(**kwargs)

    if search.find == 'submit':
        media.populate_with_submission_media(results)
    elif search.find == 'char':
        for r in results:
            r['sub_media'] = character.fake_media_items(
                r['charid'], r['userid'], d.get_sysname(r['username']), r['settings'])
    elif search.find == 'journal':
        media.populate_with_user_media(results)

    return results, next_count, back_count


def browse(userid, rating, limit, find, cat, backid, nextid):
    backid = d.get_int(backid)
    nextid = d.get_int(nextid)

    if find == "char":
        return character.select_list(userid, rating, limit, backid=backid, nextid=nextid)
    elif find == "journal":
        return journal.select_user_list(userid, rating, limit, backid=backid, nextid=nextid)
    else:
        return submission.select_list(userid, rating, limit, backid=backid, nextid=nextid,
                                      subcat=d.get_int(cat) if d.get_int(cat) in [1000, 2000, 3000] else None)
