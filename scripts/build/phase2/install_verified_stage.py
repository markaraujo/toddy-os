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
    'freetype': ('2.14.3', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1), bzip2 (>= 1.0.8-1), libpng (>= 1.6.58-1+toddy1)',
                 'freetype-2.14.3.tar.xz', 'usr/lib/pkgconfig/freetype2.pc'),
    'libpng': ('1.6.58', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1)',
               'libpng-1.6.58.tar.xz', 'usr/lib/pkgconfig/libpng16.pc'),
    'pixman': ('0.46.4', 'glibc (>= 2.44-1)',
               'pixman-0.46.4.tar.gz', 'usr/lib/pkgconfig/pixman-1.pc'),
    'wayland': ('1.26.0', 'glibc (>= 2.44-1), libffi (>= 3.8.0-1), libxml2 (>= 2.15.3-1+toddy1)',
                'wayland-1.26.0.tar.xz', 'usr/lib/libwayland-client.so.0'),
    'wayland-protocols': ('1.49', 'wayland (>= 1.26.0-1+toddy1)',
                          'wayland-protocols-1.49.tar.xz', 'usr/share/pkgconfig/wayland-protocols.pc'),
    'libxml2': ('2.15.3', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1)',
               'libxml2-2.15.3.tar.xz', 'usr/lib/pkgconfig/libxml-2.0.pc'),
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
    qualifier='wayland-recheck-2' if name=='wayland' else name+'-1'
    assert (log / (qualifier+'.exit')).read_text().strip() == '0', 'Reconcile actual compiler/test exit first'
    if name=='wayland':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/wayland-1/qualified-tests.json').read_text())
        assert proof['total']==26 and proof['original_passed']==6 and proof['corrected_passed']==20 and proof['compiled_binaries_unchanged']
        command=json.loads((log/'wayland-recheck-2.job.json').read_text())['command']
        assert command[-1]==(ROOT/'scripts/build/phase2/wayland-recheck.sh').read_text()
    if name in ('wayland-protocols','pixman'):
        rows=[json.loads(line) for line in (Path('/mnt/lfs/sources/phase2/work')/(name+'-1')/'compile/meson-logs/testlog.json').read_text().splitlines()]
        assert rows and all(r['result']=='OK' and r['returncode']==0 and not r['is_fail'] for r in rows)
    if name=='freetype':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/freetype-1/test-results.json').read_text())
        assert proof['staged_consumer_exit']==0 and proof['upstream_suite']=='not provided'
    if name=='libpng':
        counts=json.loads(Path('/mnt/lfs/sources/phase2/work/libpng-1/test-results.json').read_text())
        assert counts['TOTAL']>0 and counts['TOTAL']==counts['PASS']
        assert all(counts[k]==0 for k in ['SKIP','XFAIL','FAIL','XPASS','ERROR'])
    if name=='libxml2':
        status=json.loads((ROOT/'status.json').read_text())
        assert status['owner_review']['phase_2_approved'] is True
        assert next(r for r in status['milestones'] if r['id']=='B02')['status']=='in_progress'
        work=Path('/mnt/lfs/sources/phase2/work/libxml2-1')
        tests=json.loads((work/'test-results.json').read_text())
        assert {t['name'] for t in tests}=={'testdict','testchar','testparser','testrecurse','testcatalog','testapi','runtest'}
        assert len(tests)==7 and all(t['exit']==0 for t in tests)
        assert (work/'test-logs/runtest.log').read_text().rstrip().endswith('Total 3904 tests, no errors')
    source = Path('/mnt/lfs/sources/phase2/work') / (name+'-1') / 'stage'
    before = inspect_stage(source)
    assert required in before['entries'], 'Missing declared payload'
    destination = Path('/mnt/lfs/sources/stage') / ('phase2-'+name)
    assert not destination.exists(), 'Reconcile existing stage; no replay'
    shutil.copytree(source, destination, symlinks=True)
    assert inspect_stage(destination) == before
    (log / (name+'-stage.json')).write_text(json.dumps(before, indent=2)+'\n')
    if name=='libxml2':
        wrapper=destination/'usr/bin/xml2-config'
        wrapper.write_text(wrapper.read_text().replace('--static','--shared'))
    if name=='freetype':
        doc=destination/'usr/share/doc/freetype';doc.mkdir(parents=True,exist_ok=True)
        (doc/'README.Toddy').write_text('This software is based in part on the work of the FreeType Team.\nPortions copyright 1996-2026 The FreeType Project (https://freetype.org). All rights reserved.\nFTL license option selected; exact upstream terms in copyright/source-notices.\nSource modifications: enabled gxvalid/otvalid modules and FT_CONFIG_OPTION_SUBPIXEL_RENDERING per BLFS13.1.\nDynamic HarfBuzz loading; optional reference manual not included.\n')
    write_copyright(destination, name, [archive])
    subprocess.run([sys.executable, str(ROOT/'scripts/build/stage_package.py'), name,
                    version+'-1+toddy1', str(destination), '--source', archive,
                    '--recipe', 'scripts/build/phase2/'+name+'-install.sh',
                    '--depends', depends, '--install'], cwd=ROOT, check=True)
