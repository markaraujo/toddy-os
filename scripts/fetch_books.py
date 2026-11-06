#!/usr/bin/env python3
"""Retrieve exact book archives; verify the committed SHA-256 before unpacking."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / '.local/books'
folder.mkdir(parents=True, exist_ok=True)
lock = json.loads((ROOT / 'config/books.lock.json').read_text())
for kind in ('lfs', 'blfs'):
    book = lock[kind]
    url = book['archive_url']
    archive = folder / url.rsplit('/', 1)[-1]
    if not archive.exists():
        part = archive.with_name(archive.name + '.part')
        subprocess.run(['curl', '-fLsS', '--retry', '3', url, '-o', str(part)], check=True)
        part.replace(archive)
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != book['archive_sha256']:
        raise SystemExit(f'{kind}: frozen book checksum mismatch; not extracted')
    # Python tar's data filter rejects traversal and unsafe links/devices.
    with tarfile.open(archive) as source:
        source.extractall(folder / kind, filter='data')
    print(f'{kind}: verified and extracted at .local/books/{kind}')
