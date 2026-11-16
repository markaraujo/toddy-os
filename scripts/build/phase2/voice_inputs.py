"""Acquire immutable optional speech inputs; never install, infer or touch devices."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
RESERVE = 100 * 1024**3 + 512 * 1024**2


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def check_space(directory, additional, *, reserve=RESERVE):
    if shutil.disk_usage(directory).free < reserve + additional:
        raise ValueError('voice_input_reserve')


def load_lock(path=ROOT / 'runtime/voice/native-inputs.lock.json'):
    lock = json.loads(path.read_text())
    if lock['schema_version'] != 1 or lock['reserve_bytes'] != RESERVE:
        raise ValueError('voice_input_lock')
    candidates = json.loads((ROOT / 'runtime/voice/candidates.json').read_text())
    versions = {r['id']: (r['version'], r['source_commit']) for r in candidates['engines']}
    for ident, version, commit in [('whisper-cpp', '1.9.5', 'd1be6fde11ac6e0407606b4e42fe72d34add8037'),
                                  ('espeak-ng', '1.52.0', '4870adfa25b1a32b4361592f1be8a40337c58d6c')]:
        if versions[ident] != (version, commit):
            raise ValueError('voice_frozen_version_changed')
    return lock


def verify_file(path, row):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o022 or info.st_size != row['size'] or digest(path) != row['sha256']:
        raise ValueError('voice_input_integrity')


def fetch(row, directory, *, opener=urllib.request.urlopen, reserve=RESERVE):
    """HTTPS, bounded, no implicit retry, exact bytes, atomic no-clobber publication."""
    filename = row['filename']
    if Path(filename).name != filename or filename in ('', '.', '..') or not row['url'].startswith('https://'):
        raise ValueError('voice_input_record')
    target = directory / filename
    if os.path.lexists(target):
        verify_file(target, row)
        return False
    check_space(directory, row['size'], reserve=reserve)
    temporary = directory / (filename + '.partial')
    # A previous partial is deliberately retained for inspection, never resumed.
    size, h = 0, hashlib.sha256()
    with temporary.open('xb') as output:
        os.fchmod(output.fileno(), 0o600)
        with opener(row['url'], timeout=30) as response:
            if not response.geturl().startswith('https://'):
                raise ValueError('voice_input_redirect')
            while chunk := response.read(1024**2):
                size += len(chunk)
                if size > row['size']:
                    raise ValueError('voice_input_size')
                check_space(directory, len(chunk), reserve=reserve)
                output.write(chunk)
                h.update(chunk)
        output.flush()
        os.fsync(output.fileno())
    if size != row['size'] or h.hexdigest() != row['sha256']:
        raise ValueError('voice_input_integrity')
    # Never replace an input that appeared during acquisition.
    os.link(temporary, target)
    temporary.unlink()
    return True


def patch_source(kind, source):
    """Hash-bound corrections preserve read-only source and disconnected builds."""
    filename = 'cmake/deps.cmake' if kind == 'espeak-source' else 'CMakeLists.txt'
    path = source / filename
    expected = {'espeak-source': '4423d516710eacc4f9d8d1fe8090d6ddc6874452362af4374e2ff3f51a35dea5',
                'whisper-source': 'f4494d2da1353158b8a33b935abe6bbe76b8cee95d503fb16088224dd4755dcc'}[kind]
    if digest(path) != expected:
        raise ValueError('voice_source_patch_input')
    text = path.read_text()
    if kind == 'espeak-source':
        start = text.index('else()\n  FetchContent_Declare(sonic-git')
        end = text.index('endif()', start)
        text = text[:start] + 'else()\n  set(HAVE_LIBSONIC OFF)\n# Toddy: optional Sonic disabled; no configure-time network acquisition.\n' + text[end:]
    else:
        old = '${CMAKE_SOURCE_DIR}/bindings/javascript/package.json @ONLY)'
        if text.count(old) != 1:
            raise ValueError('voice_source_patch_count')
        text = text.replace(old, '${CMAKE_CURRENT_BINARY_DIR}/whisper-package.json @ONLY)')
    path.write_text(text)
    return {'path': filename, 'before_sha256': expected, 'after_sha256': digest(path)}


def validate_members(kind, members):
    if any(not PurePosixPath(m.name).parts for m in members) or len({m.name for m in members}) != len(members):
        raise ValueError('voice_archive_member')
    roots = {PurePosixPath(m.name).parts[0] for m in members}
    if len(roots) != 1 or len(members) > 10000:
        raise ValueError('voice_archive_roots')
    expanded = sum(m.size for m in members if m.isfile())
    if expanded > 128 * 1024**2:
        raise ValueError('voice_archive_expanded_limit')
    for m in members:
        name = PurePosixPath(m.name)
        if name.is_absolute() or '..' in name.parts or not (m.isfile() or m.isdir() or m.issym()):
            raise ValueError('voice_archive_member')
        if m.issym() and (kind != 'espeak-source' or str(name) != next(iter(roots)) + '/src/include/espeak/speak_lib.h' or m.linkname != '../espeak-ng/speak_lib.h'):
            raise ValueError('voice_archive_link')
    return next(iter(roots)), expanded


def prepare(kind, cache, output):
    """New unprivileged source tree only. Caller owns isolated build admission."""
    lock = load_lock()
    row = next(r for r in lock['artifacts'] if r['id'] == kind)
    archive = cache / row['filename']
    verify_file(archive, row)
    if os.path.lexists(output):
        raise ValueError('voice_source_already_exists')
    with tarfile.open(archive) as bundle:
        members = bundle.getmembers()
        archive_root, expanded = validate_members(kind, members)
        check_space(output.parent, expanded)
        output.mkdir(mode=0o700)
        bundle.extractall(output, filter='data')
    source = output / archive_root
    correction = patch_source(kind, source)
    recipe = ROOT / 'scripts/build/phase2' / ('voice-espeak-build.sh' if kind == 'espeak-source' else 'voice-whisper-build.sh')
    shutil.copyfile(recipe, source / 'toddy-build.sh')
    receipt = {'scope': 'Prepared source only; not compiled, packaged or native qualified',
               'input': row, 'expanded_bytes': expanded, 'correction': correction,
               'recipe_sha256': digest(recipe)}
    (output / 'prepared.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('verify', 'fetch', 'prepare'))
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--kind', choices=('espeak-source', 'whisper-source'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    cache = args.cache
    if not cache.is_absolute() or cache.resolve() != cache or not cache.is_dir():
        parser.error('cache must be an existing canonical directory')
    lock = load_lock()
    with (cache / '.acquire.lock').open('a') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.command == 'prepare':
            if args.kind is None or args.output is None or not args.output.is_absolute() or args.output.parent.resolve() != args.output.parent:
                parser.error('prepare requires --kind and new canonical --output')
            print(prepare(args.kind, cache, args.output))
            return
        rows = lock['artifacts']
        if args.command == 'fetch':
            check_space(cache, sum(r['size'] for r in rows if not os.path.lexists(cache / r['filename'])))
        acquired = 0
        for row in rows:
            if args.command == 'fetch' and fetch(row, cache):
                acquired += row['size']
            verify_file(cache / row['filename'], row)
        print(json.dumps({'scope': 'Exact optional input bytes only; no native/audio acceptance',
                          'verified_bytes': sum(r['size'] for r in rows), 'new_bytes': acquired,
                          'free_bytes': shutil.disk_usage(cache).free, 'reserve_bytes': RESERVE}))

if __name__ == '__main__':
    main()
