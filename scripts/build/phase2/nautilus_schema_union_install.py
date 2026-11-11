"""Update only GTK's owned shared schema cache/legal metadata, without rebuilding."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
from package_copyright import write_copyright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
CACHE='usr/share/glib-2.0/schemas/gschemas.compiled'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(record):
    for name,row in record['payload'].items():
        p=TARGET/name.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid']),name
        if 'sha256' in row:assert digest(p)==row['sha256'],name
        elif 'symlink' in row:assert os.readlink(p)==row['symlink'],name
        else:assert row['directory'] and p.is_dir(),name
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    source=TARGET/'sources/phase2/inputs/nautilus-schema-union-1';work=TARGET/'sources/phase2/work/nautilus-schema-union-1'
    proof=json.loads((source/'toddy-schema-union.json').read_text());r=json.loads((work/'test-results.json').read_text())
    assert (LOG/'nautilus-schema-union-1.exit').read_text().strip()=='0'
    assert json.loads((LOG/'nautilus-schema-union-1.job.json').read_text())['command'][2:]==[str(source),str(work),'python3','-c',(ROOT/'scripts/build/phase2/schema_union_build.py').read_text()]
    assert r['compile_exit']==r['native_consumer_exit']==0 and r['inputs']==proof['inputs']
    assert r['baseline_schemas_preserved']==125 and r['baseline_keys_preserved']==1081
    assert r['total_schemas']==131 and r['total_keys']==1111
    assert r['added_schemas']==['org.gnome.nautilus','org.gnome.nautilus.compression','org.gnome.nautilus.icon-view','org.gnome.nautilus.list-view','org.gnome.nautilus.preferences','org.gnome.nautilus.window-state']
    assert digest(work/'schema-union/gschemas.compiled')==r['cache_sha256']
    directory=(TARGET/CACHE).parent
    assert {f.name:digest(f) for f in directory.iterdir() if f.name!='gschemas.compiled'}==proof['inputs']
    old=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy11_amd64.json').read_text());assert old['installed'];verify(old)
    archive=Path('/var/cache/toddy/packages/gtk_4.22.4-1+toddy11_amd64.deb')
    assert digest(archive)==proof['old_gtk_archive_sha256']==old['archive_sha256']
    assert digest(TARGET/CACHE)==r['baseline_cache_sha256']==proof['old_cache_sha256']
    assert subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Version}','gtk'],text=True)=='4.22.4-1+toddy11'
    reverse=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Package} ${Depends}\n'],text=True)
    assert 'gtk (= ' not in reverse,'Review exact reverse dependencies before native update'
    depends=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Depends}','gtk'],text=True)
    stage=TARGET/'sources/stage/phase2-gtk-nautilus-schema-union';receipt=LOG/'nautilus-schema-union-transaction-1.json'
    assert not stage.exists() and not receipt.exists()
    for suffix,base in [('.deb','/var/cache/toddy/packages'),('.json','/var/log/toddy/packages')]:
        assert not Path(base,'gtk_4.22.4-1+toddy12_amd64'+suffix).exists()
    size=sum((TARGET/name.lstrip('/')).stat().st_size for name,row in old['payload'].items() if 'sha256' in row)
    assert shutil.disk_usage(TARGET).free>16*1024**3+size+32*1024**2
    scratch=Path('/run/toddy-samba-client-1')
    backing=scratch/'gtk-nautilus-schema-promotion-1'
    assert not backing.exists() and not backing.is_symlink()
    assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','--mountpoint',str(scratch)],text=True).strip()=='tmpfs'
    assert shutil.disk_usage(scratch).free>size+128*1024**2
    data={'state':'prepared','scope':'Same-version GTK4 schema/legal-only update; all libraries/configurations/preferences unchanged. Actual Nautilus schemas plus all installed stock schema inputs, no graphical acceptance.', 'old_version':'4.22.4-1+toddy11','new_version':'4.22.4-1+toddy12','old_archive_sha256':old['archive_sha256'],'old_cache_sha256':r['baseline_cache_sha256'],'new_cache_sha256':r['cache_sha256'],'added_schemas':r['added_schemas'],'schema_inputs':proof['inputs'],'source_owners':proof['owners'],'recovery':'Inspect package/receipt/postconditions before action. Retained GTK toddy11 archive/record restores previous owned cache and metadata; installed source XML remains intact. Verify old payload. No rollback executed and no uncertain replay.'}
    def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
    save();backing.mkdir();stage.mkdir()
    subprocess.run(['mount','--bind',str(backing),str(stage)],check=True)
    subprocess.run(['dpkg-deb','-x',str(archive),str(stage)],check=True)
    assert payload(stage)==old['payload']
    shutil.copyfile(work/'schema-union/gschemas.compiled',stage/CACHE)
    archives=proof['source_archives'];write_copyright(stage,'gtk',archives)
    updated=payload(stage)
    for name in set(updated)|set(old['payload']):
        if name=='/'+CACHE or name.startswith('/usr/share/doc/gtk/'):continue
        assert updated.get(name)==old['payload'].get(name),name
    data['state']='installing';save()
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'gtk','4.22.4-1+toddy12',str(stage),*[arg for a in archives for arg in ['--source',a]],'--recipe','scripts/build/phase2/nautilus-schema-union-install.sh','--depends',depends,'--install'],cwd=ROOT,check=True)
    new=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy12_amd64.json').read_text());assert new['installed'];verify(new)
    data.update(state='complete',archive_sha256=new['archive_sha256'],old_nonlegal_entries_unchanged=sum(name!='/'+CACHE and not name.startswith('/usr/share/doc/gtk/') for name in old['payload']))
    save()
if __name__=='__main__':main()
