#!/usr/bin/env python3
"""Cache exact selected GNOME root sources; no extraction, install or upgrade.

Versions come from frozen BLFS 13.1-systemd; each official checksum document
and the matching archive are hashed. This is not a transitive build qualifier.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [('gtk', '4.22.4'), ('libadwaita', '1.9.3'), ('gdm', '50.2'),
           ('mutter', '50.4'), ('gnome-shell', '50.4'), ('gnome-session', '50.1'),
           ('gnome-control-center', '50.4'), ('gnome-settings-daemon', '50.1'),
           ('gnome-keyring', '50.0'), ('libsecret', '0.21.7'), ('nautilus', '50.2.2'),
           ('xdg-desktop-portal-gnome', '50.0'), ('gnome-text-editor', '50.1')]


def download(url, destination):
    part = destination.with_name(destination.name+'.part')
    subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                    '--connect-timeout', '15', '--max-time', '180', '--output', str(part), url], check=True)
    part.replace(destination)


def fetch(item):
    name, version = item
    series = '.'.join(version.split('.')[:2]) if int(version.split('.')[0]) < 40 else version.split('.')[0]
    filename = f'{name}-{version}.tar.xz'
    url = f'https://download.gnome.org/sources/{name}/{series}/{filename}'
    checksum_url = url.removesuffix('.tar.xz')+'.sha256sum'
    checksum = ROOT/'.local/phase2/upstream'/Path(urlparse(checksum_url).path).name
    if not checksum.exists():
        download(checksum_url, checksum)
    matches = [line.split()[0] for line in checksum.read_text().splitlines()
               if len(line.split()) == 2 and line.split()[1].lstrip('*') == filename]
    assert len(matches) == 1 and len(matches[0]) == 64, 'Exact official checksum required'
    path = ROOT/'.local/sources'/filename
    if not path.exists():
        download(url, path)
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual == matches[0], 'Source integrity mismatch; no extraction'
    return {'name': name, 'version': version, 'filename': filename, 'url': url,
            'sha256': actual, 'upstream_sha256_url': checksum_url,
            'upstream_sha256_file_sha256': hashlib.sha256(checksum.read_bytes()).hexdigest(),
            'reference': 'BLFS 13.1-systemd selected desktop roots; GNOME Text Editor50.1 approved minimal-editor candidate',
            'status': 'source_verified'}


if __name__ == '__main__':
    results, failures = {}, {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(fetch, row): row[0] for row in SOURCES}
        for future in as_completed(pending):
            name = pending[future]
            try:
                results[name] = future.result()
                print('VERIFIED', name, results[name]['sha256'], flush=True)
            except Exception as error:
                failures[name] = str(error)
                print('FAILED', name, type(error).__name__, flush=True)
    report = {'sources': [results[name] for name, _ in SOURCES if name in results],
              'failures': failures, 'scope': 'Root source integrity only; transitive dependencies/native builds pending'}
    (ROOT/'.local/phase2/upstream/gnome-roots-fetch.json').write_text(json.dumps(report, indent=2)+'\n')
    if failures:
        raise SystemExit(1)
