#!/usr/bin/env python3
"""Bind selected desktop GIR inputs to frozen GI source, prepare unique work only."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import phase2_vm
ROOT=phase2_vm.ROOT
if __name__=='__main__':
    row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='gobject-introspection')
    archive=ROOT/'.local/sources'/row['filename'];assert hashlib.sha256(archive.read_bytes()).hexdigest()==row['sha256']
    with tarfile.open(archive) as source:
        hashes={name:hashlib.sha256(source.extractfile('gobject-introspection-1.86.0/gir/'+name).read()).hexdigest()
                for name in ['freetype2-2.0.gir','fontconfig-2.0.gir','libxml2-2.0.gir','cairo-1.0.gir.in']}
    remote='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'hashes={hashes!r}\nsource_sha={row["sha256"]!r}\n'+'''
base=Path('/mnt/lfs/sources/phase2');source=base/'inputs/gobject-introspection-1.86.0';work=base/'work/gi-desktop-types-1'
assert not work.exists(),'Reconcile existing preparation/job first'
for name,sha in hashes.items():assert hashlib.sha256((source/'gir'/name).read_bytes()).hexdigest()==sha
work.mkdir();os.chown(work,101,101)
receipt={'source_sha256':source_sha,'gir_inputs':hashes,'scope':'reuse authenticated immutable GI1.86.0 source; do not rebuild qualified core'}
(work/'prepared.json').write_text(json.dumps(receipt,indent=2)+'\\n')
print(json.dumps(receipt))
'''
    subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],check=True)
