"""Independent executor policy and durable no-replay operation records.

Only the root service owns this store in production. Policy mutation is invoked
by the separately authenticated owner surface, never by broker/model IPC. The
caller/session identities below must come from the transport/logind, not JSON.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time


class PolicyError(Exception):
    pass


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}',value):
        raise PolicyError('invalid_identifier')
    return value


def owner(value):
    if type(value) is not int or not 1 <= value <= 2**32-2:
        raise PolicyError('invalid_owner')
    return value


def request_hash(kind, arguments):
    # Operation-specific schema validation is mandatory at the service boundary.
    identifier(kind)
    try:
        payload=json.dumps({'kind':kind,'arguments':arguments},sort_keys=True,separators=(',',':'),
                           ensure_ascii=False,allow_nan=False).encode('utf-8',errors='strict')
    except (ValueError,TypeError,UnicodeError,RecursionError):
        raise PolicyError('invalid_arguments') from None
    if len(payload)>65536:
        raise PolicyError('arguments_limit')
    return hashlib.sha256(payload).hexdigest()


class Store:
    def __init__(self,path,*,clock=time.time):
        self.path=Path(path)
        if not self.path.is_absolute() or self.path.resolve()!=self.path:
            raise PolicyError('unsafe_store_path')
        self.clock=clock
        self.path.mkdir(mode=0o700,exist_ok=True)
        directory=self.path.stat()
        if directory.st_uid!=os.getuid() or stat.S_IMODE(directory.st_mode)!=0o700:
            raise PolicyError('unsafe_store_directory')
        # Inspect/create before SQLite opens; root-owned0700 parent is the trust
        # boundary against other users. Same-UID/root hostile code is not isolated.
        for name in ('state.sqlite','dispatch.lock'):
            fd=os.open(self.path/name,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
            try:
                info=os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:
                    raise PolicyError('unsafe_store_file')
            finally:os.close(fd)
        with self._db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS grants(
                uid INTEGER PRIMARY KEY,generation INTEGER NOT NULL,mode TEXT NOT NULL,
                session TEXT,expires REAL NOT NULL,enabled INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS operations(
                id TEXT PRIMARY KEY,uid INTEGER NOT NULL,kind TEXT NOT NULL,input_hash TEXT NOT NULL,
                generation INTEGER NOT NULL,state TEXT NOT NULL,result TEXT,created REAL NOT NULL,
                cancel_requested INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS audit(
                sequence INTEGER PRIMARY KEY,at REAL NOT NULL,event TEXT NOT NULL,uid INTEGER NOT NULL,
                operation TEXT,kind TEXT,generation INTEGER NOT NULL,state TEXT);''')
            # Reopen the earlier B04 core schema without discarding operation IDs.
            if 'cancel_requested' not in {row['name'] for row in db.execute('PRAGMA table_info(operations)')}:
                db.execute('ALTER TABLE operations ADD COLUMN cancel_requested INTEGER NOT NULL DEFAULT 0')

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path/'state.sqlite',timeout=5,isolation_level=None)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA busy_timeout=5000')
        try:yield db
        finally:db.close()

    @contextmanager
    def _transaction(self):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK');raise

    def _audit(self,db,event,uid,generation,op=None,kind=None,state=None):
        db.execute('INSERT INTO audit(at,event,uid,operation,kind,generation,state) VALUES(?,?,?,?,?,?,?)',
                   (self.clock(),event,uid,op,kind,generation,state))

    def set_grant(self,uid,mode,*,expires,session=None):
        """Trusted owner-policy entry only; never expose on broker/model interface."""
        owner(uid)
        if mode not in ('session','standing') or type(expires) not in (int,float) or not self.clock()<expires<=self.clock()+365*86400:
            raise PolicyError('invalid_grant')
        if (mode=='session' and (not isinstance(session,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}',session))) or (mode=='standing' and session is not None):
            raise PolicyError('invalid_session')
        with self._transaction() as db:
            old=db.execute('SELECT generation FROM grants WHERE uid=?',(uid,)).fetchone()
            generation=old['generation']+1 if old else 1
            db.execute('INSERT OR REPLACE INTO grants VALUES(?,?,?,?,?,1)',(uid,generation,mode,session,expires))
            self._audit(db,'grant',uid,generation)
        return generation

    def revoke(self,uid):
        owner(uid)
        with self._transaction() as db:
            old=db.execute('SELECT generation FROM grants WHERE uid=?',(uid,)).fetchone()
            generation=old['generation']+1 if old else 1
            db.execute('INSERT OR REPLACE INTO grants VALUES(?,?,?,NULL,0,0)',(uid,generation,'standing'))
            self._audit(db,'revoke',uid,generation)
            # Stop managed in-flight work where its safe boundary permits it;
            # already committed effects remain explicit in their result.
            running=db.execute("SELECT * FROM operations WHERE uid=? AND state='running'",(uid,)).fetchall()
            for operation in running:
                db.execute('UPDATE operations SET cancel_requested=1 WHERE id=?',(operation['id'],))
                self._audit(db,'revoke_cancel',uid,generation,operation['id'],operation['kind'],'running')
        return generation

    def _grant(self,db,uid,session):
        row=db.execute('SELECT * FROM grants WHERE uid=?',(uid,)).fetchone()
        if not row or not row['enabled'] or row['expires']<=self.clock() or (row['mode']=='session' and row['session']!=session):
            raise PolicyError('grant_required')
        return row

    def plan(self,uid,session,op,kind,arguments):
        owner(uid);identifier(op);digest=request_hash(kind,arguments)
        with self._transaction() as db:
            existing=db.execute('SELECT * FROM operations WHERE id=?',(op,)).fetchone()
            if existing:
                if existing['uid']!=uid or existing['input_hash']!=digest:
                    raise PolicyError('operation_identity_conflict')
                return self._view(existing)
            grant=self._grant(db,uid,session)
            db.execute('INSERT INTO operations(id,uid,kind,input_hash,generation,state,result,created) VALUES(?,?,?,?,?,?,NULL,?)',
                (op,uid,kind,digest,grant['generation'],'planned',self.clock()))
            self._audit(db,'plan',uid,grant['generation'],op,kind,'planned')
            return {'id':op,'state':'planned','generation':grant['generation'],'result':None,'cancel_requested':False}

    @staticmethod
    def _view(row):
        return {'id':row['id'],'state':row['state'],'generation':row['generation'],
                'result':json.loads(row['result']) if row['result'] else None,'cancel_requested':bool(row['cancel_requested'])}

    def inspect(self,uid,op):
        owner(uid);identifier(op)
        with self._db() as db:
            row=db.execute('SELECT * FROM operations WHERE id=? AND uid=?',(op,uid)).fetchone()
            if not row:raise PolicyError('operation_unknown')
            return self._view(row)

    def cancel(self,uid,op):
        # Stopping one's accepted work remains possible after grant revocation.
        owner(uid);identifier(op)
        with self._transaction() as db:
            row=db.execute('SELECT * FROM operations WHERE id=? AND uid=?',(op,uid)).fetchone()
            if not row:raise PolicyError('operation_unknown')
            if row['state'] in ('planned','running'):
                state='canceled' if row['state']=='planned' else 'running'
                result='{"code":"canceled_before_dispatch"}' if state=='canceled' else row['result']
                db.execute('UPDATE operations SET cancel_requested=1,state=?,result=? WHERE id=?',(state,result,op))
                self._audit(db,'cancel_request',uid,row['generation'],op,row['kind'],state)
        return self.inspect(uid,op)

    def dispatch(self,uid,session,op,kind,arguments,apply):
        """Serialize mutations, recheck current grant, durably mark before effect.

        apply is trusted service code and returns only a bounded non-secret verified
        postcondition. Any unexpected failure is uncertain and never auto-replayed.
        """
        owner(uid);identifier(op);digest=request_hash(kind,arguments)
        with open(self.path/'dispatch.lock','r+b') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise PolicyError('executor_busy') from None
            with self._transaction() as db:
                row=db.execute('SELECT * FROM operations WHERE id=?',(op,)).fetchone()
                if not row or row['uid']!=uid or row['input_hash']!=digest:
                    raise PolicyError('operation_identity_conflict')
                if row['state']!='planned':return self._view(row)
                grant=self._grant(db,uid,session)
                if grant['generation']!=row['generation']:raise PolicyError('grant_changed')
                db.execute("UPDATE operations SET state='running' WHERE id=?",(op,))
                self._audit(db,'dispatch',uid,row['generation'],op,kind,'running')
            # No DB writer lock held during effects; revocation remains responsive.
            try:
                result=apply(kind,arguments)
                encoded=json.dumps(result,allow_nan=False,separators=(',',':'))
                if not isinstance(result,dict) or len(encoded.encode())>4096:
                    raise PolicyError('invalid_postcondition')
                state='completed'
            except BaseException as error:
                safe_codes={'package_status_unverified','package_recovery_required',
                    'package_transaction_requires_reconciliation','package_postcondition_failed',
                    'native_package_backend_unavailable','package_not_installed',
                    'operation_canceled_before_package_write'}
                code=str(error) if isinstance(error,PolicyError) and str(error) in safe_codes else 'postcondition_unverified'
                state='uncertain';encoded=json.dumps({'code':code})
                self._finish(uid,op,kind,row['generation'],state,encoded)
                raise PolicyError('operation_uncertain') from None
            self._finish(uid,op,kind,row['generation'],state,encoded)
            return self.inspect(uid,op)

    def _finish(self,uid,op,kind,generation,state,encoded):
        with self._transaction() as db:
            db.execute('UPDATE operations SET state=?,result=? WHERE id=?',(state,encoded,op))
            self._audit(db,'finish',uid,generation,op,kind,state)

    def recover(self):
        """Startup under service-wide dispatch lock; never replay effects."""
        with open(self.path/'dispatch.lock','r+b') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise PolicyError('executor_busy') from None
            with self._transaction() as db:
                rows=db.execute("SELECT * FROM operations WHERE state='running'").fetchall()
                for row in rows:
                    db.execute("UPDATE operations SET state='uncertain',result=? WHERE id=?",
                               ('{"code":"restart_reconciliation_required"}',row['id']))
                    self._audit(db,'recover',row['uid'],row['generation'],row['id'],row['kind'],'uncertain')
                return len(rows)

    def audit(self,uid,after=0):
        owner(uid)
        if type(after) is not int or not 0<=after<=2**53-1:raise PolicyError('invalid_audit_cursor')
        with self._db() as db:
            return [dict(row) for row in db.execute('SELECT * FROM audit WHERE uid=? AND sequence>? ORDER BY sequence LIMIT 100',(uid,after))]
