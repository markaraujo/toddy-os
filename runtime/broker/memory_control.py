"""Bounded explicit-owner memory IPC operations; no model tool or file path API."""
import fcntl
import json
import os
import stat

try:
    from .memory import MAX_EXPORT
    from .memory_api import MemoryAPIError
    from .protocol import strict_json
except ImportError:
    from memory import MAX_EXPORT
    from memory_api import MemoryAPIError
    from protocol import strict_json

SEALS = fcntl.F_SEAL_SEAL | fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK


def generation(value):
    if type(value) is not int or not 0 <= value < 2**53:
        raise MemoryAPIError('memory_generation_invalid')
    return value


def sealed_export(data):
    if type(data) is not bytes or len(data) > MAX_EXPORT:
        raise MemoryAPIError('memory_transfer_limit')
    descriptor = os.memfd_create('toddy-memory-export', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        os.fchmod(descriptor, 0o600)
        remaining = memoryview(data)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining):]
        fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS, SEALS)
        return os.open('/proc/self/fd/' + str(descriptor), os.O_RDONLY | os.O_CLOEXEC)
    finally:
        os.close(descriptor)


def sealed_import(descriptor):
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink > 1 or info.st_mode & 0o077 or not 0 < info.st_size <= MAX_EXPORT:
            raise MemoryAPIError('memory_transfer_fd')
        if fcntl.fcntl(descriptor, fcntl.F_GET_SEALS) & SEALS != SEALS:
            raise MemoryAPIError('memory_transfer_seals_required')
        data = os.pread(descriptor, MAX_EXPORT + 1, 0)
        if len(data) != info.st_size:
            raise MemoryAPIError('memory_transfer_changed')
        return data
    except (OSError, TypeError, ValueError) as exc:
        if isinstance(exc, MemoryAPIError):
            raise
        raise MemoryAPIError('memory_transfer_fd') from None


class MemoryControl:
    def __init__(self, memory):
        self.memory = memory

    def result(self, value):
        # MemoryAPI internally returns records for trusted callers, never expose
        # an unbounded mutation result or private text in metadata signals.
        safe = {key: value[key] for key in ('profile_revision', 'memory_generation',
            'ignored_deleted_ids', 'previous_user_document_preserved',
            'projection_sha256', 'manual_user_document_preserved') if key in value}
        return {'version': 1, 'profile_id': self.memory.profiles.profile_id, **safe}

    def page(self, after_id='', limit=16):
        value = self.memory.page(after_id, limit=limit)
        if len(json.dumps(value, ensure_ascii=False).encode()) > 49152:
            raise MemoryAPIError('memory_page_limit')
        return value

    def mutate(self, expected_revision, encoded):
        if not isinstance(encoded, str) or len(encoded.encode()) > 65536:
            raise MemoryAPIError('memory_mutation_limit')
        value = strict_json(encoded.encode())
        if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != 1:
            raise MemoryAPIError('memory_mutation_schema')
        shared = {'version', 'memory_generation', 'operation'}
        op = value.get('operation')
        fields = {'put': {'id', 'text', 'expires'}, 'delete': {'id'},
                  'review-user-document': {'preferences', 'reviewed_user_sha256'}}
        if not isinstance(op, str) or op not in fields or set(value) != shared | fields[op]:
            raise MemoryAPIError('memory_mutation_schema')
        kwargs = {'expected_revision': expected_revision, 'expected_generation': generation(value['memory_generation'])}
        if op == 'put':
            result = self.memory.put(value['id'], value['text'], expires=value['expires'], **kwargs)
        elif op == 'delete':
            result = self.memory.delete(value['id'], **kwargs)
        else:
            if not isinstance(value['preferences'], dict):
                raise MemoryAPIError('memory_mutation_schema')
            result = self.memory.review_user_document(value['preferences'],
                reviewed_user_sha256=value['reviewed_user_sha256'], **kwargs)
        return self.result(result)

    def export(self, expected_revision, expected_generation):
        return sealed_export(self.memory.export(expected_revision=expected_revision,
            expected_generation=generation(expected_generation)))

    def export_document(self, expected_revision, expected_generation):
        return sealed_export(self.memory.user_document(expected_revision=expected_revision,
            expected_generation=generation(expected_generation)))

    def restore(self, expected_revision, expected_generation, descriptor):
        # Immutable FD bytes are untrusted input, never an instruction or path.
        data = sealed_import(descriptor)
        return self.result(self.memory.restore(data, expected_revision=expected_revision,
            expected_generation=generation(expected_generation)))
