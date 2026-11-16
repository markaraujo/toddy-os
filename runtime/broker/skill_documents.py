"""Pure bounded data-only skill/profile path contract; never executes resources."""
import re

BASE_FILES = {'config.json','SOUL.md','IDENTITY.md','USER.md','AGENTS.md'}
ID = re.compile(r'[a-z][a-z0-9-]{0,63}\Z')
SEGMENT = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')


def profile_path(path):
    if path in BASE_FILES:
        return (65536 if path == 'config.json' else 32768), None
    if not isinstance(path, str) or len(path) > 256:
        raise ValueError('unsupported_profile_path')
    parts = path.split('/')
    if not 3 <= len(parts) <= 8 or parts[0] != 'skills' or not ID.fullmatch(parts[1]):
        raise ValueError('unsupported_profile_path')
    if parts[2:] == ['SKILL.md']:
        return 4096 + 32768, parts[1]
    if parts[2] != 'references' or len(parts) < 4 or any(not SEGMENT.fullmatch(p) for p in parts[3:]):
        raise ValueError('unsupported_profile_path')
    return 256 * 1024, parts[1]


def skill_metadata(data, expected_name):
    text = data.decode('utf-8', errors='strict')
    if not text.startswith('---\n') or '\n---\n' not in text:
        raise ValueError('skill_metadata')
    front, _, body = text[4:].partition('\n---\n')
    if len(front.encode()) > 4096:
        raise ValueError('skill_metadata_limit')
    values = {}
    for line in front.splitlines():
        key, sep, value = line.partition(': ')
        if not sep or key not in ('name','description') or key in values or not value:
            raise ValueError('skill_metadata_fields')
        if value.startswith(('!','&','*','{','[','|','>','"',"'")) or '\x00' in value:
            raise ValueError('skill_metadata_plain')
        values[key] = value
    if set(values) != {'name','description'} or not ID.fullmatch(values['name']) or values['name'] != expected_name or len(values['description'].encode()) > 1024:
        raise ValueError('skill_metadata_fields')
    return values, body


def parse_skill(data, expected_name):
    if type(data) is not bytes or len(data) > 4096 + 32768:
        raise ValueError('skill_file_limit')
    values, body = skill_metadata(data, expected_name)
    if len(body.encode()) > 32768:
        raise ValueError('skill_body_limit')
    return dict(values, body=body, untrusted_instructions=True, grants_tools=False)
