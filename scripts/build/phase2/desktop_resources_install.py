"""Own native themes/settings and update only GTK's schema/legal metadata."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from package_copyright import write_copyright
from verify_stage import inspect_stage
from install_verified_stage import PROFILES
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs')


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    fs=os.statvfs(TARGET);assert fs.f_bavail*fs.f_frsize>=16*1024**3+96*1024**2
    logs=Path('/var/log/toddy/phase2');source=TARGET/'sources/phase2/inputs/desktop-resources-50'
    work=TARGET/'sources/phase2/work/desktop-resources-1';data=work/'resources'
    config=json.loads((source/'toddy-resources.json').read_text())
    assert (source/'toddy-resources.json').read_bytes()==(ROOT/'config/phase2/desktop-resources.lock.json').read_bytes()
    assert (source/'toddy-build.py').read_bytes()==(ROOT/'scripts/build/phase2/desktop_resources_build.py').read_bytes()
    names={p['name'] for p in config['packages']};assert names=={'hicolor-icon-theme','adwaita-icon-theme','gsettings-desktop-schemas'}
    harness=sha(ROOT/'scripts/build/phase2/isolated.sh')
    original=json.loads((logs/'desktop-resources-1.job.json').read_text());assert original['harness_sha256']==harness
    legacy=(logs/'desktop-resources-probe-recovery-2.job.json').exists()
    if legacy:
        assert (logs/'desktop-resources-1.exit').read_text().strip()=='1'
        assert (logs/'desktop-resources-probe-recovery-2.exit').read_text().strip()=='0'
        r=json.loads((logs/'desktop-resources-probe-recovery-2.job.json').read_text());assert r['harness_sha256']==harness
        assert r['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/desktop_resources_probe_recovery.py').read_text()]
        old="assert GDesktopEnums.BackgroundStyle.ZOOM.value_nick=='zoom'"
        new="assert int(GDesktopEnums.BackgroundStyle.ZOOM)==5  # Frozen gdesktop-enums.h plain C enum."
        text=(source/'toddy-probe.py').read_text();assert text.count(old)==1
        assert text.replace(old,new)==(ROOT/'scripts/build/phase2/desktop_resources_probe.py').read_text()
        recovery=json.loads((data/'recovery-2/qualified.json').read_text());assert recovery['native_exit']==0
        for relative,row in json.loads((data/'recovery-2/stage-before.json').read_text()).items():
            path=work/'stage'/relative
            if 'link' in row:assert path.is_symlink() and path.readlink().as_posix()==row['link']
            else:assert sha(path)==row['sha256']
        consumer=recovery['consumer']
    else:
        assert (logs/'desktop-resources-1.exit').read_text().strip()=='0'
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/desktop_resources_probe.py').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['consumer_exit']==0
        consumer=proof['consumer']
    assert consumer['schemas']==52 and consumer['enum_zoom']==5 and consumer['cursor_magic']=='Xcur'
    assert consumer['svg_size']==[32,32] and consumer['png_bytes']>0
    stages={}
    for p in config['packages']:
        name=p['name']
        for phase in ['configure','build','stage']:
            assert (data/'logs'/(name+'-'+phase+'.exit')).read_text().strip()=='0'
        # These frozen data releases register no executable upstream suite.
        tests=json.loads((data/'compile'/name/'meson-info/intro-tests.json').read_text());assert tests==[]
        stages[name]=inspect_stage(work/'stage'/name)
        assert not (TARGET/'sources/stage'/('phase2-'+name)).exists(),'Reconcile prior package transaction; no replay'
    for name in ['hicolor-icon-theme','adwaita-icon-theme']:
        for phase in ['cache','cache-validate']:assert (data/'logs'/(name+'-'+phase+'.exit')).read_text().strip()=='0'
    assert (data/'logs/gsettings-desktop-schemas-schema-cache.exit').read_text().strip()=='0'
    old_path=Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy1_amd64.json');old_gtk=json.loads(old_path.read_text())
    assert old_gtk['installed'] and old_gtk['version']=='4.22.4-1+toddy1'
    gtk_sources={r['filename']:r['sha256'] for r in old_gtk['sources']}
    assert gtk_sources['gtk-4.22.4.tar.xz']=='51bd9f60c7d23a665a556c7364c21fb2e4e282566b3e7e092455e8f910330893'
    qualified=Path('/var/log/toddy/build/b02-gtk-install.success.json')
    if not qualified.exists():qualified=Path('/var/log/toddy/build/b02-gtk-postcheck-reconcile.success.json')
    accepted=json.loads(qualified.read_text());assert accepted['recipe_exit']==accepted['postcheck_exit']==0
    assert sha(Path('/var/cache/toddy/packages/gtk_4.22.4-1+toddy1_amd64.deb'))==old_gtk['archive_sha256']
    old_stage=TARGET/'sources/stage/phase2-gtk'
    original_payload={p:r for p,r in payload(old_stage).items() if p!='/DEBIAN' and not p.startswith('/DEBIAN/')}
    assert original_payload==old_gtk['payload']
    cache_relative='usr/share/glib-2.0/schemas/gschemas.compiled'
    assert sha(TARGET/cache_relative)==old_gtk['payload']['/'+cache_relative]['sha256']
    gtk_stage=TARGET/'sources/stage/phase2-gtk-desktop-schemas';assert not gtk_stage.exists()
    receipt_path=logs/'desktop-resources-transaction.json';assert not receipt_path.exists()
    receipt={'scope':'Three independent data packages; same-owner GTK schema cache/legal metadata upgrade only, no library rebuild or user configuration writes',
             'state':'planned','packages':[],'old_gtk_archive_sha256':old_gtk['archive_sha256']}
    def save():receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    save()
    def package(name,version,stage,archives,depends):
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,version,str(stage),
            *[arg for a in archives for arg in ['--source',a]],'--recipe','scripts/build/phase2/desktop-resources-install.sh',
            '--depends',depends,'--install'],cwd=ROOT,check=True)
        r=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text());assert r['installed']
        receipt['packages'].append({k:r[k] for k in ['name','version','archive_sha256','installed']});save()
    deps={'hicolor-icon-theme':'gtk (>= 4.22.4-1+toddy1)',
          'adwaita-icon-theme':'hicolor-icon-theme (= 0.18-1+toddy1), gtk (>= 4.22.4-1+toddy1), librsvg (= 2.62.3-1+toddy1)',
          'gsettings-desktop-schemas':'glib (>= 2.88.3-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)'}
    for p in config['packages']:
        name=p['name'];destination=TARGET/'sources/stage'/('phase2-'+name)
        shutil.copytree(work/'stage'/name,destination,symlinks=True);assert inspect_stage(destination)==stages[name]
        write_copyright(destination,name,[p['archive']])
        package(name,p['version']+'-1+toddy1',destination,[p['archive']],deps[name])
    # Accept the already validated private schema cache only when every actual
    # installed stock input is identical; reject unexpected additions/changes.
    actual={p.name:sha(p) for p in (TARGET/'usr/share/glib-2.0/schemas').iterdir() if p.is_file() and p.name!='gschemas.compiled'}
    expected={p.name:sha(p) for p in (data/'schema-union').iterdir() if p.is_file() and p.name!='gschemas.compiled'}
    assert actual==expected
    shutil.copytree(old_stage,gtk_stage,symlinks=True,ignore=shutil.ignore_patterns('DEBIAN'))
    assert payload(gtk_stage)==old_gtk['payload']
    (gtk_stage/cache_relative).write_bytes((data/'schema-union/gschemas.compiled').read_bytes())
    archives=['gtk-4.22.4.tar.xz','gsettings-desktop-schemas-50.1.tar.xz']
    write_copyright(gtk_stage,'gtk',archives)
    revised=payload(gtk_stage)
    def legal(p):return p=='/usr/share/doc/gtk' or p.startswith('/usr/share/doc/gtk/')
    for path in set(old_gtk['payload'])|set(revised):
        if path=='/'+cache_relative or legal(path):continue
        assert old_gtk['payload'].get(path)==revised.get(path),'Unexpected GTK library/runtime change: '+path
    receipt['schema_inputs']=actual;receipt['new_schema_cache_sha256']=sha(gtk_stage/cache_relative)
    receipt['gtk_other_runtime_payload_unchanged']=True;receipt['state']='data-installed';save()
    package('gtk','4.22.4-1+toddy2',gtk_stage,archives,PROFILES['gtk'][1]+', gsettings-desktop-schemas (= 50.1-1+toddy1)')
    assert sha(TARGET/cache_relative)==receipt['new_schema_cache_sha256']
    receipt['consumer']=consumer;receipt['state']='complete';save()
    fs=os.statvfs(TARGET);assert fs.f_bavail*fs.f_frsize>=16*1024**3


if __name__=='__main__':main()
