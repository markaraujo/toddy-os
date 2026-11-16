"""Durable per-profile task/operation journal, independent of optional chat history.

The caller authenticates the session peer and validates tool-specific arguments.
Only trusted adapters supply effects/verification; model output is never evidence.
No prompt, tool arguments/results, credential or exception text is persisted.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import time
import uuid

try:
    from .protocol import strict_json
except ImportError:
    from protocol import strict_json


class TaskError(ValueError):
    pass


def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', value):
        raise TaskError('invalid_identifier')
    return value


def _hash(value):
    try:
        data = json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':'), allow_nan=False).encode()
        if len(data) > 65536:
            raise TaskError('input_limit')
        strict_json(data)
        return hashlib.sha256(data).hexdigest()
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise TaskError('invalid_input') from None


class TaskJournal:
    TERMINAL = {'completed', 'failed', 'canceled'}
    BOUNDARIES = {'interruptible', 'package', 'boot'}

    def __init__(self, profiles, *, clock=time.time, byte_limit=64 * 1024 * 1024,
                 free_reserve=2 * 1024 * 1024):
        self.profiles = profiles
        self.clock = clock
        self.byte_limit = byte_limit
        self.free_reserve = free_reserve
        self.lock_path = profiles.directory / 'task-dispatch.lock'
        fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600):
                raise TaskError('unsafe_task_lock')
        finally:
            os.close(fd)
        with self.profiles._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS tasks(
                    id TEXT PRIMARY KEY,request_id TEXT UNIQUE NOT NULL,input_hash TEXT NOT NULL,
                    profile_revision TEXT NOT NULL REFERENCES profile_revisions(revision),
                    state TEXT NOT NULL,sequence INTEGER NOT NULL,cancel_requested INTEGER NOT NULL,
                    result_uncertain INTEGER NOT NULL,code TEXT NOT NULL,operation_id TEXT,
                    deadline REAL NOT NULL,tool_calls INTEGER NOT NULL,max_tool_calls INTEGER NOT NULL,
                    created REAL NOT NULL,updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS task_operations(
                    id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(id),kind TEXT NOT NULL,
                    input_hash TEXT NOT NULL,state TEXT NOT NULL,boundary TEXT NOT NULL,
                    verified INTEGER NOT NULL,created REAL NOT NULL,updated REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS task_operations_task ON task_operations(task_id);
            ''')

    @contextmanager
    def exclusive(self):
        with open(self.lock_path, 'r+b') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise TaskError('task_dispatch_busy') from None
            yield

    def _capacity(self, additional=32768):
        # Includes canonical DB, rollback/WAL and shared profile/memory storage.
        # Reserved free space is never a success guarantee; failed COMMIT prevents
        # dispatch. No destructive pruning/VACUUM occurs during active work.
        used = sum(path.stat().st_size for path in self.profiles.directory.glob('state.sqlite*')
                   if path.is_file())
        if used + additional > self.byte_limit:
            raise TaskError('task_storage_full')
        if shutil.disk_usage(self.profiles.directory).free < self.free_reserve + additional:
            raise TaskError('task_disk_full')

    @staticmethod
    def _row(db, task_id):
        row = db.execute('SELECT * FROM tasks WHERE id=?', (_id(task_id),)).fetchone()
        if row is None:
            raise TaskError('unknown_task')
        return row

    @staticmethod
    def _view(row):
        # All strings here are generated IDs or fixed codes, never model text.
        return {'version': 1, 'task_id': row['id'], 'profile_revision': row['profile_revision'],
                'sequence': row['sequence'], 'state': row['state'],
                'cancel_requested': bool(row['cancel_requested']),
                'result_uncertain': bool(row['result_uncertain']), 'summary': row['code'],
                'operation_id': row['operation_id']}

    def inspect(self, task_id):
        with self.profiles._db() as db:
            return self._view(self._row(db, task_id))

    def lookup_request(self,request_id):
        """Read-only acceptance metadata; never resubmit or return prompt/hash bytes."""
        _id(request_id)
        with self.profiles._db() as db:
            row=db.execute('SELECT * FROM tasks WHERE request_id=?',(request_id,)).fetchone()
            return self._view(row) if row is not None else None

    def list_metadata(self,before_row=0):
        """Bounded metadata-only paging; task history does not imply text retention."""
        if type(before_row) is not int or not 0<=before_row<=2**53-1:
            raise TaskError('invalid_task_cursor')
        with self.profiles._db() as db:
            if before_row:
                rows=db.execute('SELECT rowid AS cursor,* FROM tasks WHERE rowid<? ORDER BY rowid DESC LIMIT 33',
                                (before_row,)).fetchall()
            else:
                rows=db.execute('SELECT rowid AS cursor,* FROM tasks ORDER BY rowid DESC LIMIT 33').fetchall()
        selected=rows[:32]
        return {'version':1,'profile_id':self.profiles.profile_id,
                'tasks':[{**self._view(row),'request_id':row['request_id']} for row in selected],
                'next_cursor':selected[-1]['cursor'] if len(rows)>32 else 0,'complete':len(rows)<=32}

    def remaining_seconds(self, task_id):
        with self.profiles._db() as db:
            return max(0.0, self._row(db, task_id)['deadline'] - self.clock())

    @staticmethod
    def _request_digest(request_id, expected_revision, input_text, request_metadata):
        _id(request_id)
        if not isinstance(input_text, str):
            raise TaskError('invalid_task_text')
        try:
            if not 0 < len(input_text.encode()) <= 16384:
                raise TaskError('task_text_limit')
        except UnicodeError:
            raise TaskError('invalid_task_text') from None
        return _hash({'revision': expected_revision, 'input': input_text, 'metadata': request_metadata})

    def accepted_request(self, request_id, expected_revision, input_text, *, request_metadata=None):
        """Pure exact-hash lookup. No insertion, activation, dispatch or session grant."""
        digest = self._request_digest(request_id, expected_revision, input_text, request_metadata)
        with self.profiles._db() as db:
            row = db.execute('SELECT * FROM tasks WHERE request_id=?', (request_id,)).fetchone()
            if row is None:
                return None
            if row['input_hash'] != digest:
                raise TaskError('request_identity_conflict')
            return self._view(row)

    def submit(self, request_id, expected_revision, input_text, *, request_metadata=None):
        """Persist request/revision binding before any worker/provider dispatch.

        An already accepted same request returns the same task even after profile
        selection changes. An unknown/stale client request is never auto-retried
        by this API. Prompt bytes are hashed, not persisted as safety metadata.
        """
        digest = self._request_digest(request_id, expected_revision, input_text, request_metadata)
        old = self.accepted_request(request_id, expected_revision, input_text, request_metadata=request_metadata)
        if old:
            return old
        files = self.profiles.snapshot(expected_revision)
        config = strict_json(files['config.json'])
        with self.profiles._transaction() as db:
            old = db.execute('SELECT * FROM tasks WHERE request_id=?', (request_id,)).fetchone()
            if old:
                if old['input_hash'] != digest:
                    raise TaskError('request_identity_conflict')
                return self._view(old)
            if self.profiles._current(db) != expected_revision:
                raise TaskError('stale_profile_revision')
            self._capacity()
            task_id = 'task-' + uuid.uuid4().hex
            now = self.clock()
            db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,1,0,0,?,NULL,?,0,?,?,?)',
                       (task_id, request_id, digest, expected_revision, 'queued', 'accepted',
                        now + config['budgets']['task_deadline_seconds'],
                        config['budgets']['max_tool_calls'], now, now))
            # Atomic with acceptance; no race with profile apply or task dispatch.
            db.execute('INSERT INTO task_profiles VALUES(?,?,?,?)',
                       (task_id, self.profiles.profile_id, expected_revision, now))
            return self._view(self._row(db, task_id))

    def start(self, task_id):
        with self.profiles._transaction() as db:
            row = self._row(db, task_id)
            if row['state'] != 'queued' or row['cancel_requested']:
                raise TaskError('task_not_dispatchable')
            self._capacity()
            if self.clock() >= row['deadline']:
                raise TaskError('task_deadline')
            db.execute("UPDATE tasks SET state='planning',code='planning',sequence=sequence+1,updated=? WHERE id=?",
                       (self.clock(), task_id))
        return self.inspect(task_id)

    def cancel(self, task_id):
        """Durable Stop is accepted even with full journal/no current root grant.

        Interruptible work must observe cancel_requested via a managed adapter.
        Package/boot commits report the active operation until its safe boundary;
        this function never SIGKILLs an unknown/executor-owned writer.
        """
        with self.profiles._transaction() as db:
            row = self._row(db, task_id)
            if row['state'] in self.TERMINAL:
                return self._view(row)
            state = 'running' if row['state'] == 'running' else 'canceled'
            code = 'stop_pending_safe_boundary' if state == 'running' else 'canceled_before_dispatch'
            # Uncertain work cannot be made terminal merely by clicking Stop.
            if row['result_uncertain']:
                state, code = 'waiting', 'reconciliation_required'
            db.execute('UPDATE tasks SET state=?,code=?,cancel_requested=1,sequence=sequence+1,updated=? WHERE id=?',
                       (state, code, self.clock(), task_id))
        return self.inspect(task_id)

    def prepare_operation(self, task_id, operation_id, kind, arguments, *, boundary='interruptible'):
        _id(operation_id); _id(kind)
        if boundary not in self.BOUNDARIES:
            raise TaskError('invalid_commit_boundary')
        digest = _hash({'kind': kind, 'arguments': arguments, 'boundary': boundary})
        with self.profiles._transaction() as db:
            row = self._row(db, task_id)
            old = db.execute('SELECT * FROM task_operations WHERE id=?', (operation_id,)).fetchone()
            if old:
                if old['task_id'] != task_id or old['input_hash'] != digest:
                    raise TaskError('operation_identity_conflict')
                return dict(old)
            if row['state'] not in {'planning', 'running'} or row['cancel_requested'] or row['result_uncertain']:
                raise TaskError('task_not_dispatchable')
            if db.execute("SELECT 1 FROM task_operations WHERE task_id=? AND state IN ('prepared','running','uncertain')", (task_id,)).fetchone():
                raise TaskError('operation_pending')
            if self.clock() >= row['deadline']:
                raise TaskError('task_deadline')
            if row['tool_calls'] >= row['max_tool_calls']:
                raise TaskError('task_tool_limit')
            self._capacity()
            now = self.clock()
            db.execute('INSERT INTO task_operations VALUES(?,?,?,?,?,?,0,?,?)',
                       (operation_id, task_id, kind, digest, 'prepared', boundary, now, now))
            db.execute("UPDATE tasks SET operation_id=?,tool_calls=tool_calls+1,sequence=sequence+1,updated=? WHERE id=?",
                       (operation_id, now, task_id))
            return dict(db.execute('SELECT * FROM task_operations WHERE id=?', (operation_id,)).fetchone())

    def operation(self, task_id, operation_id):
        with self.profiles._db() as db:
            self._row(db, task_id)
            row = db.execute('SELECT * FROM task_operations WHERE id=? AND task_id=?',
                             (_id(operation_id), task_id)).fetchone()
            if row is None:
                raise TaskError('unknown_operation')
            return dict(row)

    def run_operation(self, task_id, operation_id, kind, arguments, apply, verify,
                      *, boundary='interruptible'):
        """One serialized effect; callbacks trusted, exceptions never auto-retried.

        Repeating an accepted operation only returns its existing journal record.
        verify receives ephemeral adapter output and must establish a real known
        postcondition. Success requires literal True; exception text is discarded.
        """
        with self.exclusive():
            operation = self.prepare_operation(task_id, operation_id, kind, arguments, boundary=boundary)
            if operation['state'] != 'prepared':
                return operation
            with self.profiles._transaction() as db:
                row = self._row(db, task_id)
                if row['cancel_requested'] or row['state'] not in {'planning', 'running'} or row['result_uncertain']:
                    raise TaskError('task_not_dispatchable')
                if self.clock() >= row['deadline']:
                    raise TaskError('task_deadline')
                self._capacity()
                now = self.clock()
                db.execute("UPDATE task_operations SET state='running',updated=? WHERE id=?", (now, operation_id))
                db.execute("UPDATE tasks SET state='running',code='operation_running',sequence=sequence+1,updated=? WHERE id=?", (now, task_id))
            try:
                result = apply(operation_id, kind, arguments)
                verified = verify(result) is True
            except BaseException:
                self._operation_result(task_id, operation_id, 'uncertain', False)
                raise TaskError('operation_uncertain') from None
            self._operation_result(task_id, operation_id, 'completed' if verified else 'uncertain', verified)
            if not verified:
                raise TaskError('operation_uncertain')
            return self.operation(task_id, operation_id)

    def _operation_result(self, task_id, operation_id, state, verified):
        with self.profiles._transaction() as db:
            row = self._row(db, task_id)
            now = self.clock()
            db.execute('UPDATE task_operations SET state=?,verified=?,updated=? WHERE id=? AND task_id=?',
                       (state, int(verified), now, operation_id, task_id))
            uncertain = state == 'uncertain'
            task_state = 'waiting' if uncertain else 'canceled' if row['cancel_requested'] else 'planning'
            code = 'reconciliation_required' if uncertain else 'stopped_after_verified_effect' if row['cancel_requested'] else 'operation_verified'
            db.execute('UPDATE tasks SET state=?,code=?,result_uncertain=?,sequence=sequence+1,updated=? WHERE id=?',
                       (task_state, code, int(uncertain), now, task_id))

    def hold(self, task_id):
        """Visible pre-dispatch failure; never hides a running/uncertain effect."""
        with self.profiles._transaction() as db:
            row = self._row(db, task_id)
            if row['state'] in self.TERMINAL or row['state'] == 'running' or row['result_uncertain']:
                return self._view(row)
            db.execute("UPDATE tasks SET state='waiting',code='dispatch_review_required',sequence=sequence+1,updated=? WHERE id=?",
                       (self.clock(), task_id))
        return self.inspect(task_id)

    def finish_model(self, task_id, state):
        if state == 'completed':
            return self.complete(task_id)
        if state not in {'failed', 'canceled'}:
            raise TaskError('invalid_model_state')
        with self.profiles._transaction() as db:
            row = self._row(db, task_id)
            if row['state'] in self.TERMINAL or row['result_uncertain'] or row['state'] == 'running':
                return self._view(row)
            db.execute('UPDATE tasks SET state=?,code=?,sequence=sequence+1,updated=? WHERE id=?',
                       (state, 'engine_failed' if state == 'failed' else 'canceled', self.clock(), task_id))
        return self.inspect(task_id)

    def complete(self, task_id):
        with self.profiles._transaction() as db:
            row = self._row(db, task_id)
            if row['state'] in self.TERMINAL:
                return self._view(row)
            if row['result_uncertain'] or row['state'] != 'planning':
                raise TaskError('task_not_completable')
            if db.execute("SELECT 1 FROM task_operations WHERE task_id=? AND state!='completed'", (task_id,)).fetchone():
                raise TaskError('operation_pending')
            state = 'canceled' if row['cancel_requested'] else 'completed'
            db.execute('UPDATE tasks SET state=?,code=?,sequence=sequence+1,updated=? WHERE id=?',
                       (state, state, self.clock(), task_id))
        return self.inspect(task_id)

    def recover(self):
        """On service ownership acquisition: hold unfinished work, never replay."""
        with self.exclusive(), self.profiles._transaction() as db:
            rows = db.execute("SELECT * FROM tasks WHERE state IN ('queued','planning','running')").fetchall()
            for row in rows:
                uncertain = db.execute("SELECT 1 FROM task_operations WHERE task_id=? AND state IN ('running','uncertain')", (row['id'],)).fetchone() is not None
                db.execute("UPDATE task_operations SET state='uncertain',updated=? WHERE task_id=? AND state='running'", (self.clock(), row['id']))
                # Prepared was durably not dispatched; still require explicit resume.
                db.execute("UPDATE tasks SET state='waiting',result_uncertain=?,code=?,sequence=sequence+1,updated=? WHERE id=?",
                           (int(uncertain), 'reconciliation_required' if uncertain else 'restart_review_required', self.clock(), row['id']))
            return len(rows)

    def reconcile(self, task_id, operation_id, inspect_effect):
        """Read-only trusted inspector may prove completion; never apply an effect.

        Only exact True proves a known effect. False/errors keep uncertainty and
        require owner review; lack of evidence is never permission to replay.
        """
        with self.exclusive():
            operation = self.operation(task_id, operation_id)
            if operation['state'] == 'completed':
                return operation
            if operation['state'] != 'uncertain':
                raise TaskError('operation_not_reconcilable')
            try:
                verified = inspect_effect(operation_id, operation['kind']) is True
            except Exception:
                verified = False
            if verified:
                self._operation_result(task_id, operation_id, 'completed', True)
            return self.operation(task_id, operation_id)
