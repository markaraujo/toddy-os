"""Expose only authenticated public source files to the unprivileged compiler."""
import hashlib
import os
from pathlib import Path
import stat


def readable_vendor(root):
    assert root.is_dir() and not root.is_symlink()
    changes=[]
    for path in sorted(root.rglob('*')):
        assert not path.is_symlink()
        mode=stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():new=mode|0o005;sha=None
        else:
            assert path.is_file()
            new=mode|0o004
            if new==mode:continue
            with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if new==mode:continue
        path.chmod(new)
        assert stat.S_IMODE(path.stat().st_mode)==new
        if sha is not None:
            with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha
        changes.append({'path':str(path.relative_to(root)),'before_mode':mode,'after_mode':new,'content_sha256':sha})
    return changes
