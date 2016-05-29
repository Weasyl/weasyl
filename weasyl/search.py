import re
import web

from libweasyl.ratings import GENERAL, MODERATE, MATURE, EXPLICIT

from weasyl import character, journal, media, submission
from weasyl import define as d


_query_find_modifiers = {
    "#submission": "submit",
    "#character": "char",
    "#journal": "journal",
    "#user": "user",
}

_query_rating_modifiers = {
    "#general": GENERAL.code,
    "#moderate": MODERATE.code,
    "#mature": MATURE.code,
    "#explicit": EXPLICIT.code,
}

_query_delimiter = re.compile(r"[\s,;]+")

_table_information = {
    "submit": (10, "s", "submission", "submitid", "subtype"),
    # The subtype values for characters and journals are fake
    # and set to permit us to reuse the same sql query.
    "char": (20, "f", "character", "charid", 3999),
    "journal": (30, "j", "journal", "journalid", 3999),
}

_rating_codes = {
    "g": GENERAL.code,
    "m": MODERATE.code,
    "a": MATURE.code,
    "p": EXPLICIT.code,
}


class Query:
    _find = None

    def __init__(self):
        self.possible_includes = set()
        self.required_includes = set()
        self.required_excludes = set()
        self.required_user_includes = set()
        self.required_user_excludes = set()
        self.ratings = set()

    @property
    def find(self):
        return self._find or "submit"

    def to_dict(self):
        return {
            "possible_includes": list(self.possible_includes - (self.required_includes | self.required_excludes)),
            "required_includes": list(self.required_includes),
            "required_excludes": list(self.required_excludes - self.required_includes),
            "required_user_includes": list(self.required_user_includes),
            "required_user_excludes": list(self.required_user_excludes),
        }

    def add_criterion(self, criterion):
        def add_nonempty(s, item):
            if item:
                s.add(item)

        find_modifier = _query_find_modifiers.get(criterion)

        if find_modifier:
            self._find = find_modifier
            return

        rating_modifier = _query_rating_modifiers.get(criterion)

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

    @classmethod
    def parse(cls, query_string):
        """
        Parses a search query string into collections of tags and users.
        """
        query = Query()

        for criterion in _query_delimiter.split(query_string):
            if criterion:
                query.add_criterion(criterion)

        return query


def select(userid, rating, limit,
           q, find, within, rated, cat, subcat, backid, nextid):
    search = Query.parse(q)
    search.ratings.update([_rating_codes[r] for r in rated])

    if not search._find:
        search._find = find

    if search.find == "user":
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
        return ret, 0, 0

    type_code, type_letter, table, select, subtype = _table_information[search.find]
    search_dict = search.to_dict()

    if not any(search_dict.values()):
        raise web.seeother("/search?type=" + search.find)

    # Begin statement
    statement_from = ["FROM {table} content INNER JOIN profile ON content.userid = profile.userid"]
    statement_where = ["WHERE content.rating <= %(rating)s AND content.settings !~ '[fhm]'"]
    statement_group = []

    if search.required_includes:
        statement_from.append("INNER JOIN searchmap{find} ON targetid = content.{select}")
        statement_from.append("INNER JOIN searchtag ON searchmap{find}.tagid = searchtag.tagid")
        statement_where.append("AND searchtag.title = ANY (%(required_includes)s)")
        statement_group.append(
            "GROUP BY content.{select}, profile.username HAVING COUNT(searchtag.tagid) = %(required_include_count)s")

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
    if userid and search.ratings:
        statement_where.append("AND content.rating = ANY (%(ratings)s)")

    # Blocked tags and ignored users
    if userid:
        statement_where.append("""
            AND NOT EXISTS (
                SELECT 0 FROM ignoreuser
                WHERE userid = %(userid)s
                    AND otherid = content.userid)
            AND NOT EXISTS (
                SELECT 0 FROM searchmap{find}
                WHERE targetid = content.{select}
                    AND tagid IN (SELECT tagid FROM blocktag WHERE userid = %(userid)s AND rating <= content.rating))
        """)

    if search.possible_includes:
        statement_where.append("""
            AND EXISTS (
                SELECT 0 FROM searchmap{find}
                WHERE targetid = content.{select}
                    AND tagid IN (SELECT tagid FROM searchtag WHERE title = ANY (%(possible_includes)s))
            )
        """)

    if search.required_excludes:
        statement_where.append("""
            AND NOT EXISTS (
                SELECT 0 FROM searchmap{find}
                WHERE targetid = content.{select}
                    AND tagid IN (
                        SELECT tagid FROM searchtag
                        WHERE title = ANY (%(required_excludes)s)
                    )
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

    params = dict(
        search_dict,
        type=type_letter,
        userid=userid,
        rating=rating,
        ratings=list(search.ratings),
        category=cat,
        subcategory=subcat,
        limit=limit,
        backid=backid,
        nextid=nextid,
        required_include_count=len(search.required_includes))

    query = d.engine.execute(statement, **params)

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

    if search.find == "submit":
        media.populate_with_submission_media(ret)
    elif search.find == "char":
        for r in ret:
            r["sub_media"] = character.fake_media_items(
                r["charid"], r["userid"], d.get_sysname(r["username"]), r["settings"])
    elif search.find == "journal":
        media.populate_with_user_media(ret)

    if backid:
        back_count = d.engine.execute(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", pagination_filter, ") _"), **params).scalar() - len(ret)
    elif nextid:
        back_count = (d.engine.execute(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", "AND content.{select} >= %(nextid)s", ") _"),
            **params).scalar())
    else:
        back_count = 0

    if backid:
        next_count = (d.engine.execute(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", "AND content.{select} <= %(backid)s", ") _"),
            **params).scalar())
        return list(reversed(ret)), next_count, back_count
    else:
        next_count = d.engine.execute(
            make_statement("SELECT COUNT(*) FROM (SELECT 1", pagination_filter, ") _"), **params).scalar() - len(ret)
        return ret, next_count, back_count


# form
#   find    backid
#   cat     nextid

def browse(userid, rating, limit, form, find=None, config=None):
    backid = d.get_int(form.backid)
    nextid = d.get_int(form.nextid)

    if find:
        form.find = find

    if form.find == "char":
        query = character.select_list(userid, rating, limit, backid=backid, nextid=nextid, config=config)
    elif form.find == "journal":
        query = journal.select_user_list(userid, rating, limit, backid=backid, nextid=nextid, config=config)
    else:
        query = submission.select_list(userid, rating, limit, backid=backid, nextid=nextid,
                                       subcat=d.get_int(form.cat) if d.get_int(form.cat) in [1000, 2000, 3000] else None,
                                       config=config)

    if query and not backid:
        backid = query[0][form.find + "id"]
    if query and not nextid:
        nextid = query[-1][form.find + "id"]

    return query
