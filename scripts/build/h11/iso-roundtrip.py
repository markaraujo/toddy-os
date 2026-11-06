#!/usr/bin/env python3
"""Exercise installed Xorriso only against private regular-file ISO images."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile


def run(*arguments, accepted=(0,)):
    result = subprocess.run(arguments, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=120)
    print(result.stdout, end='', flush=True)
    if result.returncode not in accepted:
        raise RuntimeError(f'{arguments[0]} exited {result.returncode}')
    return result


def snapshot(root):
    result = {}
    for path in [root, *sorted(root.rglob('*'))]:
        info = path.lstat()
        row = {'mode': stat.S_IMODE(info.st_mode), 'uid': info.st_uid,
               'gid': info.st_gid, 'mtime': int(info.st_mtime)}
        if path.is_symlink():
            row.update(type='link', target=os.readlink(path))
        elif path.is_file():
            row.update(type='file', sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        elif path.is_dir():
            row['type'] = 'directory'
        else:
            raise RuntimeError(f'Unexpected fixture object: {path}')
        row['xattrs'] = {name: os.getxattr(path, name, follow_symlinks=False).hex()
                        for name in sorted(os.listxattr(path, follow_symlinks=False))}
        result[str(path.relative_to(root))] = row
    return result


def main():
    root = Path(tempfile.mkdtemp(prefix='toddy-iso-roundtrip-'))
    print(f'Private ISO fixture: {root}', flush=True)
    try:
        source = root / 'input'
        source.mkdir(mode=0o750)
        (source / 'directory').mkdir(mode=0o751)
        payload = b''.join(hashlib.sha256(f'Toddy ISO payload {n}'.encode()).digest()
                           for n in range(128))
        (source / 'payload.bin').write_bytes(payload)
        data = source / 'directory' / 'ação\nmetadata.txt'
        data.write_text('Native ISO metadata roundtrip\n', encoding='utf-8')
        os.chown(data, 18, 18)
        os.chmod(data, 0o4750)
        os.setxattr(data, 'user.toddy', b'ISO metadata')
        run('setfacl', '-m', 'u:101:r--', str(data))
        assert stat.S_IMODE(data.stat().st_mode) == 0o4750
        assert 'system.posix_acl_access' in os.listxattr(data)
        os.link(data, source / 'hardlink')
        (source / 'relative-link').symlink_to('directory/ação\nmetadata.txt')
        for path in [source, *source.rglob('*')]:
            os.utime(path, (1793923200, 1793923200), follow_symlinks=False)
        expected = snapshot(source)
        image = root / 'probe.iso'
        common = ('xorriso', '-no_rc', '-abort_on', 'FATAL', '-return_with', 'SORRY', '32',
                  '-local_charset', 'UTF-8', '-hardlinks', 'on', '-acl', 'on',
                  '-xattr', 'on', '-md5', 'on')
        run(*common, '-outdev', 'stdio:' + str(image), '-volid', 'TODDY_PROBE',
            '-map', str(source), '/', '-commit', '-end')
        assert image.is_file() and not image.is_symlink()
        image_bytes = image.read_bytes()
        assert image_bytes[32768 + 1:32768 + 6] == b'CD001', 'Missing ISO9660 volume descriptor'
        run(*common, '-indev', 'stdio:' + str(image), '-check_md5_r', 'FAILURE', '/', '--', '-end')
        output = root / 'output'
        run(*common, '-indev', 'stdio:' + str(image), '-osirrox', 'on:check_md5_on',
            '-extract', '/', str(output), '-end')
        actual = snapshot(output)
        if expected != actual:
            raise RuntimeError('ISO metadata mismatch: ' + json.dumps({
                'expected': expected, 'actual': actual}, ensure_ascii=True))
        assert (output / 'hardlink').stat().st_ino == (output / data.relative_to(source)).stat().st_ino
        # Corrupt only one uniquely located fixture payload; preserve the original.
        assert image_bytes.count(payload) == 1, 'Payload location is ambiguous'
        offset = image_bytes.index(payload)
        changed = bytearray(image_bytes)
        changed[offset] ^= 1
        corrupt = root / 'corrupt.iso'
        corrupt.write_bytes(changed)
        rejection = run(*common, '-indev', 'stdio:' + str(corrupt),
                        '-check_md5', 'FAILURE', '/payload.bin', '--', '-end',
                        accepted=(32,))
        if 'MISMATCH' not in rejection.stdout:
            raise RuntimeError('Rejection did not identify a checksum mismatch')
        evidence = {'fixture_entries': len(expected), 'native_metadata_roundtrip': True,
                    'corrupt_payload_rejected': True, 'corrupt_exit': rejection.returncode,
                    'iso_sha256': hashlib.sha256(image_bytes).hexdigest(),
                    'iso_size': len(image_bytes), 'native_boot_validated': False,
                    'release_iso': False, 'physical_media_accessed': False}
        destination = Path('/sources/evidence/h11-libisoburn')
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'iso-roundtrip.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print(json.dumps(evidence, sort_keys=True), flush=True)
    except BaseException:
        print(f'Preserved failed ISO fixture: {root}', flush=True)
        raise
    else:
        shutil.rmtree(root)


if __name__ == '__main__':
    main()
