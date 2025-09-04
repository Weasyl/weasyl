import arrow
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import aliased, contains_eager, joinedload
import sqlalchemy as sa
import web

from libweasyl.models.content import Report, ReportComment
from libweasyl.models.users import Login
from libweasyl import constants, staff
from weasyl.error import WeasylError
from weasyl.forms import parse_sysname
from weasyl import macro as m, define as d, media, note


_CONTENT = 2000


def _convert_violation(target):
    violation = [i[2] for i in m.MACRO_REPORT_VIOLATION if i[0] == target]
    return violation[0] if violation else 'Unknown'


def _dict_of_targetid(submitid, charid, journalid):
    """
    Given a target of some type, return a dictionary indicating what the 'some
    type' is. The dictionary's key will be the appropriate column on the Report
    model.
    """
    if submitid:
        return {'target_sub': submitid}
    elif charid:
        return {'target_char': charid}
    elif journalid:
        return {'target_journal': journalid}
    else:
        raise ValueError('no ID given')


# form
#   submitid     violation
#   charid       content
#   journalid

def create(userid, form):
    form.submitid = d.get_int(form.submitid)
    form.charid = d.get_int(form.charid)
    form.journalid = d.get_int(form.journalid)
    form.violation = d.get_int(form.violation)
    form.content = form.content.strip()[:_CONTENT]

    # get the violation type from allowed types
    try:
        vtype = next(x for x in m.MACRO_REPORT_VIOLATION if x[0] == form.violation)
    except StopIteration:
        raise WeasylError("Unexpected")

    if not form.submitid and not form.charid and not form.journalid:
        raise WeasylError("Unexpected")
    elif form.violation == 0:
        if userid not in staff.MODS:
            raise WeasylError("Unexpected")
    elif (form.submitid or form.charid) and not 2000 <= form.violation < 3000:
        raise WeasylError("Unexpected")
    elif form.journalid and not 3000 <= form.violation < 4000:
        raise WeasylError("Unexpected")
    elif vtype[3] and not form.content:
        raise WeasylError("ReportCommentRequired")

    is_hidden = d.engine.scalar(
        "SELECT hidden FROM %s WHERE %s = %i" % (
            ("submission", "submitid", form.submitid) if form.submitid else
            ("character", "charid", form.charid) if form.charid else
            ("journal", "journalid", form.journalid)
        )
    )

    if is_hidden is None or (form.violation != 0 and is_hidden):
        raise WeasylError("TargetRecordMissing")

    now = arrow.get()
    target_dict = _dict_of_targetid(form.submitid, form.charid, form.journalid)
    report = Report.query.filter_by(is_closed=False, **target_dict).first()
    if report is None:
        if form.violation == 0:
            raise WeasylError("Unexpected")
        urgency = vtype[1]
        report = Report(urgency=urgency, opened_at=now, **target_dict)
        Report.dbsession.add(report)

    Report.dbsession.add(ReportComment(
        report=report, violation=form.violation, userid=userid, unixtime=now, content=form.content))

    Report.dbsession.flush()


_report_types = [
    '_target_sub',
    '_target_char',
    '_target_journal',
]


def select_list(userid, form):
    # Find the unique violation types and the number of reporters. This will be
    # joined against the Report model to get the violations/reporters for each
    # selected report.
    subq = (
        ReportComment.dbsession.query(
            ReportComment.reportid,
            sa.func.count(),
            sa.type_coerce(
                sa.func.array_agg(ReportComment.violation.distinct()),
                ARRAY(sa.Integer, as_tuple=True)).label('violations'))
        .filter(ReportComment.violation != 0)
        .group_by(ReportComment.reportid)
        .subquery())

    # Find reports, joining against the aforementioned subquery, and eager-load
    # the reports' owners.
    q = (
        Report.dbsession.query(Report, subq)
        .options(joinedload(Report.owner))
        .join(subq, Report.reportid == subq.c.reportid)
        .reset_joinpoint())

    # For each type of report, eagerly load the content reported and the
    # content's owner. Also, keep track of the Login model aliases used for each
    # report type so they can be filtered against later.
    login_aliases = []
    for column_name in _report_types:
        login_alias = aliased(Login)
        login_aliases.append(login_alias)
        q = (
            q
            .outerjoin(getattr(Report, column_name))
            .outerjoin(login_alias)
            .options(contains_eager(column_name + '.owner', alias=login_alias))
            .reset_joinpoint())

    # Filter by report status. form.status can also be 'all', in which case no
    # filter is applied.
    if form.status == 'closed':
        q = q.filter_by(is_closed=True)
    elif form.status == 'open':
        q = q.filter_by(is_closed=False)

    # If filtering by the report's content's owner, iterate over the previously
    # collected Login model aliases to compare against Login.login_name.
    if form.submitter:
        submitter = parse_sysname(form.submitter)
        q = q.filter(sa.or_(login.login_name == submitter for login in login_aliases))

    # If filtering by violation type, see if the violation is in the array
    # aggregate of unique violations for this report.
    if form.violation and form.violation != '-1':
        q = q.filter(sa.literal(int(form.violation)) == sa.func.any(subq.c.violations))

    q = q.order_by(Report.opened_at.desc())
    return [(report, report_count, list(map(_convert_violation, violations)))
            for report, _, report_count, violations in q.all()]


def select_view(userid, *, reportid):
    report = (
        Report.query
        .options(joinedload('comments', innerjoin=True).joinedload('poster', innerjoin=True))
        .get(reportid))

    if report is None:
        raise HTTPNotFound()

    report.old_style_comments = [
        {
            'userid': c.userid,
            'username': c.poster.profile.username,
            'unixtime': c.unixtime,
            'content': c.content,
            'violation': _convert_violation(c.violation),
        } for c in report.comments]
    media.populate_with_user_media(report.old_style_comments)
    report.old_style_comments.sort(key=lambda c: c['unixtime'])
    return report


_closure_actions = {
    'no_action_taken': constants.ReportClosureReason.no_action_taken,
    'action_taken': constants.ReportClosureReason.action_taken,
    'invalid': constants.ReportClosureReason.invalid,
}


def close(userid, form):
    if userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    root_report = Report.query.get(int(form.reportid))
    if root_report is None or root_report.is_closed:
        return

    if 'close_all_user_reports' in form:
        # If we're closing all of the reports opened against a particular content
        # owner, do the same thing as in the select_list function and collect Login
        # aliases so that filtering can be done by Login.login_name.
        q = Report.query
        login_aliases = []
        for column_name in _report_types:
            login_alias = aliased(Login)
            login_aliases.append(login_alias)
            q = (
                q
                .outerjoin(getattr(Report, column_name))
                .outerjoin(login_alias)
                .reset_joinpoint())

        q = (
            q
            .filter_by(is_closed=False)
            .filter(sa.or_(login.login_name == root_report.target.owner.login_name
                           for login in login_aliases)))
        reports = q.all()

    else:
        reports = [root_report]

    for report in reports:
        if report.is_closed:
            raise RuntimeError("a closed report shouldn't have gotten this far")
        report.closerid = userid
        report.settings.mutable_settings.clear()
        if 'assign' in form:
            report.is_under_review = True
        elif 'unassign' in form:
            report.closerid = None
        else:
            report.closed_at = arrow.get()
            report.closure_explanation = form.explanation
            report.closure_reason = _closure_actions[form.action]

    Report.dbsession.flush()
    if form.action == 'action_taken':
        # TODO(hyena): Remove this dependency on web.py's Storage objects.
        note_form = web.Storage()
        note_form.title = form.note_title
        note_form.content = form.user_note
        note_form.recipient = root_report.target.owner.login_name
        note_form.mod_copy = True
        note_form.staff_note = form.explanation
        note.send(userid, note_form)


def check(submitid=None, charid=None, journalid=None):
    return bool(
        Report.query
        .filter_by(is_closed=False, **_dict_of_targetid(submitid, charid, journalid))
        .count())


def select_reported_list(userid):
    q = (
        Report.query
        .join(ReportComment)
        .options(contains_eager(Report.comments))
        .options(joinedload('_target_sub'))
        .options(joinedload('_target_char'))
        .options(joinedload('_target_journal'))
        .filter(ReportComment.violation != 0)
        .filter_by(userid=userid))

    reports = q.all()
    for report in reports:
        report.latest_report = max(c.unixtime for c in report.comments)

    reports.sort(key=lambda r: r.latest_report, reverse=True)
    return reports
