#!/usr/bin/env python3
"""Fetch the pinned disposable build-host image, never a Toddy OS image."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
lock = json.loads((ROOT / 'config/build-host.lock.json').read_text())
folder = ROOT / '.local/vm'
folder.mkdir(parents=True, exist_ok=True, mode=0o700)
image = folder / 'builder-base.img'
if not image.exists():
    part = image.with_suffix('.img.part')
    subprocess.run(['curl', '-fLsS', '--retry', '3', lock['image_url'], '-o', str(part)], check=True)
    with part.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != lock['image_sha256']:
        raise SystemExit('Build-host image mismatch; partial file retained, not usable')
    part.replace(image)
with image.open('rb') as stream:
    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
if actual != lock['image_sha256']:
    raise SystemExit('Build-host image mismatch; not usable')
subprocess.run(['curl', '-fLsS', '--retry', '3', lock['checksums_url'],
                '-o', str(folder / 'SHA256SUMS')], check=True)
print(f'Build-host image verified: {actual}')
