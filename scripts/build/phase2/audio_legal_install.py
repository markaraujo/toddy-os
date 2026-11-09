#!/usr/bin/env python3
"""Add exact Pulse license texts through owned same-source metadata upgrades."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from package_copyright import write_copyright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def legal(path):return path.startswith('/usr/share/doc/pulseaudio/')
def verify(record):
    for name,row in record['payload'].items():
        path=TARGET/name.lstrip('/');st=path.lstat()
        assert st.st_mode==row['mode'] and st.st_uid==row['uid'] and st.st_gid==row['gid']
        if 'sha256' in row:assert sha(path)==row['sha256']
        elif 'symlink' in row:assert os.readlink(path)==row['symlink']
        else:assert row['directory'] and path.is_dir()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    receipt=LOG/'audio-legal-transaction.json';assert not receipt.exists(),'Inspect actual transaction; never replay'
    plan=[]
    for name,version,archive in [('pulseaudio','17.0','pulseaudio-17.0.tar.xz'),('libcanberra','0.30','libcanberra-0.30.tar.xz')]:
        oldversion=version+'-1+toddy1';newversion=version+'-1+toddy2'
        old=json.loads(Path('/var/log/toddy/packages',name+'_'+oldversion+'_amd64.json').read_text());assert old['installed']
        source=Path('/var/cache/toddy/packages',name+'_'+oldversion+'_amd64.deb');assert sha(source)==old['archive_sha256'];verify(old)
        assert subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Version}',name],text=True)==oldversion
        for folder,suffix in [('/var/cache/toddy/packages','.deb'),('/var/log/toddy/packages','.json')]:assert not Path(folder,name+'_'+newversion+'_amd64'+suffix).exists()
        stage=TARGET/'sources/stage'/('phase2-'+name+'-legal-2');assert not stage.exists()
        depends=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Depends}',name],text=True)
        plan.append((name,newversion,archive,old,source,stage,depends))
    data={'scope':'Exact full Pulse LGPL/GPL texts and legal metadata; no runtime/build/test/library change. Canberra exact dependency follows same-source Pulse metadata version.','state':'prepared','packages':[],'rollback':'Inspect receipt/dpkg and full payload first. Retained prior Canberra then Pulse archives allow restoring the paired old exact dependency versions; never replay an uncertain transaction.'}
    def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
    save()
    for name,version,archive,old,source,stage,depends in plan:
        data['state']='staging-'+name;save();stage.mkdir()
        subprocess.run(['dpkg-deb','-x',str(source),str(stage)],check=True);assert payload(stage)==old['payload']
        if name=='pulseaudio':write_copyright(stage,name,[archive])
        else:
            assert 'pulseaudio (= 17.0-1+toddy1)' in depends
            depends=depends.replace('pulseaudio (= 17.0-1+toddy1)','pulseaudio (= 17.0-1+toddy2)')
        updated=payload(stage)
        for p in set(updated)|set(old['payload']):
            if name=='pulseaudio' and legal(p):continue
            assert updated.get(p)==old['payload'].get(p),'Unexpected runtime difference '+p
        data['state']='installing-'+name;save()
        archives=[archive]+(['libcanberra-0.30-wayland-1.patch'] if name=='libcanberra' else [])
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,version,str(stage),*[a for fn in archives for a in ['--source',fn]],'--recipe','scripts/build/phase2/audio-legal-install.sh','--depends',depends,'--install'],cwd=ROOT,check=True)
        new=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text());assert new['installed'];verify(new)
        unchanged=sum(1 for p,row in old['payload'].items() if 'sha256' in row and not (name=='pulseaudio' and legal(p)))
        data['packages'].append({**{k:new[k] for k in ['name','version','archive_sha256','installed']},'old_archive_sha256':old['archive_sha256'],'old_nonlegal_regular_files_unchanged':unchanged});data['state']='installed-'+name;save()
    notice=json.loads((TARGET/'usr/share/doc/pulseaudio/source-notices/index.json').read_text())
    assert {'pulseaudio-17.0/LGPL','pulseaudio-17.0/GPL'}<={n['path'] for r in notice['sources'] for n in r['notices']}
    data['state']='complete';save()
if __name__=='__main__':main()
