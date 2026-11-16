"""On-demand minimum SKILL.md parser; no YAML engine, code import or hooks.

Instruction text is data for a bounded task context, never executor policy.
Profile validation/import remains in the broker; this loader grants no tools.
"""
import os
from pathlib import Path
import stat

from .mcp import PluginError, _read_regular, name, relative


try:
    from ..broker.skill_documents import skill_metadata
except ImportError:
    from broker.skill_documents import skill_metadata


def _metadata(data, expected_name):
    try:
        return skill_metadata(data, expected_name)
    except (ValueError, UnicodeError) as exc:
        raise PluginError(str(exc)) from None


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
