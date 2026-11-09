"""Source-backed duplicate-capture reproducer; never install or edit inputs."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys


def main():
    assert os.getuid() == 101
    root = Path('/build')
    out = root / 'duplicate-diagnosis-1'
    out.mkdir()
    source = Path('/src/gtksourceview/implregex.c')
    before = {}
    for path in (root / 'compile').rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as stream:
            if stream.read(4) == b'\x7fELF':
                stream.seek(0)
                before[str(path.relative_to(root))] = hashlib.file_digest(stream, 'sha256').hexdigest()
    modified = out / 'modified/gtksourceview/implregex.c'
    modified.parent.mkdir(parents=True)
    modified.write_bytes(source.read_bytes())
    patch = out / 'correction.patch'
    patch.write_text(sys.argv[1])
    probe = out / 'probe.c'
    probe.write_text(sys.argv[2])
    commands = [
        ('apply', ['patch', '--batch', '--forward', '--fuzz=0', '-Np1', '-i', str(patch)]),
    ]
    flags = shlex.split(subprocess.check_output(
        ['pkg-config', '--cflags', '--libs', 'glib-2.0', 'libpcre2-8'], text=True))
    for name, path in [('original', source), ('corrected', modified)]:
        commands.extend([
            (name + '-compile', ['cc', '-std=gnu11', '-O2', '-Wall', '-Wextra',
                                '-I/build/compile', '-I/src/gtksourceview',
                                str(probe), str(path), '-o', str(out / name), *flags]),
            (name + '-run', [str(out / name)]),
        ])
    results = []
    for name, args in commands:
        with (out / (name + '.stdout')).open('xb') as stdout, (out / (name + '.stderr')).open('xb') as stderr:
            result = subprocess.run(args, cwd=out / 'modified', stdout=stdout, stderr=stderr)
        results.append({'name': name, 'exit': result.returncode})
        (out / 'progress.json').write_text(json.dumps(results, indent=2) + '\n')
        if name.endswith('-compile') or name == 'apply':
            assert result.returncode == 0, 'Preserve failed compilation/application; do not run missing consumer'
    changed = []
    for name, expected in before.items():
        with (root / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                changed.append(name)
    proof = {'scope': 'Real original vs locally corrected private regex consumer only; full package/syntax/native UI qualification still pending',
             'commands': results, 'compiled_artifacts': len(before), 'changed_artifacts': changed,
             'original_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
             'corrected_source_sha256': hashlib.sha256(modified.read_bytes()).hexdigest(),
             'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
             'probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest()}
    (out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert not changed
    assert results[-3]['name'] == 'original-run' and results[-3]['exit'] == 2
    assert results[-1]['name'] == 'corrected-run' and results[-1]['exit'] == 0


if __name__ == '__main__':
    main()
