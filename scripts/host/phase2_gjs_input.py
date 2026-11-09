#!/usr/bin/env python3
"""Prepare frozen GJS only after the installed security engine is verified."""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import phase2_vm

ROOT = phase2_vm.ROOT


def main():
    assert shutil.disk_usage(ROOT).free >= 100 * 1024**3
    row = next(x for x in json.loads((ROOT / 'config/phase2/sources.lock.json').read_text())['components'] if x['name'] == 'gjs')
    assert row['version'] == '1.88.1' and row['sha256'] == '767bab80e665d672cb00563c25f0b392a9ec8c2996ed1d4454c698b4c2f0a3d9'
    archive = ROOT / '.local/sources' / row['filename']
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256']
    files = {name: (ROOT / 'scripts/build/phase2' / canonical).read_text() for name, canonical in
             [('toddy-build.sh', 'gjs-build.sh'), ('toddy-probe.c', 'gjs-probe.c'), ('toddy-probe.py', 'gjs_probe.py')]}
    code = r'''from pathlib import Path
import fcntl,hashlib,json,os,shutil,socket,subprocess,sys,time
assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
''' + f'row={row!r}\nfiles={files!r}\n' + r'''
proof=json.loads(Path('/var/log/toddy/build/b02-mozjs-install.success.json').read_text())
assert proof['recipe_exit']==proof['postcheck_exit']==0,'Verified installed engine required'
assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','mozjs'],text=True)=='install ok installed 140.17.0-1+toddy1'
source=Path('/mnt/lfs/sources/phase2/inputs/gjs-1.88.1');work=Path('/mnt/lfs/sources/phase2/work/gjs-1')
receipt=Path('/var/log/toddy/phase2/gjs-input-1.json')
assert not source.exists() and not work.exists() and not receipt.exists(),'Reconcile existing operation, never replay'
budget=512*1024**2;free=shutil.disk_usage('/mnt/lfs').free
assert free>=16*1024**3+budget,'GJS512MiB additional budget above16GiB reserve unavailable; no mutation'
data=sys.stdin.buffer.read();assert hashlib.sha256(data).hexdigest()==row['sha256']
archive=Path('/mnt/lfs/sources')/row['filename'];part=archive.with_name(archive.name+'.part');assert not part.exists()
if archive.exists():
 with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
else:
 with part.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 part.replace(archive)
state={'state':'extracting','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'source':str(source),'work':str(work),'source_sha256':row['sha256'],'started_unix':time.time(),'free_bytes_before':free,'additional_budget_bytes':budget}
def save():
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
save();source.mkdir()
subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['filename']],cwd=source,check=True)
inner=source/'gjs-1.88.1';assert inner.is_dir() and not inner.is_symlink()
for p in list(inner.iterdir()):p.rename(source/p.name)
inner.rmdir()
assert (source/'subprojects/gobject-introspection-tests/meson.build').is_file(),'Use authenticated vendored tests, no network fallback'
for name,text in files.items():(source/name).write_text(text)
prepared={'source_sha256':row['sha256'],'reference':row['reference'],'book_page_sha256':row['book_page_sha256'],'source_patches':[],'files_sha256':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()},'engine':'Owned/verified140.17.0 security overlay, ADR0147; foundation toolchain unchanged','native_gui_tests':'pending actual compositor; do not claim from C/CLI tests'}
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
work.mkdir();os.chown(work,101,101);state.update(state='complete',prepared=prepared);save();print(json.dumps({'state':'complete','source':str(source),'work':str(work)}))
'''
    compile(code, 'gjs-input', 'exec')
    subprocess.run(phase2_vm.ssh_args() + ['python3 -c ' + shlex.quote(code)], input=archive.read_bytes(), check=True)


if __name__ == '__main__':
    main()
