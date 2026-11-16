"""Narrow B11 upgrade of the canonical B02 defaults package; run_step owns writes.

The only settings changes are the approved background URI/URI-dark/options.
No home files, locks, artwork or foreign-owned files enter this package.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
from branding_stage import render_desktop_defaults,source
import desktop_defaults as defaults

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs')
CACHE=Path('/var/cache/toddy/packages');RECORDS=Path('/var/log/toddy/packages')
LOG=Path('/var/log/toddy/phase2');BUILD=Path('/var/log/toddy/build')
NAME='toddy-desktop-defaults';OLD='0.2.0-1+toddy1';VERSION='0.2.0-1+toddy2'
STEP='b11-desktop-background-upgrade-1'
INSTALL='scripts/build/phase2/desktop-background-install.sh'
CHECK='scripts/build/phase2/desktop-background-check.sh'
STAGE=TARGET/'sources/stage/phase2-toddy-desktop-defaults-2'
RECEIPT=LOG/'desktop-background-upgrade-1.json'
LIGHT='file:///usr/share/backgrounds/toddy-os/toddy-os-wallpaper-light-logo.png'
DARK='file:///usr/share/backgrounds/toddy-os/toddy-os-wallpaper-dark-logo.png'


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def regular(path):
    path=Path(path)
    if path.resolve()!=path or not path.is_file() or path.is_symlink():raise ValueError('Background input must be a canonical regular file')
    info=path.stat()
    if info.st_nlink!=1 or info.st_mode&0o002 or (info.st_mode&0o020 and (info.st_uid!=0 or info.st_gid!=0)):raise ValueError('Background input writable or linked')
    return path


def native(*args):
    return subprocess.check_output(['chroot',str(TARGET),*args],text=True).strip()


def baseline(repository,records,cache):
    approved=next(row for row in json.loads(source(repository,'docs/evidence/B02-desktop-runtime-manifest.json'))['components'] if row['name']==NAME)
    if approved['version']!=OLD:raise ValueError('Frozen B02 defaults identity changed')
    record_path=regular(records/(NAME+'_'+OLD+'_all.json'))
    archive=regular(cache/(NAME+'_'+OLD+'_all.deb'))
    if digest(record_path)!=approved['component_record_sha256'] or digest(archive)!=approved['archive_sha256']:raise ValueError('Frozen B02 defaults custody differs')
    record=json.loads(record_path.read_text())
    if record['name']!=NAME or record['version']!=OLD or record['archive_sha256']!=approved['archive_sha256'] or record['installed'] is not True or not record['payload']:raise ValueError('Frozen B02 defaults record invalid')
    return approved,record,archive


def verify_payload(root,entries,*,exclusive=False):
    checked=[]
    for virtual,row in entries.items():
        if not virtual.startswith('/') or '..' in Path(virtual).parts:raise ValueError('Background payload path')
        if row.get('directory'):continue
        if 'sha256' not in row or 'symlink' in row:raise ValueError('Unsupported B02 defaults payload')
        path=regular(root/virtual.lstrip('/'));info=path.stat()
        if digest(path)!=row['sha256'] or stat.S_IMODE(info.st_mode)!=stat.S_IMODE(row['mode']) or info.st_uid!=row['uid'] or info.st_gid!=row['gid']:raise ValueError('Defaults payload drift: '+virtual)
        checked.append(virtual)
    if not checked:raise ValueError('Empty defaults payload')
    if exclusive:
        actual={'/'+str(p.relative_to(root)) for p in root.rglob('*') if not p.is_dir() or p.is_symlink()}
        if actual!=set(checked):raise ValueError('Unexpected defaults archive files')
    return checked


def render(stage,repository,approved,record):
    """Only called after exact old archive extraction/payload verification."""
    verify_payload(stage,record['payload'],exclusive=True)
    keyfile=stage/defaults.KEYFILE.lstrip('/')
    before=keyfile.read_text();after=render_desktop_defaults(before)
    if before==after:raise ValueError('Background upgrade must change the baseline')
    keyfile.write_text(after)
    readme=stage/'usr/share/doc'/NAME/'README'
    readme.write_text(readme.read_text()+'''\nB11 native upgrade 0.2.0-1+toddy2 supersedes the plain-background statement above.\nOnly picture-uri, picture-uri-dark and picture-options defaults change. Exact\nwallpapers remain owned by toddy-branding; no artwork is copied here. Explicit\nuser dconf preferences still take priority and no preference locks are added.\nNative default readback and actual fresh GNOME screenshots are separate gates.\n''')
    names=['LICENSE','LICENSES/CC-BY-4.0.txt','scripts/build/phase2/desktop_defaults.py',
           'scripts/build/phase2/branding_stage.py','scripts/build/phase2/desktop_background_upgrade.py',INSTALL,CHECK,
           'docs/evidence/B02-desktop-runtime-manifest.json','assets/brand/gnome/package-map.json','assets/brand/assets.json']
    inputs={name:{'sha256':hashlib.sha256(source(repository,name)).hexdigest(),'bytes':len(source(repository,name))} for name in names}
    inputs['native-inputs/'+NAME+'_'+OLD+'_all.deb']=approved['archive_sha256']
    inputs['native-inputs/'+NAME+'_'+OLD+'_all.json']=approved['component_record_sha256']
    result={'package':NAME,'version':VERSION,'source_inputs':inputs,'baseline_version':OLD,
            'baseline_archive_sha256':approved['archive_sha256'],'baseline_record_sha256':approved['component_record_sha256'],
            'settings_changed':['picture-uri','picture-uri-dark','picture-options'],
            'artwork_owner':'toddy-branding','scope':'Original data-only defaults upgrade; native rendering acceptance pending'}
    manifest=stage/'usr/share/doc'/NAME/'source-manifest.json'
    with manifest.open('x') as stream:stream.write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    manifest.chmod(0o644)
    return result


def install():
    from dependency_preflight import native as verify_dependencies
    approved,old_record,archive=baseline(ROOT,RECORDS,CACHE)
    assert native('dpkg-query','-W','-f=${Status} ${Version}',NAME)=='install ok installed '+OLD
    verify_payload(TARGET,old_record['payload']) # Preserve edited conffiles/generated DB for explicit diagnosis.
    depends=approved['depends']+', toddy-branding (= 0.2.0-1+toddy1)'
    verify_dependencies(depends)
    mapping=json.loads(source(ROOT,'assets/brand/gnome/package-map.json'))
    for uri in (LIGHT,DARK):
        virtual=uri.removeprefix('file://');row=next(row for row in mapping['payload'] if row['destination']==virtual)
        assert digest(regular(TARGET/virtual.lstrip('/')))==hashlib.sha256(source(ROOT,row['source'])).hexdigest()
        assert native('dpkg-query','-S',virtual)== 'toddy-branding: '+virtual
    assert shutil.disk_usage(TARGET).free>=16*1024**3+512*1024**2
    incoming=STAGE.with_name(STAGE.name+'-baseline.deb')
    assert not STAGE.exists() and not STAGE.is_symlink() and not incoming.exists() and not incoming.is_symlink() and not RECEIPT.exists()
    assert not (CACHE/(NAME+'_'+VERSION+'_all.deb')).exists() and not (RECORDS/(NAME+'_'+VERSION+'_all.json')).exists()
    shutil.copyfile(archive,incoming);incoming.chmod(0o644);assert digest(incoming)==approved['archive_sha256']
    # Extraction and dconf compilation use the actual installed native tools.
    native('dpkg-deb','--extract','/'+str(incoming.relative_to(TARGET)),'/'+str(STAGE.relative_to(TARGET)))
    manifest=render(STAGE,ROOT,approved,old_record)
    native('dconf','compile','/'+str(STAGE.relative_to(TARGET))+defaults.DATABASE,'/'+str(STAGE.relative_to(TARGET))+'/etc/dconf/db/toddy-desktop.d')
    (STAGE/defaults.DATABASE.lstrip('/')).chmod(0o644)
    subprocess.run(['python3',str(ROOT/'scripts/build/stage_package.py'),NAME,VERSION,str(STAGE),'--architecture','all','--recipe',INSTALL,'--depends',depends,
                    '--conffile',defaults.PROFILE,'--conffile',defaults.KEYFILE,'--install'],cwd=ROOT,check=True)
    with RECEIPT.open('x') as stream:json.dump({'package':NAME,'version':VERSION,'manifest':manifest,'driver_sha256':digest(Path(__file__)),'old_archive_retained':str(archive),'old_record_retained':str(RECORDS/(NAME+'_'+OLD+'_all.json'))},stream,indent=2);stream.write('\n')


# Fixed UID101 isolated dconf consumer. It checks two fresh session buses and
# owner preference persistence/reset; no graphical acceptance or user-home scan.
CONSUMER='''import json,sys
from gi.repository import Gio
assert Gio.SettingsBackend.get_default().__gtype__.name=='DConfSettingsBackend'
b=Gio.Settings.new('org.gnome.desktop.background');i=Gio.Settings.new('org.gnome.desktop.interface')
p=Gio.Settings.new_with_path('org.gnome.Terminal.Legacy.Profile','/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/')
expected={'picture-uri':sys.argv[2],'picture-uri-dark':sys.argv[3],'picture-options':'zoom'}
assert all(b.is_writable(key) for key in expected) and b.is_writable('primary-color')
assert i.get_string('color-scheme')=='prefer-dark'
assert p.get_string('background-color')=='#081b33' and p.get_string('foreground-color')=='#f4f7fb' and not p.get_boolean('use-theme-colors') and p.get_boolean('use-system-font')
assert Gio.Settings.new('org.gnome.shell').get_strv('favorite-apps')==['org.gnome.Nautilus.desktop','firefox.desktop','org.gnome.Terminal.desktop','org.gnome.TextEditor.desktop','org.gnome.Settings.desktop']
if sys.argv[1]=='write':
 assert all(b.get_string(key)==value for key,value in expected.items()) and b.get_string('primary-color')=='#081b33'
 assert b.set_string('picture-uri','file:///owner-preference.png') and b.set_string('primary-color','#123456');Gio.Settings.sync()
else:
 assert b.get_string('picture-uri')=='file:///owner-preference.png' and b.get_string('primary-color')=='#123456'
 b.reset('picture-uri');b.reset('primary-color');Gio.Settings.sync()
 assert all(b.get_string(key)==value for key,value in expected.items()) and b.get_string('primary-color')=='#081b33'
print(json.dumps({'cycle':sys.argv[1],'defaults_and_unlocked_user_override_verified':True}))
'''


def check():
    receipt=json.loads(regular(RECEIPT).read_text());assert receipt['driver_sha256']==digest(Path(__file__))
    assert native('dpkg-query','-W','-f=${Status} ${Version}',NAME)=='install ok installed '+VERSION
    record=json.loads(regular(RECORDS/(NAME+'_'+VERSION+'_all.json')).read_text())
    assert record['installed'] and record['name']==NAME and record['version']==VERSION
    assert digest(regular(CACHE/(NAME+'_'+VERSION+'_all.deb')))==record['archive_sha256']
    checked=verify_payload(TARGET,record['payload'])
    for virtual in checked:assert native('dpkg-query','-S',virtual)==NAME+': '+virtual
    baseline(ROOT,RECORDS,CACHE) # Historical B02 archive/record remain intact.
    rows=[]
    with tempfile.TemporaryDirectory(prefix='toddy-background-',dir=TARGET/'var/tmp') as directory:
        home=Path(directory);os.chown(home,101,101);virtual='/var/tmp/'+home.name
        for name in ('config','runtime'):(home/name).mkdir(mode=0o700);os.chown(home/name,101,101)
        env={'HOME':virtual,'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','XDG_CONFIG_HOME':virtual+'/config','XDG_RUNTIME_DIR':virtual+'/runtime','GSETTINGS_BACKEND':'dconf','DCONF_PROFILE':'user','PYTHONDONTWRITEBYTECODE':'1'}
        for mode in ('write','read'):
            process=subprocess.run(['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(TARGET),'dbus-run-session','--','python3','-c',CONSUMER,mode,LIGHT,DARK],env=env,capture_output=True,text=True,timeout=30)
            assert process.returncode==0,(mode,process.stdout,process.stderr);rows.append(json.loads(process.stdout))
    assert not native('dpkg','--audit');native('apt-get','check')
    with (LOG/'desktop-background-check-1.json').open('x') as stream:json.dump({'package':NAME,'version':VERSION,'checked':checked,'cycles':rows,'scope':'Installed native dconf/ownership/defaults only; actual GNOME screenshots pending'},stream,indent=2);stream.write('\n')


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ('install','check'):raise SystemExit('Expected install or check')
    assert os.getuid()==os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    transaction=json.loads(regular(BUILD/(STEP+'.running.json')).read_text())
    assert transaction['step']==STEP and transaction['user']=='root'
    assert transaction['recipe_sha256']==digest(ROOT/INSTALL) and transaction['postcheck_sha256']==digest(ROOT/CHECK)
    if sys.argv[1]=='install':assert transaction['recipe_pid'] in (os.getpid(),os.getppid())
    else:assert transaction['recipe_exit']==0
    globals()[sys.argv[1]]()


if __name__=='__main__':main()
