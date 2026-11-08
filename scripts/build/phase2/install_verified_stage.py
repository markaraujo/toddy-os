#!/usr/bin/env python3
"""Promote a declared successful compiler stage through the native backend only.

Invoked inside run_step's full-root transaction, never by the compiler namespace.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

from verify_stage import inspect_stage
from package_copyright import write_copyright

ROOT = Path('/opt/toddy-build')
PROFILES = {
    'qtsvg': ('6.11.2', 'qtbase (>= 6.11.2-1+toddy1)',
              'qtsvg-everywhere-src-6.11.2.tar.xz', 'usr/lib/libQt6Svg.so.6.11.2'),
    'qttools-linguist': ('6.11.2', 'qtbase (>= 6.11.2-1+toddy1)',
                        'qttools-everywhere-src-6.11.2.tar.xz', 'usr/bin/lrelease'),
    'extra-cmake-modules': ('6.29.0', 'cmake (>= 4.4.2-1)',
                          'extra-cmake-modules-6.29.0.tar.xz', 'usr/share/ECM/cmake/ECMConfig.cmake'),
    'kcoreaddons': ('6.29.0', 'qtbase (>= 6.11.2-1+toddy1), util-linux (>= 2.42.4-1), systemd (>= 261.2-1)',
                   'kcoreaddons-6.29.0.tar.xz', 'usr/lib/libKF6CoreAddons.so.6.29.0'),
    'yaml-cpp': ('0.9.0', 'gcc (>= 16.2.0-1), glibc (>= 2.44-1)',
                 'yaml-cpp-yaml-cpp-0.9.0.tar.gz', 'usr/lib/libyaml-cpp.so.0.9.0'),
}

if __name__ == '__main__':
    name, = sys.argv[1:]
    version, depends, archive, required = PROFILES[name]
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    log = Path('/var/log/toddy/phase2')
    assert (log / (name+'-1.exit')).read_text().strip() == '0', 'Reconcile actual compiler exit first'
    source = Path('/mnt/lfs/sources/phase2/work') / (name+'-1') / 'stage'
    before = inspect_stage(source)
    assert required in before['entries'], 'Missing declared payload'
    destination = Path('/mnt/lfs/sources/stage') / ('phase2-'+name)
    assert not destination.exists(), 'Reconcile existing stage; no replay'
    shutil.copytree(source, destination, symlinks=True)
    assert inspect_stage(destination) == before
    (log / (name+'-stage.json')).write_text(json.dumps(before, indent=2)+'\n')
    write_copyright(destination, name, [archive])
    subprocess.run([sys.executable, str(ROOT/'scripts/build/stage_package.py'), name,
                    version+'-1+toddy1', str(destination), '--source', archive,
                    '--recipe', 'scripts/build/phase2/'+name+'-install.sh',
                    '--depends', depends, '--install'], cwd=ROOT, check=True)
