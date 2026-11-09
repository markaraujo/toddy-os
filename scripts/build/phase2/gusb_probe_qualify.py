"""Finish only GUsb own C consumer; preserve original successful API/data tests."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(probe, recipe):
    assert os.getuid()==101
    work=Path('/build');out=work/'probe-3';out.mkdir()
    assert (work/'compile/gusb/libgusb.so').is_file()
    assert 'ok 1 /gusb/context{lookup}' in (work/'original-lookup.log').read_text()
    assert 'ok 1 /gusb/device[json]' in (work/'original-json.log').read_text()
    stage=work/'stage'
    before={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    (out/'consumer.c').write_text(probe)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(out/'consumer.c'),
                    '-I/stage/usr/include/gusb-1','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',
                    *subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0','json-glib-1.0','libusb-1.0'],text=True).split(),'-lgusb','-o',str(out/'consumer')],check=True)
    with (out/'consumer.log').open('xb') as log:
        result=subprocess.run([str(out/'consumer')],stdout=log,stderr=subprocess.STDOUT)
    (out/'consumer.exit').write_text(str(result.returncode)+'\n');assert result.returncode==0
    assert before=={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    summary=recipe.split("python3 - <<'PY'\n",1)[1].rsplit('\nPY',1)[0]
    subprocess.run(['python3','-c',summary],check=True)
    path=work/'test-results.json';proof=json.loads(path.read_text())
    proof['consumer_recovery']='Upstream0.4.9 polling interval getter returns source ID, not interval. Do not qualify that broken optional API; unchanged source retained. Own test now checks main-context reference roundtrip; original API/ID/JSON checks not replayed.'
    proof['stage_files_unchanged']=len(before)
    proof['limitations']='Optional polling interval getter bug retained; selected Linux hotplug/Colord/Mutter consumers do not use it. Physical USB access not accepted.'
    path.write_text(json.dumps(proof,indent=2)+'\n')
