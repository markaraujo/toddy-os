"""Root-owned durable acquisition identity; interrupted writes are never replayed."""
import json
import os
from pathlib import Path
import re
import sqlite3
import stat

from .pending import SetupError, _encode

TERMINAL = {'installed','deferred','canceled','failed'}
STATES = TERMINAL | {'prepared','downloading','installing','needs_reconciliation'}


def operation_id(value):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{32}',value):
        raise SetupError('acquisition_identity')


class Journal:
    def __init__(self, directory=Path('/var/lib/toddy/setup-acquisition'), *, owner_uid=0, observer=None, create=True, read_only=False):
        self.observer=observer
        self.directory = Path(directory)
        if not self.directory.is_absolute():
            raise SetupError('acquisition_custody')
        for component in (self.directory,*self.directory.parents):
            if component.is_symlink():
                raise SetupError('acquisition_custody')
        if read_only:create=False
        if not create and not (self.directory/'operations.sqlite').is_file():raise SetupError('acquisition_unknown')
        if create:self.directory.parent.mkdir(mode=0o755, exist_ok=True)
        parent=self.directory.parent.stat()
        if parent.st_uid!=owner_uid or stat.S_IMODE(parent.st_mode)&0o022:
            raise SetupError('acquisition_custody')
        if create:self.directory.mkdir(mode=0o700, exist_ok=True)
        info = self.directory.stat()
        if info.st_uid != owner_uid or stat.S_IMODE(info.st_mode) != 0o700:
            raise SetupError('acquisition_custody')
        path = self.directory/'operations.sqlite'
        descriptor = os.open(path,(os.O_RDONLY if read_only else os.O_RDWR)|(os.O_CREAT if create else 0)|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        info = os.fstat(descriptor); os.close(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != owner_uid or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
            raise SetupError('acquisition_custody')
        self.db = sqlite3.connect(path.as_uri()+('?mode=ro' if read_only else '?mode=rw'),uri=True,timeout=0,isolation_level=None)
        version=self.db.execute('PRAGMA user_version').fetchone()[0]
        if version!=1 and not (create and not info.st_size and version==0):
            self.db.close();raise SetupError('acquisition_storage_version')
        if read_only:return
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS operations(uid INTEGER NOT NULL,id TEXT NOT NULL,review TEXT NOT NULL,body TEXT NOT NULL,state TEXT NOT NULL,mutation INTEGER NOT NULL DEFAULT 0,cancel INTEGER NOT NULL DEFAULT 0,code TEXT,PRIMARY KEY(uid,id))')
        self.db.execute('CREATE TABLE IF NOT EXISTS catalog_generation(id INTEGER PRIMARY KEY CHECK(id=1),generation INTEGER NOT NULL)')
        self.db.execute('PRAGMA user_version=1')

    def close(self):
        self.db.close()

    def get(self,uid,identity):
        operation_id(identity)
        row = self.db.execute('SELECT review,body,state,mutation,cancel,code FROM operations WHERE uid=? AND id=?',(uid,identity)).fetchone()
        if row is None:
            return None
        return {'version':1,'operation_id':identity,'review_sha256':row[0],'review':json.loads(row[1]),
            'state':row[2],'write_intent_recorded':bool(row[3]),'cancellation_requested':bool(row[4]),'code':row[5],
            'backend_activated':False,'model_or_grant_created':False}

    def accept(self,uid,identity,review):
        operation_id(identity)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            previous = self.get(uid,identity)
            if previous is not None:
                if previous['review_sha256'] != review['review_sha256']:
                    raise SetupError('acquisition_identity_conflict')
                self.db.execute('COMMIT'); return previous,False
            if self.db.execute("SELECT 1 FROM operations WHERE state IN ('prepared','downloading','installing','needs_reconciliation') LIMIT 1").fetchone():
                raise SetupError('acquisition_reconciliation_required')
            generation = self.db.execute('SELECT generation FROM catalog_generation WHERE id=1').fetchone()
            if generation and review['catalog_generation'] < generation[0]:
                raise SetupError('release_rollback')
            self.db.execute('INSERT INTO catalog_generation VALUES(1,?) ON CONFLICT(id) DO UPDATE SET generation=max(generation,excluded.generation)',(review['catalog_generation'],))
            self.db.execute('INSERT INTO operations(uid,id,review,body,state) VALUES(?,?,?,?,?)',
                (uid,identity,review['review_sha256'],_encode(review).decode(),'prepared'))
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise
        result=self.get(uid,identity)
        if self.observer:self.observer(result)
        return result,True

    def state(self,uid,identity,state,*,code=None):
        if state not in STATES or code is not None and not re.fullmatch('[a-z_]{1,64}',code):
            raise SetupError('acquisition_state')
        current = self.get(uid,identity)
        if current is None or current['state'] in TERMINAL:
            raise SetupError('acquisition_terminal')
        self.db.execute('UPDATE operations SET state=?,code=?,mutation=max(mutation,?) WHERE uid=? AND id=?',
                        (state,code,int(state=='installing'),uid,identity))
        result=self.get(uid,identity)
        if self.observer:self.observer(result)
        return result

    def cancel(self,uid,identity):
        current = self.get(uid,identity)
        if current is None:
            raise SetupError('acquisition_unknown')
        self.db.execute('UPDATE operations SET cancel=1 WHERE uid=? AND id=?',(uid,identity))
        return self.get(uid,identity)
