"""Durable deterministic schedules in the canonical broker SQLite database.

No timer daemon, model call, command execution or authorization grant lives here.
The authenticated broker supplies registered actions and current-policy checks.
An operation callback must use the executor's independent current authorization
and idempotency boundary for effects. A lost callback result is never retried.
"""
from contextlib import contextmanager
import hashlib
import json
import math
import re
import time
import uuid

ID = re.compile(r'[a-z][a-z0-9-]{0,63}\Z')
MAX_SCHEDULES = 128
MAX_RUNS = 4096


class ScheduleError(ValueError):
    pass


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ScheduleError('schedule_id')
    return value


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 2**53 - 1:
        raise ScheduleError('schedule_timestamp')
    return value


class RunBudget:
    """Cooperative callback deadline/Stop; this is not a process sandbox.

    Registered callbacks must bound their own I/O/children. Committing package
    writes finish at the executor's safe boundary instead of being killed here.
    """
    def __init__(self, scheduler, operation_id, seconds):
        self.scheduler = scheduler
        self.operation_id = operation_id
        self.deadline = scheduler.monotonic() + seconds

    def canceled(self):
        row = self.scheduler.db.execute('SELECT cancel_requested FROM scheduler_runs WHERE operation_id=?', (self.operation_id,)).fetchone()
        return row is None or bool(row[0]) or self.scheduler.monotonic() >= self.deadline

    def check(self):
        if self.canceled():
            raise ScheduleError('schedule_canceled_or_deadline')


class Scheduler:
    def __init__(self, db, profile_id, *, clock=time.time, monotonic=time.monotonic):
        self.db = db
        self.profile = identifier(profile_id)
        self.clock = clock
        self.monotonic = monotonic
        with self._transaction():
            self.db.execute('CREATE TABLE IF NOT EXISTS scheduler_schema(version INTEGER NOT NULL)')
            versions = [r[0] for r in self.db.execute('SELECT version FROM scheduler_schema')]
            if versions and versions != [1]:
                raise ScheduleError('schedule_schema_version')
            if not versions:
                for statement in [
                    '''CREATE TABLE scheduler_jobs(profile_id TEXT NOT NULL,id TEXT NOT NULL,
                       action TEXT NOT NULL,interval INTEGER NOT NULL,next_due REAL NOT NULL,
                       missed TEXT NOT NULL,catchup INTEGER NOT NULL,seconds INTEGER NOT NULL,
                       remaining INTEGER NOT NULL,enabled INTEGER NOT NULL,
                       PRIMARY KEY(profile_id,id))''',
                    '''CREATE TABLE scheduler_runs(operation_id TEXT PRIMARY KEY,
                       profile_id TEXT NOT NULL,job_id TEXT NOT NULL,due REAL NOT NULL,
                       state TEXT NOT NULL,cancel_requested INTEGER NOT NULL DEFAULT 0,
                       result TEXT,UNIQUE(profile_id,job_id,due))''',
                    '''CREATE TABLE scheduler_health(profile_id TEXT NOT NULL,id TEXT NOT NULL,
                       fingerprint TEXT NOT NULL,actionable INTEGER NOT NULL,
                       PRIMARY KEY(profile_id,id))''',
                    'INSERT INTO scheduler_schema VALUES(1)',
                ]:
                    self.db.execute(statement)

    @contextmanager
    def _transaction(self):
        # Dispatch must commit preparation before an effect, so silently nesting
        # in the caller's transaction would violate its durability guarantee.
        if self.db.in_transaction:
            raise ScheduleError('schedule_outer_transaction')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def configure(self, job_id, action, *, interval, next_due, missed='skip',
                  catchup=0, seconds=10, max_runs=30):
        """Save disabled configuration; a separate current owner action enables.

        Absolute UTC intervals have no timezone/DST ambiguity. Calendar schedules
        and generic imported executable workflows are outside this first slice.
        """
        identifier(job_id)
        identifier(action)
        number(next_due)
        if type(interval) is not int or not 60 <= interval <= 365 * 86400:
            raise ScheduleError('schedule_interval')
        if missed not in ('skip', 'run-once') or type(catchup) is not int or not 0 <= catchup <= 3600 or (missed == 'run-once' and catchup == 0):
            raise ScheduleError('schedule_missed_policy')
        if type(seconds) is not int or not 1 <= seconds <= 300 or type(max_runs) is not int or not 1 <= max_runs <= 1000:
            raise ScheduleError('schedule_budget')
        with self._transaction():
            running = self.db.execute("SELECT 1 FROM scheduler_runs WHERE profile_id=? AND job_id=? AND state IN ('running','uncertain')", (self.profile, job_id)).fetchone()
            if running:
                raise ScheduleError('schedule_active_or_uncertain')
            exists = self.db.execute('SELECT 1 FROM scheduler_jobs WHERE profile_id=? AND id=?', (self.profile, job_id)).fetchone()
            if not exists and self.db.execute('SELECT count(*) FROM scheduler_jobs WHERE profile_id=?', (self.profile,)).fetchone()[0] >= MAX_SCHEDULES:
                raise ScheduleError('schedule_count_limit')
            self.db.execute('''INSERT INTO scheduler_jobs VALUES(?,?,?,?,?,?,?,?,?,0)
                ON CONFLICT(profile_id,id) DO UPDATE SET action=excluded.action,interval=excluded.interval,
                next_due=excluded.next_due,missed=excluded.missed,catchup=excluded.catchup,
                seconds=excluded.seconds,remaining=excluded.remaining,enabled=0''',
                (self.profile, job_id, action, interval, next_due, missed, catchup, seconds, max_runs))

    def enable(self, job_id, *, authorize):
        identifier(job_id)
        row = self.db.execute('SELECT action,remaining FROM scheduler_jobs WHERE profile_id=? AND id=?', (self.profile, job_id)).fetchone()
        if not row or row[1] <= 0 or not authorize(row[0]):
            raise ScheduleError('schedule_authorization_required')
        # Root standing-policy IPC must not run inside the SQLite write lock.
        # Dispatch independently checks current authorization again afterwards.
        with self._transaction():
            current = self.db.execute('SELECT action,remaining FROM scheduler_jobs WHERE profile_id=? AND id=?', (self.profile, job_id)).fetchone()
            if not current or tuple(current) != tuple(row):
                raise ScheduleError('schedule_changed_during_authorization')
            if self.db.execute("SELECT 1 FROM scheduler_runs WHERE profile_id=? AND state='uncertain'", (self.profile,)).fetchone():
                raise ScheduleError('schedule_uncertain')
            self.db.execute('UPDATE scheduler_jobs SET enabled=1 WHERE profile_id=? AND id=?', (self.profile, job_id))

    def cancel(self, job_id):
        with self._transaction():
            return self.cancel_in_transaction(job_id)

    def cancel_in_transaction(self, job_id):
        """Atomically disable a workflow together with its pending outbox."""
        if not self.db.in_transaction:
            raise ScheduleError('schedule_transaction_required')
        identifier(job_id)
        self.db.execute('UPDATE scheduler_jobs SET enabled=0 WHERE profile_id=? AND id=?', (self.profile, job_id))
        self.db.execute("UPDATE scheduler_runs SET cancel_requested=1 WHERE profile_id=? AND job_id=? AND state='running'", (self.profile, job_id))
        return {'dispatch_disabled': True, 'active_write_may_finish': True}

    def run_due(self, job_id, *, authorize, actions):
        identifier(job_id)
        now = number(self.clock())
        with self._transaction():
            row = self.db.execute('''SELECT action,interval,next_due,missed,catchup,seconds,remaining,enabled
                FROM scheduler_jobs WHERE profile_id=? AND id=?''', (self.profile, job_id)).fetchone()
            if not row:
                raise ScheduleError('schedule_missing')
            action, interval, due, missed, catchup, seconds, remaining, enabled = row
            if not enabled or remaining <= 0 or due > now:
                return {'state': 'idle'}
            if self.db.execute("SELECT 1 FROM scheduler_runs WHERE profile_id=? AND state IN ('running','uncertain')", (self.profile,)).fetchone():
                return {'state': 'busy'}
            if self.db.execute('SELECT count(*) FROM scheduler_runs WHERE profile_id=?', (self.profile,)).fetchone()[0] >= MAX_RUNS:
                raise ScheduleError('schedule_history_limit')
            if action not in actions or not callable(actions[action]):
                raise ScheduleError('schedule_action_unavailable')
            operation_id = uuid.uuid4().hex
            too_late = now - due > (catchup if missed == 'run-once' else 30)
            state = 'skipped' if too_late else 'running'
            self.db.execute('INSERT INTO scheduler_runs(operation_id,profile_id,job_id,due,state) VALUES(?,?,?,?,?)', (operation_id, self.profile, job_id, due, state))
            next_due = due + (int((now - due) // interval) + 1) * interval
            self.db.execute('UPDATE scheduler_jobs SET next_due=?,remaining=remaining-1,enabled=CASE WHEN remaining=1 THEN 0 ELSE enabled END WHERE profile_id=? AND id=?', (next_due, self.profile, job_id))
        if state == 'skipped':
            return {'state': state, 'operation_id': operation_id}
        # No database write transaction is held during policy/backend execution.
        budget = RunBudget(self, operation_id, seconds)
        try:
            if not authorize(action):
                return self._finish(operation_id, 'denied', {'reason': 'current_policy_denied'})
            budget.check()
            result = actions[action](operation_id, budget)
            # Only a bounded explicit backend status is recorded. No output,
            # transcript, credentials or arbitrary returned metadata is journaled.
            if not isinstance(result, dict) or set(result) != {'verified'} or type(result['verified']) is not bool:
                raise ScheduleError('schedule_result_unverified')
            if not result['verified']:
                raise ScheduleError('schedule_result_unverified')
            return self._finish(operation_id, 'completed', result)
        except BaseException:
            # Effect may already have happened. Never convert a callback failure,
            # deadline or cancellation into permission to replay its side effects.
            self._finish(operation_id, 'uncertain', {'reason': 'callback_or_result_uncertain'})
            raise

    def _finish(self, operation_id, state, result):
        with self._transaction():
            self.db.execute("UPDATE scheduler_runs SET state=?,result=? WHERE operation_id=? AND profile_id=? AND state='running'", (state, json.dumps(result, separators=(',', ':')), operation_id, self.profile))
            if state in ('uncertain', 'denied'):
                self.db.execute('UPDATE scheduler_jobs SET enabled=0 WHERE profile_id=?', (self.profile,))
        return {'state': state, 'operation_id': operation_id}

    def recover(self):
        """Call only after proving the old broker/writer is gone, never on attach."""
        with self._transaction():
            cursor = self.db.execute("UPDATE scheduler_runs SET state='uncertain',result=? WHERE profile_id=? AND state='running'", ('{"reason":"broker_interrupted"}', self.profile))
            if cursor.rowcount:
                self.db.execute('UPDATE scheduler_jobs SET enabled=0 WHERE profile_id=?', (self.profile,))
            return cursor.rowcount

    def history(self):
        cursor = self.db.execute('''SELECT operation_id,job_id,due,state,cancel_requested,result
            FROM scheduler_runs WHERE profile_id=? ORDER BY due,operation_id''', (self.profile,))
        return [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]

    def observe(self, probe_id, *, state, actionable):
        """Persist a bounded deterministic condition; notify once on bad changes.

        Callers pass stable condition labels (healthy/low/failed), not varying
        free-byte samples or secret-bearing service output. Recovery is inspectable
        and quiet; no notification/model call on unchanged/healthy observations.
        """
        with self._transaction():
            return self.observe_in_transaction(probe_id, state=state, actionable=actionable)

    def observe_in_transaction(self, probe_id, *, state, actionable):
        """Share one canonical commit with observation/outbox records."""
        if not self.db.in_transaction:
            raise ScheduleError('schedule_transaction_required')
        identifier(probe_id)
        identifier(state)
        if type(actionable) is not bool:
            raise ScheduleError('schedule_health_state')
        fingerprint = hashlib.sha256(state.encode()).hexdigest()
        old = self.db.execute('SELECT fingerprint,actionable FROM scheduler_health WHERE profile_id=? AND id=?', (self.profile, probe_id)).fetchone()
        changed = old is None or tuple(old) != (fingerprint, int(actionable))
        self.db.execute('INSERT OR REPLACE INTO scheduler_health VALUES(?,?,?,?)', (self.profile, probe_id, fingerprint, int(actionable)))
        return {'notify': actionable and changed, 'actionable': actionable, 'changed': changed}

    def export(self):
        cursor = self.db.execute('''SELECT id,action,interval,next_due,missed,catchup,seconds,remaining
            FROM scheduler_jobs WHERE profile_id=? ORDER BY id''', (self.profile,))
        return {'scheduler_version': 1, 'timezone': 'UTC', 'jobs': [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]}

    def import_disabled(self, document):
        """Import configuration only: never jobs/results/grants or enabled state."""
        if not isinstance(document, dict) or set(document) != {'scheduler_version', 'timezone', 'jobs'} or type(document['scheduler_version']) is not int or document['scheduler_version'] != 1 or document['timezone'] != 'UTC':
            raise ScheduleError('schedule_import_schema')
        jobs = document['jobs']
        if not isinstance(jobs, list) or len(jobs) > MAX_SCHEDULES:
            raise ScheduleError('schedule_import_limit')
        ids = set()
        # Validate the complete candidate using a temporary savepoint is unsafe
        # with durable dispatch; imported configurations are staged by broker.
        # Reuse a private in-memory database for full validation before any write.
        import sqlite3
        staged_db = sqlite3.connect(':memory:', isolation_level=None)
        try:
            staged = Scheduler(staged_db, 'staging')
            for job in jobs:
                if not isinstance(job, dict) or set(job) != {'id', 'action', 'interval', 'next_due', 'missed', 'catchup', 'seconds', 'remaining'}:
                    raise ScheduleError('schedule_import_fields')
                key = identifier(job['id'])
                if key in ids:
                    raise ScheduleError('schedule_import_duplicate')
                ids.add(key)
                if type(job['remaining']) is not int or not 0 <= job['remaining'] <= 1000:
                    raise ScheduleError('schedule_budget')
                staged.configure(key, job['action'], interval=job['interval'], next_due=job['next_due'], missed=job['missed'], catchup=job['catchup'], seconds=job['seconds'], max_runs=max(1, job['remaining']))
        finally:
            staged_db.close()
        # Import is creation-only. Existing active histories must never be reset.
        with self._transaction():
            if self.db.execute('SELECT 1 FROM scheduler_jobs WHERE profile_id=?', (self.profile,)).fetchone():
                raise ScheduleError('schedule_import_nonempty')
            for job in jobs:
                self.db.execute('INSERT INTO scheduler_jobs VALUES(?,?,?,?,?,?,?,?,?,0)', (self.profile, job['id'], job['action'], job['interval'], job['next_due'], job['missed'], job['catchup'], job['seconds'], job['remaining']))
