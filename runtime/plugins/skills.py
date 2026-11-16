"""On-demand minimum SKILL.md parser; no YAML engine, code import or hooks.

Instruction text is data for a bounded task context, never executor policy.
Profile validation/import remains in the broker; this loader grants no tools.
"""
import os
from pathlib import Path
import stat

from .mcp import PluginError, _read_regular, name, relative


def _metadata(data, expected_name):
    try:
        text = data.decode('utf-8', errors='strict')
    except UnicodeError as exc:
        raise PluginError('skill_utf8') from exc
    if not text.startswith('---\n') or '\n---\n' not in text:
        raise PluginError('skill_metadata')
    front, _, body = text[4:].partition('\n---\n')
    if len(front.encode()) > 4096:
        raise PluginError('skill_metadata_limit')
    values = {}
    for line in front.splitlines():
        key, sep, value = line.partition(': ')
        if not sep or key not in ('name', 'description') or key in values or not value:
            raise PluginError('skill_metadata_fields')
        if value.startswith(('!', '&', '*', '{', '[', '|', '>', '"', "'")) or '\x00' in value:
            raise PluginError('skill_metadata_plain')
        values[key] = value
    if set(values) != {'name', 'description'} or name(values['name']) != expected_name or len(values['description'].encode()) > 1024:
        raise PluginError('skill_metadata_fields')
    return values, body


class Skill:
    def __init__(self, directory, skill_id):
        self.directory = Path(directory)
        self.id = name(skill_id)

    def metadata(self):
        """Read metadata only, one line at a time; do not load instructions."""
        try:
            fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                file_fd = os.open('SKILL.md', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            finally:
                os.close(fd)
            with os.fdopen(file_fd, 'rb') as stream:
                metadata = os.fstat(stream.fileno())
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > 4096 + 32768:
                    raise PluginError('skill_file_limit')
                lines = []
                size = 0
                for _ in range(5):
                    line = stream.readline(4097)
                    lines.append(line)
                    size += len(line)
                    if size > 4096:
                        raise PluginError('skill_metadata_limit')
                    if len(lines) > 1 and line == b'---\n':
                        break
                values, _ = _metadata(b''.join(lines), self.id)
                return dict(values, instructions_loaded=False, grants_tools=False)
        except OSError as exc:
            raise PluginError('skill_path') from exc

    def load(self, *, relevant=False):
        if relevant is not True:
            raise PluginError('skill_not_selected')
        try:
            fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            raise PluginError('skill_path') from exc
        try:
            data = _read_regular(fd, 'SKILL.md', 4096 + 32768)
            values, body = _metadata(data, self.id)
            if len(body.encode()) > 32768:
                raise PluginError('skill_body_limit')
            return dict(values, body=body, untrusted_instructions=True, grants_tools=False)
        finally:
            os.close(fd)

    def resource(self, path, *, reviewed=False):
        if reviewed is not True or not relative(path).startswith('references/'):
            raise PluginError('skill_resource_not_reviewed')
        try:
            fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            raise PluginError('skill_path') from exc
        try:
            return _read_regular(fd, path, 256 * 1024)
        finally:
            os.close(fd)
