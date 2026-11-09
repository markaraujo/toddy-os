"""Probe-only POSIX declaration correction; preserve original ALSA build/tests."""
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
    for name in ['config','midi_event']:
        text=(work/('compile/test/lsb/'+name+'.trs')).read_text()
        assert ':test-result: PASS' in text and ':test-result: FAIL' not in text
    (out/'consumer.c').write_text(probe)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(out/'consumer.c'),
                    '-I/stage/usr/include','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',
                    '-lasound','-o',str(out/'consumer')],check=True)
    with (out/'consumer.log').open('xb') as log:
        result=subprocess.run([str(out/'consumer')],env=dict(os.environ,ALSA_PLUGIN_DIR='/stage/usr/lib/alsa-lib'),stdout=log,stderr=subprocess.STDOUT)
    (out/'consumer.exit').write_text(str(result.returncode)+'\n');assert result.returncode==0
    assert before=={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    (work/'test-results.json').write_text(json.dumps({
        'scope':'Native ALSA configuration and null PCM API; no audible/physical or Pipewire/GNOME acceptance',
        'upstream_check_exit':0,'upstream_lsb_tests':[{'name':n,'result':'PASS'} for n in ['config','midi_event']],
        'upstream_examples':'Original manual/hardware examples compiled, not exercised/countable as passes',
        'staged_consumer_exit':0,'stage_files_unchanged':len(before),
        'consumer_recovery':'POSIX_C_SOURCE200809L declared before ALSA includes for strict C11; no library/test/assertion changes',
        'profile':'Shared libasound/topology/default source configuration; no user preference edits or physical hardware claim'
    },indent=2)+'\n')
