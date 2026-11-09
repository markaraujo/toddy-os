"""Affected original pure syntax tests; original regex driver needs native GTK."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    assert os.getuid() == 101
    root = Path('/build/affected-tests-1')
    root.mkdir()
    fixture = root / 'layout/testsuite'
    fixture.mkdir(parents=True)
    (fixture / 'data').symlink_to('/src/data', target_is_directory=True)
    (fixture.parent / 'tests').symlink_to('/src/tests', target_is_directory=True)
    before = json.loads(Path('/build/stage-results.json').read_text())
    tests = json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
    syntax = next(x for x in tests if x['name'] == 'test-syntax')
    commands = []
    commands += [(name, syntax, ['-p', '/syntax-highlighting/file.' + name])
                 for name in ['py', 'py3', 'sh', 'json', 'xml']]
    outcomes = []
    for name, original, args in commands:
        env = {**os.environ, **original['env'], 'G_TEST_SRCDIR': str(fixture),
               'LD_LIBRARY_PATH': '/build/compile/gtksourceview:/stage/usr/lib'}
        with (root / (name + '.stdout')).open('xb') as stdout, (root / (name + '.stderr')).open('xb') as stderr:
            try:
                result = subprocess.run(original['cmd'] + args, cwd='/build/compile',
                                        env=env, stdout=stdout, stderr=stderr, timeout=60)
                status = result.returncode
            except subprocess.TimeoutExpired:
                status = None
        text = (root / (name + '.stdout')).read_text()
        passed = re.findall(r'^ok\s+\d+(?:\s+.*)?$', text, re.M)
        skipped = [line for line in passed if '# SKIP' in line]
        row = {'name': name, 'exit': status, 'tap_pass_lines': passed,
               'skips': skipped, 'stdout_sha256': hashlib.sha256(text.encode()).hexdigest(),
               'stderr_sha256': hashlib.sha256((root / (name + '.stderr')).read_bytes()).hexdigest()}
        outcomes.append(row)
        (root / 'progress.json').write_text(json.dumps(outcomes, indent=2) + '\n')
        assert status == 0 and passed and not skipped, 'Preserve actual failed affected test; no timeout/skip success'
        if name != 'regex':
            assert len(passed) == 1 and '/syntax-highlighting/file.' + name in passed[0]
    changed = []
    for name, expected in before['compiled_elf_sha256'].items():
        with (Path('/build') / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                changed.append(name)
    proof = {'scope': 'One-file duplicate-name correction: native C/GI data consumers and affected original pure syntax cases; original regex driver pending native GTK; no display/editor/all-grammar acceptance',
             'outcomes': outcomes, 'changed_artifacts': changed,
             'compiled_artifacts': len(before['compiled_elf_sha256']),
             'upstream_unqualified': ['Original invalid UTF8 file.cir', 'Original known GDB grammar duplicate-name warning'],
             'native_widget_tests': 'Historical baseline evidence retained; affected product editor UI still pending'}
    (root / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert not changed


if __name__ == '__main__':
    main()
