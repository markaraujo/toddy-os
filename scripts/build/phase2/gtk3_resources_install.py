"""Own GTK3 resources and upgrade only GTK4's shared schema/legal metadata."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from package_copyright import write_copyright
from verify_stage import inspect_stage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
CACHE='usr/share/glib-2.0/schemas/gschemas.compiled'
IMCACHE='usr/lib/gtk-3.0/3.0.0/immodules.cache'


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def legal(p):
    return p=='/usr/share/doc/gtk' or p.startswith('/usr/share/doc/gtk/')


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    assert os.statvfs(TARGET).f_bavail*os.statvfs(TARGET).f_frsize>=16*1024**3+256*1024**2
    source=TARGET/'sources/phase2/inputs/gtk3-resources-1'
    work=TARGET/'sources/phase2/work/gtk3-resources-1'
    gtk_source=TARGET/'sources/phase2/inputs/gtk-3.24.52'
    gtk_work=TARGET/'sources/phase2/work/gtk3-1'
    for name in ['gtk3-1','gtk3-resources-recovery-2']:
        assert (LOG/(name+'.exit')).read_text().strip()=='0'
        job=json.loads((LOG/(name+'.job.json')).read_text())
        assert job['harness_sha256']==sha(ROOT/'scripts/build/phase2/isolated.sh')
    assert (gtk_source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/gtk3-build.sh').read_bytes()
    assert (gtk_source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/gtk3-probe.c').read_bytes()
    native=json.loads((gtk_work/'test-results.json').read_text())
    assert native['original_rgba_cases']==4 and native['staged_consumer_exit']==native['gi_exit']==0
    code=(ROOT/'scripts/build/phase2/gtk3_resources_recover.py').read_text()+'\nmain('+repr((ROOT/'scripts/build/phase2/gtk3_resources_build.py').read_text())+')\n'
    assert json.loads((LOG/'gtk3-resources-recovery-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
    frozen=json.loads((source/'toddy-resources.json').read_text())
    assert sha(source/'toddy-build.py')==frozen['recipe_sha256']
    assert inspect_stage(gtk_work/'stage')==inspect_stage(source/'gtk3-stage')==frozen['gtk3_stage']
    proof=json.loads((work/'test-results.json').read_text())
    assert proof['schema_exit']==proof['immodules_query_exit']==0
    assert (proof['baseline_fixed'],proof['baseline_relocatable'],proof['union_fixed'],proof['union_relocatable'])==(52,6,56,6)
    assert sha(work/'schema-union/gschemas.compiled')==proof['schema_cache_sha256']
    assert sha(work/'immodules.cache')==proof['immodules_cache_sha256']
    assert len(proof['immodules'])==11
    for p,h in proof['immodules'].items():assert sha(gtk_work/'stage'/p)==h
    old=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy2_amd64.json').read_text())
    assert old['installed'] and old['archive_sha256']==frozen['old_gtk_archive_sha256']
    assert sha(Path('/var/cache/toddy/packages/gtk_4.22.4-1+toddy2_amd64.deb'))==old['archive_sha256']
    status=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Version}','gtk'],text=True)
    assert status=='4.22.4-1+toddy2'
    state=subprocess.run(['chroot',str(TARGET),'dpkg-query','-W','-f=${Status}','gtk3'],capture_output=True,text=True)
    assert state.returncode in (0,1) and state.stdout.strip()!='install ok installed'
    # A metadata-only upgrade must never restore a changed runtime/user path.
    for name,row in old['payload'].items():
        path=TARGET/name.lstrip('/');st=path.lstat()
        assert st.st_mode==row['mode'] and st.st_uid==row['uid'] and st.st_gid==row['gid']
        if 'sha256' in row:assert path.is_file() and not path.is_symlink() and sha(path)==row['sha256']
        elif 'symlink' in row:assert path.is_symlink() and os.readlink(path)==row['symlink']
        else:assert row['directory'] and path.is_dir()
    assert sha(TARGET/CACHE)==frozen['old_cache_sha256']==old['payload']['/'+CACHE]['sha256']
    actual={p.name:sha(p) for p in (TARGET/Path(CACHE).parent).iterdir() if p.is_file() and p.name!='gschemas.compiled'}
    assert actual==frozen['stock_inputs']
    gtk3=TARGET/'sources/stage/phase2-gtk3-resources'
    gtk4=TARGET/'sources/stage/phase2-gtk-gtk3-schemas'
    receipt_path=LOG/'gtk3-resources-transaction.json'
    assert not any(p.exists() for p in [gtk3,gtk4,receipt_path]), 'Inspect prior transaction; never replay'
    for name in ['gtk3_3.24.52-1+toddy1','gtk_4.22.4-1+toddy3']:
        assert not Path('/var/cache/toddy/packages',name+'_amd64.deb').exists()
        assert not Path('/var/log/toddy/packages',name+'_amd64.json').exists()
    shutil.copytree(gtk_work/'stage',gtk3,symlinks=True)
    assert inspect_stage(gtk3)==frozen['gtk3_stage']
    assert sha(gtk3/CACHE)==native['schema_cache_sha256']
    (gtk3/CACHE).unlink()
    assert not (gtk3/IMCACHE).exists()
    shutil.copy2(work/'immodules.cache',gtk3/IMCACHE)
    write_copyright(gtk3,'gtk3',['gtk-3.24.52.tar.xz'])
    old_stage=TARGET/'sources/stage/phase2-gtk-desktop-schemas'
    shutil.copytree(old_stage,gtk4,symlinks=True,ignore=shutil.ignore_patterns('DEBIAN'))
    assert payload(gtk4)==old['payload']
    shutil.copy2(work/'schema-union/gschemas.compiled',gtk4/CACHE)
    archives=['gtk-4.22.4.tar.xz','gsettings-desktop-schemas-50.1.tar.xz','gtk-3.24.52.tar.xz']
    write_copyright(gtk4,'gtk',archives)
    revised=payload(gtk4)
    for p in set(old['payload'])|set(revised):
        if p=='/'+CACHE or legal(p):continue
        assert old['payload'].get(p)==revised.get(p), 'Unexpected GTK4 runtime change: '+p
    receipt={'scope':'GTK3 new owned runtime/IM cache and same-owner GTK4 schema/legal-only upgrade; no GTK4 library rebuild or user preferences',
             'state':'prepared','packages':[],'old_gtk_archive_sha256':old['archive_sha256'],
             'old_cache_sha256':frozen['old_cache_sha256'],'new_cache_sha256':proof['schema_cache_sha256'],
             'schema_inputs':proof['schema_inputs'],'gtk4_other_runtime_unchanged':True,
             'previous_gtk3_absent':True,
             'rollback':'Inspect actual dpkg/receipt first. Full rollback restores retained verified GTK4 toddy2 archive (dropping the GTK3 dependency), then removes only the new owned GTK3 package and verifies original schema inputs/cache. Never replay an uncertain step.',
             'immodules_cache_sha256':proof['immodules_cache_sha256']}
    def save():receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    save()
    def package(name,version,stage,inputs,depends):
        receipt['state']='installing-'+name;save()
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,version,str(stage),
            *[a for filename in inputs for a in ['--source',filename]],
            '--recipe','scripts/build/phase2/gtk3-resources-install.sh','--depends',depends,'--install'],cwd=ROOT,check=True)
        record=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text())
        assert record['installed']
        receipt['packages'].append({k:record[k] for k in ['name','version','archive_sha256','installed']})
        receipt['state']='installed-'+name;save()
    gtk3_deps='glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), at-spi2-core (= 2.60.6-1+toddy1), pango (= 1.58.2-1+toddy1), cairo (>= 1.18.4-1+toddy1), gdk-pixbuf (= 2.44.7-1+toddy2), libepoxy (= 1.5.10-1+toddy1), wayland (>= 1.26.0-1+toddy1), libxkbcommon (= 1.13.2-1+toddy1), gsettings-desktop-schemas (= 50.1-1+toddy1)'
    gtk4_deps=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Depends}','gtk'],text=True)
    package('gtk3','3.24.52-1+toddy1',gtk3,['gtk-3.24.52.tar.xz'],gtk3_deps)
    actual={p.name:sha(p) for p in (TARGET/Path(CACHE).parent).iterdir() if p.is_file() and p.name!='gschemas.compiled'}
    assert actual==proof['schema_inputs'], 'Installed schema inputs differ from qualified private union'
    package('gtk','4.22.4-1+toddy3',gtk4,archives,gtk4_deps+', gtk3 (= 3.24.52-1+toddy1)')
    assert sha(TARGET/CACHE)==proof['schema_cache_sha256']
    assert sha(TARGET/IMCACHE)==proof['immodules_cache_sha256']
    receipt['state']='complete';save()


if __name__=='__main__':main()
