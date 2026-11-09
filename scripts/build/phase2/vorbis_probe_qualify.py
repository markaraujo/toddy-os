"""Finish only Vorbis strict C consumer; reuse original codec roundtrips."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(probe, recipe):
    assert os.getuid()==101
    work=Path('/build');out=work/'probe-2';out.mkdir()
    assert (work/'compile/lib/.libs/libvorbis.so').is_file()
    stage=work/'stage'
    before={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    (out/'consumer.c').write_text(probe)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(out/'consumer.c'),
                    '-I/stage/usr/include','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',
                    '-lvorbisenc','-lvorbisfile','-lvorbis','-logg','-o',str(out/'consumer')],check=True)
    with (out/'consumer.log').open('xb') as log:
        result=subprocess.run([str(out/'consumer')],stdout=log,stderr=subprocess.STDOUT)
    (out/'consumer.exit').write_text(str(result.returncode)+'\n');assert result.returncode==0
    assert before=={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    summary=recipe.split("python3 - <<'PY'\n",1)[1].rsplit('\nPY',1)[0]
    subprocess.run(['python3','-c',summary],check=True)
    path=work/'test-results.json';proof=json.loads(path.read_text())
    proof['consumer_recovery']='Use documented OV_EXCLUDE_STATIC_CALLBACKS for unused header convenience definitions under strict own C consumer. No upstream/library/stage replay.'
    proof['stage_files_unchanged']=len(before)
    path.write_text(json.dumps(proof,indent=2)+'\n')
