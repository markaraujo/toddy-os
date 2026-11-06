#!/usr/bin/env python3
"""Hash the complete supporting recipe set, including streamed inner scripts."""
import hashlib
import json
from pathlib import Path


def recipe_set(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    files = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(root.rglob('*'))
             if path.is_file() and path.suffix in ('.py', '.sh')}
    encoded = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    return {'sha256': hashlib.sha256(encoded).hexdigest(), 'files': files}
