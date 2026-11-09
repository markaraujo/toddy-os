"""Qualify the corrected consumer against preserved libinput build/test/stage."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(probe):
    assert os.getuid()==101
    work=Path('/build');out=work/'probe-2';out.mkdir()
    stage=work/'stage'
    before={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
    assert len(rows)==10 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    (out/'consumer.c').write_text(probe)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(out/'consumer.c'),
                    '-I/stage/usr/include','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',
                    '-linput','-o',str(out/'consumer')],check=True)
    with (out/'consumer.log').open('xb') as log:
        result=subprocess.run([str(out/'consumer')],stdout=log,stderr=subprocess.STDOUT)
    (out/'consumer.exit').write_text(str(result.returncode)+'\n');assert result.returncode==0
    assert before=={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    registered=json.loads((work/'compile/meson-info/intro-tests.json').read_text())
    (work/'test-results.json').write_text(json.dumps({
        'scope':'Native portable libinput tests/API only; no device events, graphical input, tablet or physical acceptance',
        'selected_drivers':[{'name':r['name'],'result':r['result'],'exit':r['returncode']} for r in rows],
        'hardware_drivers_not_selected':[r['name'] for r in registered if any(s.endswith(':hardware') or s=='hardware' for s in r['suite'])],
        'staged_consumer_exit':0,'stage_files_unchanged':len(before),
        'private_check_sdk':'Reused qualified Check0.15.2, not installed',
        'profile':{'mtdev':True,'libwacom':False,'lua_plugins':False,'internal_event_debugging':False,'debug_gui':False},
        'consumer_recovery':'Original absent-path assertion failed before open callback; frozen source validates udev path first. Probe-only correction, original ten passing drivers/build/stage retained.',
        'limitations':'Hardware suites not selected; libwacom tablet identification and optional Lua plugins unavailable'
    },indent=2)+'\n')
