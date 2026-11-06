#!/usr/bin/env python3
"""Split versioned shared runtimes from staged GCC without changing their bytes."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def split(stage, runtime):
    if runtime.exists():
        raise ValueError('Runtime stage exists; inspect prior split before retry')
    source_notice = stage / 'usr/share/doc/gcc/copyright'
    if not source_notice.is_file() or source_notice.is_symlink():
        raise ValueError('Regular GCC copyright notice required before split')
    libraries = sorted(path for path in (stage / 'usr/lib').iterdir()
                       if re.fullmatch(r'lib[^/]+\.so\.[0-9][^/]*', path.name))
    if not any(path.name.startswith('libstdc++.so.6') for path in libraries) or not any(path.name == 'libgcc_s.so.1' for path in libraries):
        raise ValueError('Required native shared runtimes missing from staged GCC')
    records = {}
    for path in libraries:
        if path.is_symlink():
            target = path.readlink()
            if target.is_absolute() or len(target.parts) != 1:
                raise ValueError('Unexpected runtime link outside library directory')
            records[path.name] = {'symlink': str(target)}
        elif path.is_file():
            with path.open('rb') as stream:
                if stream.read(4) != b'\x7fELF':
                    raise ValueError('Versioned runtime candidate is not ELF')
                stream.seek(0)
                records[path.name] = {'sha256': hashlib.file_digest(stream, 'sha256').hexdigest()}
        else:
            raise ValueError('Unexpected special runtime candidate')
    for row in records.values():
        if 'symlink' in row and row['symlink'] not in records:
            raise ValueError('Runtime alias target would be absent from runtime package')
    destination = runtime / 'usr/lib'
    destination.mkdir(parents=True)
    for path in libraries:
        path.rename(destination / path.name)
    notice = runtime / 'usr/share/doc/gcc-runtime/copyright'
    notice.parent.mkdir(parents=True)
    shutil.copyfile(source_notice, notice)
    return records


def main():
    here = Path(__file__).resolve()
    subprocess.run(['bash', '-c', 'source "$1"; guard_target', 'guard', str(here.parents[1] / 'target.sh')], check=True)
    stage = Path('/mnt/lfs/sources/stage')
    records = split(stage / 'gcc', stage / 'gcc-runtime')
    evidence = Path('/mnt/lfs/sources/evidence/h07-gcc/runtime-split.json')
    evidence.write_text(json.dumps({'version': '16.2.0', 'libraries': records,
                        'splitter_sha256': hashlib.sha256(here.read_bytes()).hexdigest()}, indent=2) + '\n')
    print(json.dumps({'versioned_runtime_entries': len(records)}))


if __name__ == '__main__':
    main()
