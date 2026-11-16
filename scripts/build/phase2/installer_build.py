#!/usr/bin/env python3
"""Qualified UID101 compiler-side entry; no native root/package installation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def build():
    if os.getuid()!=101 or Path('/src').resolve()!=Path('/src') or not Path('/build').is_dir():raise SystemExit('installer_isolated_uid101_required')
    repository=Path('/src/repository');source=repository/'runtime/installer/calamares';compile=Path('/build/compile')
    if compile.exists() or list(Path('/stage').iterdir()):raise SystemExit('installer_compiler_outputs_not_fresh')
    sys.path.insert(0,str(repository/'scripts/build/phase2'))
    import installer_package as package
    environment={'PATH':'/usr/bin:/usr/sbin','HOME':'/build/home','LC_ALL':'C.UTF-8','LANG':'C.UTF-8'}
    commands=[['/usr/bin/cmake','-S',str(source),'-B',str(compile),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
               '-DCMAKE_INSTALL_PREFIX=/usr','-DCMAKE_INSTALL_LIBDIR=lib','-DCMAKE_SKIP_RPATH=ON'],
              ['/usr/bin/cmake','--build',str(compile),'--parallel','6']]
    for command in commands:subprocess.run(command,env=environment,check=True,close_fds=True)
    module=compile/'libcalamares_viewmodule_toddy.so'
    probe=compile/'toddy-installer-plugin-probe'
    result=subprocess.run([str(probe),str(module)],env={**environment,'QT_QPA_PLATFORM':'offscreen','GTK_A11Y':'none'},
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=30,close_fds=True)
    if len(result.stdout)>8192:raise SystemExit('installer_probe_output_limit')
    receipt={'schema_version':1,'kind':'native-toddy-calamares-module-v1','calamares_version':'3.4.3','qt_version':'6.11.2',
             'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),
             'source_sha256':{name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in package.COMPILE_INPUTS},
             'probe':json.loads(result.stdout),'compile_exit':0}
    proof=Path('/build/native-module-compile.json');proof.write_bytes(package.encoded(receipt))
    payload=Path('/build/package-stage');manifest=package.stage(repository,payload,module,proof)
    shutil.copytree(payload,'/stage',dirs_exist_ok=True,symlinks=True)
    Path('/build/package-stage-manifest.json').write_bytes(package.encoded(manifest))
    print(package.encoded({'state':'native-module-built-and-staged','module_sha256':manifest['module_sha256'],
                          'native_root_gui_qualified':False,'disk_writes':False}).decode(),end='')

if __name__=='__main__':build()
