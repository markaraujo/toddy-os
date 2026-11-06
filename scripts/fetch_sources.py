#!/usr/bin/env python3
"""Fetch frozen LFS sources, validate upstream MD5, then record SHA-256.

MD5 is the book's corruption check, not a modern authenticity signature.
HTTPS upstream URLs and an observed SHA-256 lock are recorded separately.
No source is extracted by this tool. An incomplete run never verifies the lock.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.local/sources'
LOCK = ROOT / 'config/sources.lock.json'


def digest(path, algorithm):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def fetch(row):
    row = row.copy()
    name = row['filename']
    if name != Path(name).name or name in ('.', '..'):
        raise ValueError(f'Unsafe filename {name}')
    target = CACHE / name
    if target.exists() and digest(target, 'md5') != row['upstream_md5']:
        raise ValueError(f'Cached upstream integrity mismatch: {name}')
    urls = [row['url']]
    if row['url'].startswith('https://ftpmirror.gnu.org/'):
        urls.append(row['url'].replace('https://ftpmirror.gnu.org/', 'https://ftp.gnu.org/gnu/'))
    # LFS's package mirror retains the exact frozen versions; never substitute versions.
    urls.append(f'https://ftp.osuosl.org/pub/lfs/lfs-packages/13.1/{name}')
    if not target.exists():
        part = target.with_name(name + '.part')
        for url in urls:
            result = subprocess.run(['curl', '-fLsS', '--connect-timeout', '20',
                '--max-time', '300', '--retry', '2', url, '-o', str(part)],
                capture_output=True, text=True)
            if result.returncode != 0:
                print(f'{name}: {urlparse(url).netloc} failed ({result.returncode})', flush=True)
                continue
            if digest(part, 'md5') != row['upstream_md5']:
                part.unlink()
                raise ValueError(f'Download integrity mismatch: {name} from {url}')
            part.replace(target)
            row['download_url'] = url
            break
        else:
            raise RuntimeError(f'No verified download: {name}')
    actual = digest(target, 'sha256')
    if row.get('sha256') and row['sha256'] != actual:
        raise ValueError(f'Frozen SHA-256 mismatch: {name}')
    row['sha256'] = actual
    print(f'VERIFIED {name} {actual}', flush=True)
    return row


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    data = json.loads(LOCK.read_text())
    rows = {r['filename']: r for r in data['packages']}
    errors = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch, row): row for row in data['packages']}
        for future in as_completed(futures):
            try:
                row = future.result()
                rows[row['filename']] = row
            except Exception as error:
                errors.append(str(error))
                print(f'ERROR: {error}', flush=True)
    data['packages'] = [rows[r['filename']] for r in data['packages']]
    data['status'] = 'verified' if not errors else 'incomplete'
    temp = LOCK.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(LOCK)
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'All {len(rows)} sources verified; nothing extracted.', flush=True)


if __name__ == '__main__':
    main()
