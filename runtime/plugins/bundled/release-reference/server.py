"""Local MCP release-baseline lookup. Never inspects installed packages or owner data."""
import json
from pathlib import Path
import re
import sys

VERSION = '2025-06-18'
TOOL = 'lookup-package'
records = json.loads(Path(__file__).with_name('release.json').read_text())

for line in sys.stdin:
    if len(line.encode()) > 65536:
        raise SystemExit(2)
    request = json.loads(line)
    method = request.get('method')
    if method == 'notifications/initialized':
        continue
    if method == 'initialize':
        result = {'protocolVersion': VERSION, 'capabilities': {'tools': {}},
            'serverInfo': {'name': 'toddy-release-reference', 'version': '1'}}
    elif method == 'tools/list':
        result = {'tools': [{'name': TOOL,
            'description': 'Read source/version/notices from the pinned B02 release baseline; current installed state is not queried.',
            'inputSchema': {'type': 'object', 'properties': {'package': {'type':'string'}},
                            'required': ['package'], 'additionalProperties': False}}]}
    elif method == 'tools/call':
        arguments = request['params']['arguments']
        if request['params']['name'] != TOOL or set(arguments) != {'package'} or not isinstance(arguments['package'], str) or not re.fullmatch('[a-z0-9][a-z0-9+.-]{0,127}', arguments['package']):
            raise SystemExit(2)
        record = records['components'].get(arguments['package'])
        content = {'scope': records['scope'], 'installed_status': 'not-queried',
            'release_manifest_sha256': records['source_manifest_sha256'],
            'found': record is not None, 'component': record}
        result = {'content': [{'type': 'text', 'text': json.dumps(content, ensure_ascii=False)}], 'isError': False}
    else:
        raise SystemExit(2)
    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
