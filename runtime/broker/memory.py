"""Bounded memory extension of the broker's canonical per-profile SQLite store.

The broker supplies its existing connection, authenticates the user and owns the
outer transaction. No file paths, credentials, tasks or grants are imported here.
Document content is always untrusted; only explicit owner edits make preferences.
This module never scans USER.md or rehydrates memory from a retrieval cache.
"""
from contextlib import contextmanager
import hashlib
import json
import math
import re
import time
import uuid


MAX_RECORDS = 10000
MAX_EXPORT = 8 * 1024 * 1024
MAX_TEXT = 4096
ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
KINDS = {"preference", "document"}
SOURCES = {"owner-edit", "user-md", "document"}


class MemoryError(ValueError):
    """A bounded validation or canonical memory conflict, without private text."""


def _text(value, limit=MAX_TEXT):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise MemoryError("memory_text")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise MemoryError("memory_text") from exc
    if size > limit:
        raise MemoryError("memory_text_limit")
    return value


def _id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise MemoryError("memory_id")
    return value


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise MemoryError("memory_timestamp")
    if not math.isfinite(value) or not 0 <= value <= 2**53 - 1:
        raise MemoryError("memory_timestamp")
    return value


@contextmanager
def _atomic(db):
    # SAVEPOINT also works inside caller-owned transactions; never commit them.
    name = "memory_" + uuid.uuid4().hex
    db.execute("SAVEPOINT " + name)
    try:
        yield
    except BaseException:
        db.execute("ROLLBACK TO " + name)
        db.execute("RELEASE " + name)
        raise
    else:
        db.execute("RELEASE " + name)


class Memory:
    """Logical profile isolation; same-UID arbitrary code is not a boundary.

    Caller must use an owned private canonical DB, serialize writers and avoid
    passing secrets as text. Export is an explicit memory-only disclosure, never
    an automatic diagnostic or credential scrubber for arbitrary user prose.
    """

    def __init__(self, db, profile_id, *, clock=time.time):
        self.db = db
        self.profile = _id(profile_id)
        self.clock = clock
        self._migrate()

    def _migrate(self):
        with _atomic(self.db):
            self.db.execute("CREATE TABLE IF NOT EXISTS memory_schema(version INTEGER NOT NULL)")
            versions = [r[0] for r in self.db.execute("SELECT version FROM memory_schema")]
            if versions and versions != [1]:
                raise MemoryError("memory_schema_version")
            if versions:
                return
            # Execute individually: executescript would commit an outer transaction.
            statements = [
                """CREATE TABLE memory_records(
                    profile_id TEXT NOT NULL, id TEXT NOT NULL, kind TEXT NOT NULL,
                    text TEXT NOT NULL, source_kind TEXT NOT NULL, source_ref TEXT NOT NULL,
                    source_revision TEXT NOT NULL, updated REAL NOT NULL, expires REAL,
                    PRIMARY KEY(profile_id,id))""",
                """CREATE TABLE memory_deleted(
                    profile_id TEXT NOT NULL, id TEXT NOT NULL, deleted REAL NOT NULL,
                    PRIMARY KEY(profile_id,id))""",
                """CREATE VIRTUAL TABLE memory_fts USING fts5(
                    profile_id UNINDEXED, memory_id UNINDEXED, text, tokenize='unicode61')""",
                """CREATE TRIGGER memory_insert AFTER INSERT ON memory_records BEGIN
                    INSERT INTO memory_fts(profile_id,memory_id,text)
                    VALUES(new.profile_id,new.id,new.text); END""",
                """CREATE TRIGGER memory_delete AFTER DELETE ON memory_records BEGIN
                    DELETE FROM memory_fts WHERE profile_id=old.profile_id AND memory_id=old.id; END""",
                """CREATE TRIGGER memory_update AFTER UPDATE ON memory_records BEGIN
                    DELETE FROM memory_fts WHERE profile_id=old.profile_id AND memory_id=old.id;
                    INSERT INTO memory_fts(profile_id,memory_id,text)
                    VALUES(new.profile_id,new.id,new.text); END""",
                "INSERT INTO memory_schema VALUES(1)",
            ]
            for statement in statements:
                self.db.execute(statement)

    def _record(self, record):
        expected = {"id", "kind", "text", "source_kind", "source_ref", "source_revision", "updated", "expires"}
        if not isinstance(record, dict) or set(record) != expected:
            raise MemoryError("memory_record_fields")
        _id(record["id"])
        if not isinstance(record["kind"], str) or not isinstance(record["source_kind"], str) or record["kind"] not in KINDS or record["source_kind"] not in SOURCES:
            raise MemoryError("memory_record_kind")
        if (record["kind"] == "document") != (record["source_kind"] == "document"):
            raise MemoryError("memory_source_trust")
        _text(record["text"])
        _text(record["source_ref"], 1024)
        if not isinstance(record["source_revision"], str) or not HASH.fullmatch(record["source_revision"]):
            raise MemoryError("memory_source_revision")
        _number(record["updated"])
        if record["expires"] is not None:
            _number(record["expires"])
            if record["expires"] <= record["updated"]:
                raise MemoryError("memory_retention")
        return record

    def put(self, memory_id, text, *, source_ref, kind="preference", source_kind="owner-edit",
            source_revision=None, expires=None):
        """Explicit current-owner change; revives a deliberately deleted key.

        The broker must not expose this owner action directly to document/model
        output. USER.md ingestion uses import_user_preferences instead.
        """
        record = self._record({"id": memory_id, "kind": kind, "text": text,
            "source_kind": source_kind, "source_ref": source_ref,
            "source_revision": source_revision or hashlib.sha256(_text(text).encode()).hexdigest(),
            "updated": _number(self.clock()), "expires": expires})
        with _atomic(self.db):
            self._upsert(record)
            self.db.execute("DELETE FROM memory_deleted WHERE profile_id=? AND id=?", (self.profile, memory_id))
        return self.get(memory_id)

    def _upsert(self, record):
        count, exists = self._capacity(record["id"])
        if count >= MAX_RECORDS and not exists:
            raise MemoryError("memory_record_limit")
        self.db.execute("""INSERT INTO memory_records VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(profile_id,id) DO UPDATE SET kind=excluded.kind,text=excluded.text,
            source_kind=excluded.source_kind,source_ref=excluded.source_ref,
            source_revision=excluded.source_revision,updated=excluded.updated,expires=excluded.expires""",
            (self.profile, record["id"], record["kind"], record["text"], record["source_kind"],
             record["source_ref"], record["source_revision"], record["updated"], record["expires"]))

    def _capacity(self, memory_id):
        rows = self.db.execute("""SELECT id FROM memory_records WHERE profile_id=?
            UNION SELECT id FROM memory_deleted WHERE profile_id=?""", (self.profile, self.profile)).fetchall()
        return len(rows), any(row[0] == memory_id for row in rows)

    def _rows(self, sql, params):
        cursor = self.db.execute(sql, params)
        keys = [c[0] for c in cursor.description]
        return [dict(zip(keys, row)) for row in cursor.fetchall()]

    def inspect(self):
        """Bounded canonical view; expired records are never retrieved."""
        return self._rows("""SELECT id,kind,text,source_kind,source_ref,source_revision,updated,expires
            FROM memory_records WHERE profile_id=? AND (expires IS NULL OR expires>?) ORDER BY id""",
            (self.profile, _number(self.clock())))

    def get(self, memory_id):
        _id(memory_id)
        rows = self._rows("""SELECT id,kind,text,source_kind,source_ref,source_revision,updated,expires
            FROM memory_records WHERE profile_id=? AND id=? AND (expires IS NULL OR expires>?)""",
            (self.profile, memory_id, _number(self.clock())))
        return rows[0] if rows else None

    def search(self, query, *, limit=10):
        _text(query, 1024)
        if type(limit) is not int or not 1 <= limit <= 50:
            raise MemoryError("memory_query_limit")
        words = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
        if not words or len(words) > 16:
            raise MemoryError("memory_query_terms")
        match = " AND ".join('"' + word + '"' for word in words)
        return self._rows("""SELECT r.id,r.kind,r.text,r.source_kind,r.source_ref,r.source_revision,r.updated,r.expires
            FROM memory_fts JOIN memory_records r ON r.profile_id=memory_fts.profile_id AND r.id=memory_fts.memory_id
            WHERE memory_fts MATCH ? AND r.profile_id=? AND (r.expires IS NULL OR r.expires>?)
            ORDER BY bm25(memory_fts),r.id LIMIT ?""", (match, self.profile, _number(self.clock()), limit))

    def delete(self, memory_id):
        """Delete canonical/FTS data and suppress automatic USER.md reimport."""
        _id(memory_id)
        with _atomic(self.db):
            count, exists = self._capacity(memory_id)
            if count >= MAX_RECORDS and not exists:
                raise MemoryError("memory_record_limit")
            self.db.execute("DELETE FROM memory_records WHERE profile_id=? AND id=?", (self.profile, memory_id))
            self.db.execute("""INSERT INTO memory_deleted VALUES(?,?,?) ON CONFLICT(profile_id,id)
                DO UPDATE SET deleted=excluded.deleted""", (self.profile, memory_id, _number(self.clock())))

    def expire(self):
        rows = self.db.execute("SELECT id FROM memory_records WHERE profile_id=? AND expires<=?", (self.profile, _number(self.clock()))).fetchall()
        with _atomic(self.db):
            for row in rows:
                self.delete(row[0])
        return len(rows)

    def import_user_preferences(self, preferences, *, source_revision):
        """Review-parsed USER.md input; tombstones always win automatic imports.

        No raw Markdown parsing or prompt-driven trust promotion happens here.
        An explicit put is required to revive a deleted preference, even after a
        different file revision. A source cannot replace explicit owner edits.
        """
        if not isinstance(preferences, dict) or len(preferences) > MAX_RECORDS:
            raise MemoryError("memory_preferences")
        records = [self._record({"id": key, "kind": "preference", "text": text,
            "source_kind": "user-md", "source_ref": "USER.md", "source_revision": source_revision,
            "updated": _number(self.clock()), "expires": None}) for key, text in preferences.items()]
        applied = []
        with _atomic(self.db):
            self.expire()
            for row in self.db.execute("SELECT id FROM memory_records WHERE profile_id=? AND source_kind='user-md'", (self.profile,)).fetchall():
                if row[0] not in preferences:
                    self.delete(row[0])
            for record in records:
                key = record["id"]
                deleted = self.db.execute("SELECT 1 FROM memory_deleted WHERE profile_id=? AND id=?", (self.profile, key)).fetchone()
                old = self.get(key)
                if deleted or (old and old["source_kind"] != "user-md"):
                    continue
                self._upsert(record)
                applied.append(key)
        return applied

    def export(self):
        """Explicit memory-only portable JSON, excluding tasks/grants/credentials.

        Text itself is user-selected private memory; this does not claim to find
        every secret a user may have deliberately pasted into a preference.
        """
        with _atomic(self.db):
            self.expire()
            records = self.inspect()
            deleted = self._rows("SELECT id,deleted FROM memory_deleted WHERE profile_id=? ORDER BY id", (self.profile,))
            document = {"memory_version": 1, "records": records, "deleted": deleted}
            data = json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
            if len(data) > MAX_EXPORT:
                raise MemoryError("memory_export_limit")
        return data

    def restore(self, data):
        """Replace this profile's memory atomically; never restore active work.

        Existing deletion tombstones prevail over older backups. Other profiles,
        canonical tasks, profile revisions and executor policy remain unchanged.
        """
        if not isinstance(data, bytes) or len(data) > MAX_EXPORT:
            raise MemoryError("memory_import_limit")
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise MemoryError("memory_duplicate_key")
                result[key] = value
            return result
        try:
            doc = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=pairs)
        except (UnicodeError, ValueError, RecursionError) as exc:
            raise MemoryError("memory_import_json") from exc
        if not isinstance(doc, dict) or set(doc) != {"memory_version", "records", "deleted"} or type(doc["memory_version"]) is not int or doc["memory_version"] != 1:
            raise MemoryError("memory_import_schema")
        if not isinstance(doc["records"], list) or not isinstance(doc["deleted"], list) or len(doc["records"]) + len(doc["deleted"]) > MAX_RECORDS:
            raise MemoryError("memory_import_records")
        records = [self._record(record) for record in doc["records"]]
        ids = [record["id"] for record in records]
        deleted = {}
        for item in doc["deleted"]:
            if not isinstance(item, dict) or set(item) != {"id", "deleted"}:
                raise MemoryError("memory_import_deleted")
            key = _id(item["id"])
            if key in deleted:
                raise MemoryError("memory_import_duplicate")
            deleted[key] = _number(item["deleted"])
        if len(ids) != len(set(ids)) or set(ids) & set(deleted):
            raise MemoryError("memory_import_duplicate")
        with _atomic(self.db):
            # Keep local tombstones: restoring an old backup cannot resurrect a
            # deletion the owner made after that backup was exported.
            local = dict(self.db.execute("SELECT id,deleted FROM memory_deleted WHERE profile_id=?", (self.profile,)))
            deleted.update(local)
            if len(set(ids) | set(deleted)) > MAX_RECORDS:
                raise MemoryError("memory_record_limit")
            self.db.execute("DELETE FROM memory_records WHERE profile_id=?", (self.profile,))
            for key, when in deleted.items():
                self.db.execute("INSERT OR REPLACE INTO memory_deleted VALUES(?,?,?)", (self.profile, key, when))
            for record in records:
                if record["id"] not in deleted:
                    self._upsert(record)
