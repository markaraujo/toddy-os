"""Probe an already staged binding without recompiling or rerunning48 scripts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    assert os.getuid()==101
    root=Path('/build/python-binding-1');tests=json.loads((root/'test-results.json').read_text())
    assert len(tests['upstream_python_scripts'])==48 and all(r['exit']==0 for r in tests['upstream_python_scripts'])
    cache=root/'stage/usr/lib/python3.14/site-packages/__pycache__'
    if cache.exists():
        assert {p.name for p in cache.iterdir()}=={'libxml2.cpython-314.pyc'}
        assert not cache.is_symlink() and all(p.is_file() and not p.is_symlink() for p in cache.iterdir())
        (cache/'libxml2.cpython-314.pyc').unlink();cache.rmdir()
    with (root/'consumer-5.log').open('xb') as log:
        r=subprocess.run(['python3','-c',sys.argv[1]],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root/'stage/usr/lib/python3.14/site-packages')),stdout=log,stderr=subprocess.STDOUT)
    (root/'consumer-5.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    binaries=json.loads((root/'core-before.json').read_text())
    for name,digest in binaries.items():
        with (Path('/build/compile')/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    tests['consumer']=json.loads((root/'consumer-5.log').read_text());tests['staged_consumer_exit']=0
    (root/'qualified-5.json').write_text(json.dumps(tests,indent=2)+'\n');print(json.dumps(tests))


if __name__=='__main__':main()
