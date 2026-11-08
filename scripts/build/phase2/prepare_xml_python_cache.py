"""Qualify reuse of the accepted native XML compiler cache for Python only."""
import fcntl
import json
import os
from pathlib import Path
import subprocess


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt=Path('/var/log/toddy/phase2/libxml2-python-cache.json')
    assert not receipt.exists(),'Inspect receipt/mount/job before recovery; never replay preparation'
    accepted=json.loads(Path('/var/log/toddy/build/b02-libxml2-install.success.json').read_text())
    assert accepted['recipe_exit']==accepted['postcheck_exit']==0
    doxygen=json.loads(Path('/var/log/toddy/build/b02-doxygen-install.success.json').read_text())
    assert doxygen['recipe_exit']==doxygen['postcheck_exit']==0
    old=Path('/mnt/lfs/sources/phase2/work/libxml2-1/compile')
    assert old.is_dir() and old.resolve()==old and old.stat().st_uid==101
    options=json.loads((old/'meson-info/intro-buildoptions.json').read_text())
    assert next(r['value'] for r in options if r['name']=='python')=='disabled'
    work=old.parent;assert not (work/'python-binding-1').exists()
    fs=os.statvfs(work.parent);assert fs.f_bavail*fs.f_frsize>16*1024**3+256*1024**2
    r={'source_cache':str(old),'work':str(work),'optional_output':str(work/'python-binding-1'),'state':'qualified',
       'identity':{'device':old.stat().st_dev,'inode':old.stat().st_ino},
       'scope':'Same /src and /build/compile paths; optional Python target only; core ELF hashes must remain unchanged',
       'recovery':'Inspect cache identity, optional output and actual job before any action; never reconfigure or rerun an uncertain job.'}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:f.write(json.dumps(r,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();print(json.dumps(r))


if __name__=='__main__':main()
