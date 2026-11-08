#!/usr/bin/env python3
"""Transfer one already verified model cache input to the isolated B03 guest.

No download, activation, credentials or default ISO bundling. Refuse any existing
partial/final input so interruption is reconciled before an intentional resume.
"""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile

import phase2_vm

ROOT = phase2_vm.ROOT

if __name__ == '__main__':
    model = json.loads((ROOT/'config/phase2/local-model.lock.json').read_text())['model']
    source = ROOT/'.local/models'/model['filename']
    assert source.is_file() and not source.is_symlink() and source.stat().st_size == model['bytes']
    with source.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == model['sha256']
    import os
    stat = os.statvfs(ROOT)
    assert stat.f_bavail*stat.f_frsize >= 100*1024**3+model['bytes'], 'Host free-space reserve'
    remote = '''from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,sys,tarfile
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
receipt=json.loads(Path('/var/log/toddy/build/b03-llama-cpu-install.success.json').read_text())
assert receipt['recipe_exit']==0 and receipt['postcheck_exit']==0
'''+f'model={model!r}\n'+'''
base=Path('/mnt/lfs/sources/phase2/inputs')
part=base/'.local-model-proof.part';dest=base/'local-model-proof'
work=Path('/mnt/lfs/sources/phase2/work/local-model-proof-1')
assert not part.exists() and not dest.exists() and not work.exists(), 'Inspect existing model transfer; no replay'
stat=os.statvfs(base);assert stat.f_bavail*stat.f_frsize>=16*1024**3+model['bytes']
part.mkdir(mode=0o700)
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
    member=archive.next()
    assert member and member.name=='model.gguf' and member.type==tarfile.REGTYPE and member.size==model['bytes']
    digest=hashlib.sha256();count=0
    with archive.extractfile(member) as incoming, (part/'model.gguf').open('xb') as output:
        while chunk:=incoming.read(1024*1024):
            count+=len(chunk);assert count<=model['bytes']
            digest.update(chunk);output.write(chunk)
        output.flush();os.fsync(output.fileno())
    assert archive.next() is None, 'Unexpected additional model payload'
assert count==model['bytes'] and digest.hexdigest()==model['sha256']
(part/'model-input.json').write_text(json.dumps(model,indent=2)+'\\n')
os.chmod(part/'model.gguf',0o644);os.chmod(part,0o755)
part.rename(dest);work.mkdir();os.chown(work,101,101)
print(json.dumps({'model_input':'local-model-proof','sha256':digest.hexdigest(),'bytes':count,'scope':'verified development input only; not installed/activated/inference proof'}))
'''
    command = 'python3 -c '+shlex.quote(remote)
    with (ROOT/'.local/phase2/model-input-transfer.log').open('xb') as log:
        process = subprocess.Popen(phase2_vm.ssh_args()+[command], stdin=subprocess.PIPE,
                                   stdout=log, stderr=subprocess.STDOUT)
        try:
            with tarfile.open(fileobj=process.stdin, mode='w|') as archive:
                info = tarfile.TarInfo('model.gguf')
                info.size = model['bytes']
                info.mode = 0o644
                with source.open('rb') as stream:
                    archive.addfile(info, stream)
        finally:
            process.stdin.close()
            code = process.wait()
        (ROOT/'.local/phase2/model-input-transfer.exit').write_text(str(code)+'\n')
        raise SystemExit(code)
