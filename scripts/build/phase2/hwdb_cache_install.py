#!/usr/bin/env python3
"""Own the qualified shared hwdb cache with unchanged native Systemd binaries."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from package_copyright import write_copyright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def legal(p):return p.startswith('/usr/share/doc/systemd/')
def verify(old):
    for name,row in old['payload'].items():
        p=TARGET/name.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid'])
        if 'sha256' in row:assert sha(p)==row['sha256']
        elif 'symlink' in row:assert os.readlink(p)==row['symlink']
        else:assert row['directory'] and p.is_dir()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    assert (LOG/'hwdb-cache-probe-2.exit').read_text().strip()=='0'
    work=TARGET/'sources/phase2/work/hwdb-cache-1';proof=json.loads((work/'test-results.json').read_text());assert proof['native_consumer_exit']==0
    recipe=(ROOT/'scripts/build/phase2/hwdb_cache_build.py').read_text()
    initial=json.loads((LOG/'hwdb-cache-1.job.json').read_text());expected=proof['input_sha256']
    assert initial['command'][-3:]==['python3','-c',recipe.replace('acpi:__TODDY_INVALID_PNP__:','acpi:ZZZ_INVALID_TODDY:')+'\nmain('+repr(expected)+')\n']
    code=(ROOT/'scripts/build/phase2/hwdb_cache_finish.py').read_text()+'\nmain('+repr(recipe)+')\n'
    assert json.loads((LOG/'hwdb-cache-probe-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
    assert {p.name:sha(p) for p in (TARGET/'usr/lib/udev/hwdb.d').glob('*.hwdb')}==expected
    assert not list((TARGET/'etc/udev/hwdb.d').iterdir())
    assert not (TARGET/'etc/udev/hwdb.bin').exists() and not (TARGET/'usr/lib/udev/hwdb.bin').exists()
    cache=work/'stage/usr/lib/udev/hwdb.bin';assert sha(cache)==proof['cache_sha256']
    old=json.loads(Path('/var/log/toddy/packages/systemd_261.2-1+toddy1_amd64.json').read_text());assert old['installed'];verify(old)
    archive=Path('/var/cache/toddy/packages/systemd_261.2-1+toddy1_amd64.deb');assert sha(archive)==old['archive_sha256']
    assert subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Version}','systemd'],text=True)=='261.2-1+toddy1'
    depends=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Depends}','systemd'],text=True)
    all_depends=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Package} ${Depends}\n'],text=True);assert 'systemd (= ' not in all_depends
    stage=TARGET/'sources/stage/phase2-systemd-hwdb';receipt=LOG/'hwdb-cache-transaction.json'
    assert not stage.exists() and not receipt.exists()
    for folder,suffix in [('/var/cache/toddy/packages','.deb'),('/var/log/toddy/packages','.json')]:assert not Path(folder,'systemd_261.2-1+toddy2_amd64'+suffix).exists()
    data={'scope':'Same-version Systemd shared hwdb/legal metadata only; existing source/binaries/services/configurations unchanged, no foundation rebuild or hardware claim','state':'prepared','cache_sha256':proof['cache_sha256'],'input_sha256':expected,'old_archive_sha256':old['archive_sha256'],'rollback':'Inspect receipt/dpkg first. Retained original Systemd toddy1 archive/record restore previous owned payload; remove only the newly owned cache after verifying prior absence and current owner, then verify exact original payload. Never replay an uncertain transaction.'}
    def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
    save();stage.mkdir();subprocess.run(['dpkg-deb','-x',str(archive),str(stage)],check=True);assert payload(stage)==old['payload']
    shutil.copyfile(cache,stage/'usr/lib/udev/hwdb.bin');(stage/'usr/lib/udev/hwdb.bin').chmod(0o644)
    archives=[r['filename'] for r in old['sources']]+['libwacom-2.19.1.tar.xz'];write_copyright(stage,'systemd',archives)
    updated=payload(stage)
    for p in set(updated)|set(old['payload']):
        if p=='/usr/lib/udev/hwdb.bin' or legal(p):continue
        assert updated.get(p)==old['payload'].get(p),'Unexpected old runtime change '+p
    data['state']='installing';save()
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'systemd','261.2-1+toddy2',str(stage),*[a for fn in archives for a in ['--source',fn]],'--recipe','scripts/build/phase2/hwdb-cache-install.sh','--depends',depends,'--install'],cwd=ROOT,check=True)
    new=json.loads(Path('/var/log/toddy/packages/systemd_261.2-1+toddy2_amd64.json').read_text());assert new['installed'];verify(new)
    data['package']={k:new[k] for k in ['name','version','archive_sha256']};data['old_nonlegal_regular_files_unchanged']=sum(1 for p,row in old['payload'].items() if 'sha256' in row and not legal(p));data['state']='complete';save()
if __name__=='__main__':main()
