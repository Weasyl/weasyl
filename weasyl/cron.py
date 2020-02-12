from __future__ import absolute_import

import arrow
from twisted.python import log

from weasyl.define import engine, get_time
from weasyl import index, submission


def run_periodic_tasks():
    # An arrow object representing the current UTC time
    now = arrow.utcnow()

    # An integer representing the current unixtime (with an offset applied sourced from libweasyl.legacy)
    time_now = get_time()

    db = engine.connect()
    with db.begin():
        locked = db.scalar("SELECT pg_try_advisory_xact_lock(0)")
        if not locked:
            return
        last_run = arrow.get(db.scalar("SELECT last_run FROM cron_runs"))
        if not last_run or now < last_run.replace(second=59):
            return

        # Recache the latest submissions
        # Every 2 minutes
        if now.minute % 2 == 0:
            index.recent_submissions.refresh()
            log.msg('refreshed recent submissions')

        # Recalculate recently popular submissions
        # Every 10 minutes
        if now.minute % 10 == 0:
            submission.select_recently_popular.refresh()
            log.msg('refreshed recently popular submissions')

        # Delete all records from views table
        # Every 15 minutes
        if now.minute % 15 == 0:
            db.execute("DELETE FROM views")
            log.msg('cleared views')

        # Daily at 0:00
        if now.hour == 0 and now.minute == 0:
            # Delete password resets older than one day
            db.execute("DELETE FROM forgotpassword WHERE set_time < %(expiry)s", expiry=time_now - 86400)
            log.msg('cleared old forgotten password requests')

            # Delete email reset requests older than two days
            db.execute("""
                DELETE FROM emailverify
                WHERE createtimestamp < (NOW() - INTERVAL '2 days')
            """)
            log.msg('cleared stale email change records')

            # Purge stale logincreate records older than two days
            db.execute("""
                DELETE FROM logincreate
                WHERE unixtime < %(time)s
            """, time=time_now - (86400 * 2))
            log.msg('cleared stale account creation records')

        db.execute("UPDATE cron_runs SET last_run = %(now)s", now=now.naive)
