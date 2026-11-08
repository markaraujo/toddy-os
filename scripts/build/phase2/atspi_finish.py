"""Recover only two missing-bus tests; retain seven passes and compiled payload."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    assert os.getuid() == 101 and not list(Path('/stage').iterdir())
    work = Path('/build')
    out = work / 'finish-4'
    out.mkdir()
    logs = work / 'compile/meson-logs'
    original_logs = work / 'finish-3'
    original = [json.loads(x) for x in (original_logs/'original-testlog.json').read_text().splitlines()]
    assert len(original) == 9
    failed = {r['name'].split(':')[-1] for r in original if r['result'] != 'OK'}
    assert failed == {'memory', 'atk-test'}
    assert 'org.a11y.Bus' in (original_logs/'original-testlog.txt').read_text()
    for name in ['testlog.json', 'testlog.txt']:
        shutil.copy2(original_logs/('original-'+name), out/('original-'+name))
    binaries = {}
    for p in (work/'compile').rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4) == b'\x7fELF':
                    f.seek(0)
                    binaries[str(p.relative_to(work/'compile'))] = hashlib.file_digest(f,'sha256').hexdigest()
    assert binaries
    previous = json.loads((work/'resume-2/binaries-before.json').read_text())
    assert all(binaries.get(k) == v for k,v in previous.items())
    (out/'binaries-before.json').write_text(json.dumps(binaries,indent=2)+'\n')
    def run(name, args):
        with (out/(name+'.log')).open('xb') as log:
            result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT)
        (out/(name+'.exit')).write_text(str(result.returncode)+'\n')
        assert result.returncode == 0, (name, result.returncode)
    run('affected-tests', ['dbus-run-session', '--', 'python3', '-c', sys.argv[1],
                           'affected-4', 'memory', 'atk-test'])
    rows = [json.loads(x) for x in (logs/'testlog.json').read_text().splitlines()]
    assert len(rows)==2 and {r['name'].split(':')[-1] for r in rows} == failed
    assert all(r['result']=='OK' and r['returncode']==0 for r in rows)
    for name in ['testlog.json','testlog.txt']:
        shutil.copy2(logs/name,out/('affected-'+name))
    original_recipe=sys.argv[2]
    marker='DESTDIR=/stage ninja -C /build/compile install\n'
    tail='set -euo pipefail\n'+marker+original_recipe.split(marker,1)[1].split("python3 - <<'PY'",1)[0]
    run('stage-consumers',['bash','-c',tail])
    for relative,digest in binaries.items():
        with (work/'compile'/relative).open('rb') as f:
            assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    passed = [r for r in original if r['result']=='OK']+rows
    result={'scope':'Native full ATK/AT-SPI core and bridge; real private D-Bus/registry fixture, not a graphical desktop or installed session',
            'upstream_drivers':[{'name':r['name'],'native_exit':r['returncode']} for r in passed],
            'reused_passed_drivers':7,'affected_private_bus_drivers':2,
            'existing_compiled_elf_files_unchanged':len(binaries),
            'resume_2_existing_elf_files_unchanged':len(previous),
            'staged_consumer_exit':0,'gi_exit':0,
            'profile':'Wayland; X11 and optional GTK2 module disabled; introspection and systemd integration enabled'}
    (work/'test-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
