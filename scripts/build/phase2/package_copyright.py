"""Consolidate the exact retained upstream notices for native package metadata."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_notices import retain_source_notices


def write_copyright(stage, package, archives):
    retain_source_notices(Path('/opt/toddy-build'), Path('/mnt/lfs'), stage, package, archives)
    directory = stage/'usr/share/doc'/package
    notices = directory/'source-notices'
    index = json.loads((notices/'index.json').read_text())
    parts = [b'Exact upstream legal notices from the corresponding authenticated source archives.\n'
             b'Per-file source conditions also apply; see source-notices/index.json.\n']
    seen = set()
    for source in index['sources']:
        for notice in source['notices']:
            sha = notice['sha256']
            data = (notices/sha).read_bytes()
            assert hashlib.sha256(data).hexdigest() == sha
            if sha in seen:
                continue
            seen.add(sha)
            parts += [('\nSource: '+source['filename']+' / '+notice['path']+'\n').encode(), data, b'\n']
    assert seen, 'No upstream notice found; review before packaging'
    (directory/'copyright').write_bytes(b''.join(parts))
