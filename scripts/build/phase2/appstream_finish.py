"""Qualify the actual eight successful drivers and preserved staged consumers."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    assert os.getuid()==101
    work=Path('/build');out=work/'probe-4';out.mkdir()
    rows=[json.loads(l) for l in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()]
    assert len(rows)==8 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    binaries={}
    for p in (work/'compile').rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4)==b'\x7fELF':
                    f.seek(0);binaries[str(p.relative_to(work/'compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
    def stage():
        result={}
        for p in Path('/stage').rglob('*'):
            key=str(p.relative_to('/stage'));st=p.lstat();r={'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid}
            if p.is_symlink():r['link']=str(p.readlink())
            elif p.is_file():
                with p.open('rb') as f:r['sha256']=hashlib.file_digest(f,'sha256').hexdigest()
            result[key]=r
        return result
    before=stage();assert binaries and before
    (out/'binaries-before.json').write_text(json.dumps(binaries,indent=2)+'\n')
    (out/'stage-before.json').write_text(json.dumps(before,indent=2)+'\n')
    def run(name,args,env=None):
        with (out/(name+'.log')).open('xb') as log:r=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,env=env)
        (out/(name+'.exit')).write_text(str(r.returncode)+'\n');assert r.returncode==0
    run('consumer',['/build/native-metadata'])
    run('gi',['python3','-B','-c',"import gi;gi.require_version('AppStream','1.0');from gi.repository import AppStream;c=AppStream.Component.new();c.set_id('org.toddy.NativeProbe');assert c.get_id()=='org.toddy.NativeProbe'"],dict(os.environ,GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0',LD_LIBRARY_PATH='/stage/usr/lib'))
    assert stage()==before
    for relative,digest in binaries.items():
        with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    result={'scope':'Native core metadata bootstrap/API/GI, not graphical or application catalog acceptance',
        'upstream_drivers':[{'name':r['name'],'native_exit':r['returncode']} for r in rows],
        'existing_compiled_elf_files_unchanged':len(binaries),'stage_entries_unchanged':len(before),'staged_consumer_exit':0,'gi_exit':0,
        'limitations':'Compose, stemming, systemd hooks, Qt, shell completions and Debian APT integration disabled in bootstrap profile'}
    (work/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
