"""Finish the staged Pulse client with its private staged indirect dependency."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(recipe):
    assert os.getuid()==101
    w=Path('/build');stage=w/'stage'
    before={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    rows=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
    assert len(rows)==12 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    env={**os.environ,'LD_LIBRARY_PATH':'/stage/usr/lib:/stage/usr/lib/pulseaudio'}
    with (w/'consumer-2.log').open('xb') as log:
        r=subprocess.run(['/build/consumer'],env=env,stdout=log,stderr=subprocess.STDOUT)
    (w/'consumer-2.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    assert before=={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    summary=recipe.split("python3 - <<'PY'\n",1)[1].rsplit('\nPY',1)[0]
    subprocess.run(['python3','-c',summary],check=True)
    p=w/'test-results.json';proof=json.loads(p.read_text());proof['consumer_recovery']='Explicit private staged libpulsecommon lookup; installed canonical /usr/lib/pulseaudio RUNPATH remains unchanged. No compile/upstream/stage replay.';proof['stage_files_unchanged']=len(before);p.write_text(json.dumps(proof,indent=2)+'\n')
