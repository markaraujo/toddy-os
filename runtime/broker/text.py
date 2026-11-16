"""Bounded private assistant-output spool in the canonical per-profile SQLite DB.

This is separate from minimal task metadata and memory exports. History-off output
is a transient handoff (at most five minutes), never saved conversation history.
No prompt/tool trace/connection/key is accepted by this text-only API.
"""
import json
import time


class TextError(ValueError):
    pass


class TaskText:
    def __init__(self, journal, *, clock=time.time, task_limit=262144, profile_limit=16 * 1024 * 1024):
        self.journal = journal
        self.profiles = journal.profiles
        self.clock = clock
        self.task_limit, self.profile_limit = task_limit, profile_limit
        with self.profiles._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS task_text_state(
                    task_id TEXT PRIMARY KEY REFERENCES tasks(id),latest INTEGER NOT NULL,
                    bytes INTEGER NOT NULL,complete INTEGER NOT NULL,history_enabled INTEGER NOT NULL,
                    retention_days INTEGER NOT NULL,expires REAL,expired INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS task_text_chunks(
                    task_id TEXT NOT NULL REFERENCES task_text_state(task_id),sequence INTEGER NOT NULL,
                    text TEXT NOT NULL,bytes INTEGER NOT NULL,PRIMARY KEY(task_id,sequence));
            ''')

    def begin(self, task_id, *, history_enabled, retention_days):
        if type(history_enabled) is not bool or type(retention_days) is not int or not 0 <= retention_days <= 365:
            raise TextError('invalid_text_retention')
        with self.profiles._transaction() as db:
            self.journal._row(db, task_id)
            used = db.execute('SELECT coalesce(sum(bytes),0) FROM task_text_state WHERE expired=0').fetchone()[0]
            if used + self.task_limit > self.profile_limit:
                raise TextError('task_text_limit')
            self.journal._capacity(self.task_limit + 32768)
            db.execute('INSERT OR IGNORE INTO task_text_state VALUES(?,0,0,0,?,?,NULL,0)',
                       (task_id, int(history_enabled and retention_days > 0), retention_days))

    def append(self, task_id, text):
        if not isinstance(text, str):
            raise TextError('invalid_task_text')
        try:
            size = len(text.encode('utf-8', errors='strict'))
        except UnicodeError:
            raise TextError('invalid_task_text') from None
        if size > self.task_limit:
            raise TextError('task_text_limit')
        if not text:
            return self.latest(task_id)
        chunks, current, current_bytes = [], [], 0
        for character in text:
            encoded = len(character.encode())
            if current_bytes + encoded > 1024:
                chunks.append(''.join(current)); current, current_bytes = [], 0
            current.append(character); current_bytes += encoded
        if current:
            chunks.append(''.join(current))
        with self.profiles._transaction() as db:
            row = db.execute('SELECT * FROM task_text_state WHERE task_id=?', (task_id,)).fetchone()
            if row is None or row['expired'] or row['complete']:
                raise TextError('task_text_not_writable')
            used = db.execute('SELECT coalesce(sum(bytes),0) FROM task_text_state WHERE expired=0').fetchone()[0]
            if row['bytes'] + size > self.task_limit or used + size > self.profile_limit or row['latest'] + len(chunks) > 16384:
                raise TextError('task_text_limit')
            self.journal._capacity(size + 32768)
            sequence = row['latest']
            for chunk in chunks:
                sequence += 1
                db.execute('INSERT INTO task_text_chunks VALUES(?,?,?,?)', (task_id, sequence, chunk, len(chunk.encode())))
            db.execute('UPDATE task_text_state SET latest=?,bytes=bytes+? WHERE task_id=?', (sequence, size, task_id))
        return sequence

    def finish(self, task_id):
        with self.profiles._transaction() as db:
            row = db.execute('SELECT * FROM task_text_state WHERE task_id=?', (task_id,)).fetchone()
            if row is None:
                return
            lifetime = row['retention_days'] * 86400 if row['history_enabled'] else 300
            db.execute('UPDATE task_text_state SET complete=1,expires=coalesce(expires,?) WHERE task_id=?',
                       (self.clock() + lifetime, task_id))

    def latest(self, task_id):
        with self.profiles._db() as db:
            self.journal._row(db, task_id)
            row = db.execute('SELECT latest FROM task_text_state WHERE task_id=?', (task_id,)).fetchone()
            return row['latest'] if row else 0

    def marker(self, task_id):
        with self.profiles._db() as db:
            task = self.journal._row(db, task_id)
            row = db.execute('SELECT latest,complete FROM task_text_state WHERE task_id=?', (task_id,)).fetchone()
            return (row['latest'], bool(row['complete'])) if row else (0, task['state'] in {'completed', 'failed', 'canceled', 'waiting'})

    def exists(self, task_id):
        with self.profiles._db() as db:
            return db.execute('SELECT 1 FROM task_text_state WHERE task_id=?', (task_id,)).fetchone() is not None

    def page(self, task_id, after_sequence):
        if type(after_sequence) is not int or not 0 <= after_sequence <= 2**53 - 1:
            raise TextError('invalid_text_cursor')
        with self.profiles._db() as db:
            task = self.journal._row(db, task_id)
            row = db.execute('SELECT * FROM task_text_state WHERE task_id=?', (task_id,)).fetchone()
            if row is None:
                if after_sequence != 0:
                    raise TextError('invalid_text_cursor')
                return {'version': 1, 'task_id': task_id, 'chunks': [], 'next_sequence': 0, 'latest_sequence': 0,
                        'complete': task['state'] in {'completed', 'failed', 'canceled', 'waiting'}, 'history_enabled': False}
            if row['expired'] or (row['complete'] and row['expires'] <= self.clock()):
                raise TextError('task_text_unavailable')
            if after_sequence > row['latest']:
                raise TextError('invalid_text_cursor')
            page = {'version': 1, 'task_id': task_id, 'chunks': [], 'next_sequence': after_sequence,
                    'latest_sequence': row['latest'], 'complete': bool(row['complete']),
                    'history_enabled': bool(row['history_enabled'])}
            for chunk in db.execute('SELECT sequence,text FROM task_text_chunks WHERE task_id=? AND sequence>? ORDER BY sequence LIMIT 256',
                                    (task_id, after_sequence)):
                item = {'sequence': chunk['sequence'], 'text': chunk['text']}
                page['chunks'].append(item)
                previous = page['next_sequence']; page['next_sequence'] = chunk['sequence']
                if len(json.dumps(page, ensure_ascii=False, separators=(',', ':')).encode()) > 32768:
                    page['chunks'].pop(); page['next_sequence'] = previous
                    break
            return page

    def purge_expired(self):
        with self.profiles._transaction() as db:
            ids = [row['task_id'] for row in db.execute('SELECT task_id FROM task_text_state WHERE complete=1 AND expired=0 AND expires<=?',
                                                      (self.clock(),))]
            for task in ids:
                db.execute('DELETE FROM task_text_chunks WHERE task_id=?', (task,))
                db.execute('UPDATE task_text_state SET expired=1,bytes=0 WHERE task_id=?', (task,))
            return len(ids)

    def acknowledge(self, task_id, through_sequence):
        if type(through_sequence) is not int or not 0 <= through_sequence <= 2**53 - 1:
            raise TextError('invalid_text_cursor')
        with self.profiles._transaction() as db:
            self.journal._row(db, task_id)
            row = db.execute('SELECT * FROM task_text_state WHERE task_id=?', (task_id,)).fetchone()
            if row is None:
                if through_sequence != 0:
                    raise TextError('invalid_text_cursor')
                return {'version': 1, 'task_id': task_id, 'erased': True}
            if not row['complete'] or through_sequence != row['latest']:
                raise TextError('text_ack_incomplete')
            erased = not row['history_enabled']
            if erased:
                db.execute('DELETE FROM task_text_chunks WHERE task_id=?', (task_id,))
                db.execute('UPDATE task_text_state SET expired=1,bytes=0,expires=? WHERE task_id=?', (self.clock(), task_id))
        return {'version': 1, 'task_id': task_id, 'erased': erased}

    def purge_transient(self):
        """Clean shutdown/restart: erase terminal history-off output, keep journal."""
        with self.profiles._transaction() as db:
            ids = [row['task_id'] for row in db.execute('SELECT task_id FROM task_text_state WHERE complete=1 AND history_enabled=0 AND expired=0')]
            for task in ids:
                db.execute('DELETE FROM task_text_chunks WHERE task_id=?', (task,))
                db.execute('UPDATE task_text_state SET expired=1,bytes=0,expires=? WHERE task_id=?', (self.clock(), task))
            return len(ids)

    def recover(self):
        """Finalize output of interrupted runs; never restart model generation."""
        with self.profiles._db() as db:
            ids = [row['task_id'] for row in db.execute('SELECT task_id FROM task_text_state WHERE complete=0')]
        for task_id in ids:
            self.finish(task_id)
        return len(ids)
