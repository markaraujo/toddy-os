"""Deterministically stage the live-only original Calamares module/client payload.

Requires an actual compiled module/ABI receipt; missing artifacts are blockers,
not substitute test binaries or production qualification receipts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess

VERSION='0.2.0-1+toddy1'
PACKAGE='toddy-installer'
MODULE='/usr/lib/calamares/modules/toddy/libcalamares_viewmodule_toddy.so'
COMPILE_INPUTS=('CMakeLists.txt','ToddyViewStep.cpp','ToddyViewStep.h','ToddyPluginProbe.cpp')
INSTALLER_MODULES=('backend.py','disk_plan.py','linux_disk.py','installed_identity.py','live_bindings.py',
                   'composition.py','native_finalizer.py','installed_boot.py','launch.py')
DEPENDENCIES=('toddy-assistant, calamares (= 3.4.3-1+toddy1), calamares-branding-toddy, '
 'qtbase (= 6.11.2-1+toddy2), pygobject (= 3.56.3-1+toddy1), polkit (= 127-1+toddy1), '
 'glibc (>= 2.44-1), gcc-runtime, gcc, util-linux, e2fsprogs, dosfstools, grub, shadow, '
 'systemd (>= 261.2-1+toddy3), dpkg, gnupg, kmod, libarchive, gzip, coreutils, bash')
EPOCH=1794009600
LAUNCHER='''#!/usr/bin/python3 -I
# Original MIT source; only fixed native owner authorization, no inherited data.
import json
import os
import re
import subprocess
import sys
if sys.argv[1:] or os.getuid()==0:
    raise SystemExit('Use the installed live desktop launcher as the active owner.')
display=os.environ.get('WAYLAND_DISPLAY','')
if not re.fullmatch('wayland-[0-9]{1,4}',display):
    raise SystemExit('Toddy installer requires the active native Wayland desktop.')
locale='pt_BR.UTF-8' if os.environ.get('LC_ALL',os.environ.get('LANG','')).startswith('pt') else 'en_US.UTF-8'
request=json.dumps({'version':1,'display':display,'locale':locale}).encode()
raise SystemExit(subprocess.run(['/usr/bin/pkexec','/usr/libexec/toddy-installer-auth'],input=request,close_fds=True).returncode)
'''
ROOT_ENTRY='''#!/usr/bin/python3 -I
# Fixed root-owned Polkit action; Python ignores user import configuration.
import runpy
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'/usr/lib')
runpy.run_module('toddy.installer.launch',run_name='__main__',alter_sys=True)
'''
POLICY='''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN" "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <action id="io.github.markaraujo.Toddy.Install">
    <description>Install Toddy OS onto an explicitly reviewed blank disk</description>
    <description xml:lang="pt_BR">Instalar Toddy OS em disco vazio explicitamente revisado</description>
    <message>Authenticate as the OS administrator to open the Toddy installer.</message>
    <message xml:lang="pt_BR">Autentique-se como administrador do sistema para abrir o instalador Toddy.</message>
    <defaults><allow_any>no</allow_any><allow_inactive>no</allow_inactive><allow_active>auth_admin</allow_active></defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/libexec/toddy-installer-auth</annotate>
  </action>
</policyconfig>
'''
DESKTOP='''[Desktop Entry]
Type=Application
Name=Install Toddy OS
Name[pt_BR]=Instalar Toddy OS
Exec=/usr/bin/toddy-installer
TryExec=/usr/bin/toddy-installer
Icon=io.github.markaraujo.Toddy
Terminal=false
Categories=System;
NoDisplay=true
StartupNotify=true
'''

class InstallerPackageError(ValueError):pass


def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()


def artifact_json(data):
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise InstallerPackageError('installer_duplicate_artifact_field')
            value[key]=item
        return value
    try:
        return json.loads(data.decode('utf-8'),object_pairs_hook=pairs,
                          parse_constant=lambda _:(_ for _ in ()).throw(InstallerPackageError('installer_nonfinite_artifact_field')))
    except (UnicodeError,ValueError,RecursionError) as error:
        raise InstallerPackageError('installer_artifact_json') from error

def read(repository,relative):
    path=Path(repository)/relative
    if not path.is_file() or path.is_symlink() or path.resolve()!=path or path.stat().st_nlink!=1:
        raise InstallerPackageError('installer_source_custody')
    return path.read_bytes()


def validate_module(module,receipt,repository):
    module=Path(module);receipt=Path(receipt)
    for path in (module,receipt):
        if not path.is_absolute() or path.resolve()!=path or not path.is_file() or path.is_symlink() or path.stat().st_nlink!=1:
            raise InstallerPackageError('installer_native_artifact_custody')
    if module.stat().st_size>64*1024*1024 or receipt.stat().st_size>131072:raise InstallerPackageError('installer_native_artifact_limit')
    data=module.read_bytes()
    if len(data)<64 or data[:7]!=b'\x7fELF\x02\x01\x01' or struct.unpack_from('<HHI',data,16)!=(3,62,1):
        raise InstallerPackageError('installer_native_amd64_module_required')
    value=artifact_json(receipt.read_bytes())
    expected={'schema_version','kind','calamares_version','qt_version','module_sha256','source_sha256','probe','compile_exit'}
    sources={name:sha(read(repository,'runtime/installer/calamares/'+name)) for name in COMPILE_INPUTS}
    probe={'qt':'6.11.2','plugin_iid':'io.calamares.PluginFactory','factory_created':True,'review_requires_confirmation':True,'disk_writes':False}
    if not isinstance(value,dict) or set(value)!=expected or type(value['schema_version']) is not int or value['schema_version']!=1 or \
            value['kind']!='native-toddy-calamares-module-v1' or value['calamares_version']!='3.4.3' or value['qt_version']!='6.11.2' or \
            value['module_sha256']!=sha(data) or value['source_sha256']!=sources or encoded(value['probe'])!=encoded(probe) or \
            type(value['compile_exit']) is not int or value['compile_exit']!=0:
        raise InstallerPackageError('installer_native_compile_receipt')
    dynamic=subprocess.check_output(['/usr/bin/readelf','-d',str(module)],text=True)
    if '(RPATH)' in dynamic or '(RUNPATH)' in dynamic:raise InstallerPackageError('installer_module_runtime_search_path')
    needed=re.findall(r'\(NEEDED\).*\[(.*?)\]',dynamic)
    if not all(any(name.startswith(prefix) for name in needed) for prefix in ('libcalamares.so','libcalamaresui.so','libQt6Widgets.so','libQt6Core.so')):
        raise InstallerPackageError('installer_module_frozen_providers')
    symbols=subprocess.check_output(['/usr/bin/nm','-D','--defined-only',str(module)],text=True)
    if not re.search(r'\bqt_plugin_instance\b',symbols) or not re.search(r'\bqt_plugin_query_metadata(?:_v2)?\b',symbols) or b'io.calamares.PluginFactory' not in data:
        raise InstallerPackageError('installer_native_qt_plugin_metadata')
    return data,value


def plan(repository):
    repository=Path(repository)
    if not repository.is_absolute() or repository.resolve()!=repository:raise InstallerPackageError('installer_repository_path')
    inputs={};files={};links={}
    def source(relative):
        data=read(repository,relative);inputs[relative]=sha(data);return data
    def copy(relative,destination,mode=0o644):files[destination]=(source(relative),mode)
    for name in INSTALLER_MODULES:copy('runtime/installer/'+name,'/usr/lib/toddy/installer/'+name)
    for name in ('cli.py','adapter.py'):copy('runtime/installer/calamares/'+name,'/usr/lib/toddy/installer/calamares/'+name)
    copy('scripts/build/phase2/offline_payload.py','/usr/lib/toddy/installer/offline_payload.py')
    for name in ('initramfs_runtime.py','initramfs_archive.py'):copy('scripts/build/h10/'+name,'/usr/lib/toddy/installer/h10/'+name)
    copy('scripts/build/audit_native_elf.py','/usr/lib/toddy/installer/audit_native_elf.py')
    copy('runtime/installer/calamares/module.desc','/usr/lib/calamares/modules/toddy/module.desc')
    copy('runtime/installer/calamares/strings.json','/usr/share/calamares/modules/toddy/strings.json')
    settings=source('runtime/installer/calamares/settings.conf.in')
    if b'exec:\n  - toddy@review' not in settings or b'disable-cancel-during-exec: true' not in settings or b'modules-search: [ "/usr/lib/calamares/modules" ]' not in settings:
        raise InstallerPackageError('installer_fixed_module_sequence')
    readonly=settings.replace(b'- exec:\n  - toddy@review\n',b'').replace(b'- show:\n  - toddy@finished\n',b'')
    if re.search(rb'(?m)^- exec:',readonly):raise InstallerPackageError('installer_qualification_config_can_execute')
    for name,body in (('calamares',settings),('calamares-qualification',readonly)):
        prefix='/usr/share/toddy/installer/'+name
        files[prefix+'/settings.conf']=(body,0o644)
        for leaf in ('toddy-review.conf','toddy-finished.conf'):copy('runtime/installer/calamares/'+leaf,prefix+'/modules/'+leaf)
        # Calamares -c changes appDataDir including branding lookup. This is the
        # only declared dependency alias; the branding package owns all assets.
        links[prefix+'/branding/toddy']='../../../../calamares/branding/toddy'
    files['/usr/bin/toddy-installer']=(LAUNCHER.encode(),0o755)
    files['/usr/libexec/toddy-installer-auth']=(ROOT_ENTRY.encode(),0o755)
    files['/usr/share/polkit-1/actions/io.github.markaraujo.Toddy.Install.policy']=(POLICY.encode(),0o644)
    files['/usr/share/applications/io.github.markaraujo.Toddy.Installer.desktop']=(DESKTOP.encode(),0o644)
    docs='/usr/share/doc/'+PACKAGE
    for relative,leaf in (('LICENSE','copyright-original'),('LICENSES/GPL-3.0.txt','GPL-3.0.txt'),('LICENSES/CC-BY-4.0.txt','CC-BY-4.0.txt'),
                          ('runtime/installer/README.md','backend.md'),('runtime/installer/COMPOSITION.md','composition.md'),
                          ('runtime/installer/calamares/README.md','calamares.md'),
                          ('scripts/build/phase2/installer-package.md','package.md')):
        copy(relative,docs+'/'+leaf)
    files[docs+'/copyright']=(b'''Original Toddy Python/C++/generator code: MIT; documentation/copy: CC BY4.0.
The dynamic Calamares3.4.3 module is a GPL-3.0-or-later combined work; the
original MIT source remains available under its original terms. Calamares and
Qt are separately source-built dependencies; retain their exact native package
notices, corresponding source and per-file SPDX terms. This package does not
incorporate Qt/Calamares binaries, except its own compiled module, or upstream
implementation sources. Original source and build input hashes are recorded in
source-manifest.json. Approved artwork is owned by the separate unchanged
calamares-branding-toddy/toddy-branding packages, never redesigned or relabeled.
''',0o644)
    copy('assets/brand/assets.json',docs+'/approved-art-references.json')
    copy('assets/brand/installer/scenes.json',docs+'/scene-references.json')
    source('assets/brand/installer/motion.json');source('config/phase2/install-options.json')
    policy=json.loads(source('config/phase2/packages.json'))
    rows=[row for row in policy['packages'] if row['name']==PACKAGE]
    if len(rows)!=1 or rows[0]['offline_base'] is not False or rows[0]['image_scope']!='live-only':raise InstallerPackageError('installer_live_only_contract')
    for leaf in ('installer_package.py','installer_native.py','installer_recipe.json','installer_build.py','installer_build.sh','installer_prepare.sh','installer_install.sh','installer_check.sh'):
        source('scripts/build/phase2/'+leaf)
    return inputs,files,links


def stage(repository,destination,module,compile_receipt):
    repository=Path(repository);destination=Path(destination)
    if not destination.is_absolute() or destination.resolve()!=destination or destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
        raise InstallerPackageError('installer_fresh_stage_required')
    inputs,files,links=plan(repository);binary,receipt=validate_module(module,compile_receipt,repository)
    files[MODULE]=(binary,0o644)
    files['/usr/share/doc/'+PACKAGE+'/native-module-compile.json']=(encoded(receipt),0o644)
    destination.mkdir(mode=0o755)
    for absolute,(data,mode) in sorted(files.items()):
        output=destination/absolute.lstrip('/');output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data);output.chmod(mode)
    for absolute,target in sorted(links.items()):
        output=destination/absolute.lstrip('/');output.parent.mkdir(parents=True,exist_ok=True);output.symlink_to(target)
    manifest={'schema_version':1,'package':PACKAGE,'version':VERSION,'architecture':'amd64','live_only':True,'offline_base':False,
              'dependencies':DEPENDENCIES,'inputs':inputs,
              'files':{name:{'sha256':sha(data),'bytes':len(data),'mode':format(mode,'04o')} for name,(data,mode) in sorted(files.items())},
              'dependency_links':links,'module_sha256':sha(binary),'native_compile_receipt_sha256':sha(encoded(receipt)),
              'native_root_gui_qualified':False,'desktop_hidden_until_native_promotion':True,
              'bundled_composition_qualification':False,'bundled_credentials':False,'bundled_grants':False,
              'branding_owner':'calamares-branding-toddy','upstream_calamares_owned_paths_modified':False}
    target=destination/'usr/share/doc'/PACKAGE/'source-manifest.json';target.write_bytes(encoded(manifest));target.chmod(0o644)
    for path in [*destination.rglob('*'),destination]:
        if path.is_dir() and not path.is_symlink():path.chmod(0o755)
        os.utime(path,(EPOCH,EPOCH),follow_symlinks=False)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repository','destination','module','compile-receipt'):parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args();print(encoded(stage(args.repository,args.destination,args.module,args.compile_receipt)).decode(),end='')

if __name__=='__main__':main()
