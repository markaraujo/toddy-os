#!/usr/bin/env python3
"""Install qualified Mutter and update only its existing shared schema cache owner."""
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
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2');CACHE='usr/share/glib-2.0/schemas/gschemas.compiled'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def legal(p):return p.startswith('/usr/share/doc/gtk/')
def verify(record):
    for name,row in record['payload'].items():
        p=TARGET/name.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid'])
        if 'sha256' in row:assert sha(p)==row['sha256']
        elif 'symlink' in row:assert os.readlink(p)==row['symlink']
        else:assert row['directory'] and p.is_dir()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    work=TARGET/'sources/phase2/work/mutter-1';source=TARGET/'sources/phase2/inputs/mutter-50.4'
    assert (LOG/'mutter-resume-2.exit').read_text().strip()=='0' and (LOG/'mutter-schemas-4.exit').read_text().strip()=='0'
    recipe=(ROOT/'scripts/build/phase2/mutter-build.sh').read_text();assert (source/'toddy-build.sh').read_text()==recipe
    code=(ROOT/'scripts/build/phase2/mutter_resume.py').read_text()+'\nmain('+repr(recipe)+')\n'
    assert json.loads((LOG/'mutter-resume-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
    code=(ROOT/'scripts/build/phase2/mutter_schema_qualify.py').read_text()+'\nmain()\n'
    assert json.loads((LOG/'mutter-schemas-4.job.json').read_text())['command'][-3:]==['python3','-c',code]
    native=json.loads((work/'test-results.json').read_text());proof=json.loads((work/'schema-qualification.json').read_text())
    assert native['staged_cli_exit']==native['staged_gi_exit']==proof['native_exit']==0
    assert sum(r['passed_cases'] for r in native['original_mtk_drivers'])==15
    assert len(proof['new_schemas'])==5 and proof['new_default_values_checked']==39
    assert proof['pending_stock_schemas']==['org.freedesktop.ColorHelper']
    assert sha(work/'schema-union/gschemas.compiled')==proof['union_cache_sha256']==native['schema_cache_sha256']
    old=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy3_amd64.json').read_text());assert old['installed'];verify(old)
    archive=Path('/var/cache/toddy/packages/gtk_4.22.4-1+toddy3_amd64.deb');assert sha(archive)==old['archive_sha256']
    assert sha(TARGET/CACHE)==proof['baseline_cache_sha256']==old['payload']['/'+CACHE]['sha256']
    base=TARGET/Path(CACHE).parent
    assert {p.name:sha(p) for p in base.iterdir() if p.name!='gschemas.compiled'}==proof['baseline_inputs']
    state=subprocess.run(['chroot',str(TARGET),'dpkg-query','-W','-f=${Status}','mutter'],capture_output=True,text=True)
    assert state.returncode in (0,1) and state.stdout.strip()!='install ok installed'
    before=inspect_stage(work/'stage');assert 'usr/bin/mutter' in before['entries'] and CACHE not in before['entries']
    mutter=TARGET/'sources/stage/phase2-mutter-resources';gtk=TARGET/'sources/stage/phase2-gtk-mutter-schemas';receipt=LOG/'mutter-resources-transaction.json'
    assert not any(p.exists() for p in [mutter,gtk,receipt]),'Inspect actual prior transaction; never replay'
    for name in ['mutter_50.4-1+toddy1','gtk_4.22.4-1+toddy4']:
        assert not Path('/var/cache/toddy/packages',name+'_amd64.deb').exists()
        assert not Path('/var/log/toddy/packages',name+'_amd64.json').exists()
    deps=[]
    names=['glibc','glib','graphene','glycin','cairo','pixman','gsettings-desktop-schemas','libxkbcommon','at-spi2-core','colord','lcms2','libei','libdisplay-info','libdrm','pango','harfbuzz','fribidi','fontconfig','freetype','gnome-desktop','libcanberra','mesa','wayland','libgudev','libinput','libwacom','pipewire','gobject-introspection','gi-gl-types','python','pygobject']
    for name in names:
        version=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Version}',name],text=True);assert version and '\n' not in version
        deps.append(name+' (= '+version+')')
    deps+=['gtk (>= 4.22.4-1+toddy3)','systemd (>= 261.2-1+toddy2)']
    gtk_deps=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Depends}','gtk'],text=True)
    shutil.copytree(work/'stage',mutter,symlinks=True);assert inspect_stage(mutter)==before
    write_copyright(mutter,'mutter',['mutter-50.4.tar.xz'])
    gtk.mkdir();subprocess.run(['dpkg-deb','-x',str(archive),str(gtk)],check=True);assert payload(gtk)==old['payload']
    shutil.copyfile(work/'schema-union/gschemas.compiled',gtk/CACHE)
    archives=[r['filename'] for r in old['sources']]+['colord-1.4.8.tar.xz','mutter-50.4.tar.xz'];assert len(archives)==len(set(archives))
    write_copyright(gtk,'gtk',archives);revised=payload(gtk)
    for p in set(old['payload'])|set(revised):
        if p=='/'+CACHE or legal(p):continue
        assert old['payload'].get(p)==revised.get(p),'Unexpected GTK4 runtime change '+p
    data={'scope':'New Mutter owned Wayland bootstrap and existing GTK4 shared schema/legal-only metadata update; no GTK4 library rebuild or user preference change','state':'prepared','packages':[],'old_gtk_archive_sha256':old['archive_sha256'],'old_cache_sha256':proof['baseline_cache_sha256'],'new_cache_sha256':proof['union_cache_sha256'],'schema_inputs':proof['schema_inputs'],'new_schemas':proof['new_schemas'],'new_default_values_checked':39,'rollback':'Inspect actual dpkg/receipt first. Retained GTK4 toddy3 archive restores previous cache/owner metadata, then remove only newly installed Mutter; verify old cache and remaining stock XML. ColorHelper XML was already installed before this transaction. Never replay an uncertain step.'}
    def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
    def package(name,version,stage,inputs,depends):
        data['state']='installing-'+name;save()
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,version,str(stage),*[a for fn in inputs for a in ['--source',fn]],'--recipe','scripts/build/phase2/mutter-resources-install.sh','--depends',depends,'--install'],cwd=ROOT,check=True)
        r=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text());assert r['installed'];verify(r);data['packages'].append({k:r[k] for k in ['name','version','archive_sha256']});data['state']='installed-'+name;save()
    save();package('mutter','50.4-1+toddy1',mutter,['mutter-50.4.tar.xz'],', '.join(deps))
    assert {p.name:sha(p) for p in base.iterdir() if p.name!='gschemas.compiled'}==proof['schema_inputs']
    package('gtk','4.22.4-1+toddy4',gtk,archives,gtk_deps)
    assert sha(TARGET/CACHE)==proof['union_cache_sha256']
    data['old_gtk_nonlegal_regular_files_unchanged']=sum(1 for p,row in old['payload'].items() if 'sha256' in row and p!='/'+CACHE and not legal(p));data['state']='complete';save()
if __name__=='__main__':main()
