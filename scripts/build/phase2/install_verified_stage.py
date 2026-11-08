#!/usr/bin/env python3
"""Promote a declared successful compiler stage through the native backend only.

Invoked inside run_step's full-root transaction, never by the compiler namespace.
"""
import collections
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from verify_stage import inspect_stage
from package_copyright import write_copyright
from llvm_runtime import split_runtime

ROOT = Path('/opt/toddy-build')
PROFILES = {
    'libjpeg-turbo': ('3.2.0', 'glibc (>= 2.44-1)',
                      'libjpeg-turbo-3.2.0.tar.gz', 'usr/lib/libjpeg.so'),
    'adwaita-fonts': ('50.0', 'fontconfig (>= 2.18.3-1+toddy1)',
                      'adwaita-fonts-50.0.tar.xz', 'usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf'),
    'llvm': ('22.1.8', 'llvm-runtime (= 22.1.8-1+toddy1), glibc (>= 2.44-1), gcc (>= 16.2.0-1)',
             'llvm-project-22.1.8.src.tar.xz', 'usr/bin/llvm-config'),
    'shared-mime-info': ('2.5.1', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), glib (>= 2.88.3-1+toddy1), libxml2 (>= 2.15.3-1+toddy1)',
                         'shared-mime-info-2.5.1.tar.gz', 'usr/share/mime/mime.cache'),
    'graphene': ('1.10.8', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1)',
                 'graphene-1.10.8.tar.xz', 'usr/lib/girepository-1.0/Graphene-1.0.typelib'),
    'pango': ('1.58.2', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), freetype (>= 2.14.3-1+toddy1), fontconfig (>= 2.18.3-1+toddy1), fribidi (>= 1.0.16-1+toddy1), harfbuzz (>= 14.3.1-1+toddy1), cairo (>= 1.18.4-1+toddy1), gi-desktop-types (>= 1.86.0-1+toddy1)',
              'pango-1.58.2.tar.xz', 'usr/lib/girepository-1.0/PangoCairo-1.0.typelib'),
    'gi-desktop-types': ('1.86.0', 'gobject-introspection (>= 1.86.0-1+toddy1), freetype (>= 2.14.3-1+toddy1), fontconfig (>= 2.18.3-1+toddy1), libxml2 (>= 2.15.3-1+toddy1), cairo (>= 1.18.4-1+toddy1)',
                        'gobject-introspection-1.86.0.tar.xz', 'usr/lib/girepository-1.0/freetype2-2.0.typelib'),
    'cairo': ('1.18.4', 'glibc (>= 2.44-1), pixman (>= 0.46.4-1+toddy1), libpng (>= 1.6.58-1+toddy1), freetype (>= 2.14.3-1+toddy1), fontconfig (>= 2.18.3-1+toddy1), glib (>= 2.88.3-1+toddy1), zlib (>= 1.3.2-1)',
              'cairo-1.18.4.tar.xz', 'usr/lib/pkgconfig/cairo-gobject.pc'),
    'harfbuzz': ('14.3.1', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), freetype (>= 2.14.3-1+toddy1), zlib (>= 1.3.2-1)',
                 'harfbuzz-14.3.1.tar.xz', 'usr/lib/girepository-1.0/HarfBuzz-0.0.typelib'),
    'fribidi': ('1.0.16', 'glibc (>= 2.44-1)',
                'fribidi-1.0.16.tar.xz', 'usr/lib/pkgconfig/fribidi.pc'),
    'fontconfig': ('2.18.3', 'glibc (>= 2.44-1), freetype (>= 2.14.3-1+toddy1), libxml2 (>= 2.15.3-1+toddy1)',
                   'fontconfig-2.18.3.tar.xz', 'usr/lib/pkgconfig/fontconfig.pc'),
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
    qualifier='pango-stage-6' if name=='pango' else 'llvm-qualify-2' if name=='llvm' else 'wayland-recheck-2' if name=='wayland' else 'harfbuzz-resume-2' if name=='harfbuzz' else name+'-1'
    assert (log / (qualifier+'.exit')).read_text().strip() == '0', 'Reconcile actual compiler/test exit first'
    if name=='libjpeg-turbo':
        import xml.etree.ElementTree as ET
        work=Path('/mnt/lfs/sources/phase2/work/libjpeg-turbo-1')
        report=ET.fromstring((work/'ctest.xml').read_bytes())
        assert report.tag=='testsuite' and int(report.get('tests'))>0
        assert all(int(report.get(k,'0'))==0 for k in ['failures','errors','disabled','skipped'])
        cases=report.findall('testcase');assert len(cases)==int(report.get('tests'))
        assert all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases)
        source=Path('/mnt/lfs/sources/phase2/inputs/libjpeg-turbo-3.2.0')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libjpeg-turbo-build.sh').read_bytes()
    if name=='pango':
        assert (log/'pango-1.exit').read_text().strip()=='1'
        assert (log/'pango-metric-oracle-5.exit').read_text().strip()=='0'
        assert json.loads((log/'pango-metric-oracle-5.job.json').read_text())['command'][-2:]==[(ROOT/'scripts/build/phase2/pango_metric_fixture.py').read_text(),'qualify']
        assert json.loads((log/'pango-stage-6.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/pango-stage.sh').read_text()
        work=Path('/mnt/lfs/sources/phase2/work/pango-1')
        proof=json.loads((work/'portable-qualified.json').read_text())
        assert proof['original_binaries_unchanged'] and (proof['core_passed'],proof['curated_passed'],proof['empty_drivers'],proof['portable_metric_cases_passed'])==(9,17,2,3)
        for relative,sha in proof['proofs'].items():
            assert (work/relative).resolve().is_relative_to(work.resolve())
            assert hashlib.sha256((work/relative).read_bytes()).hexdigest()==sha
        for path,sha in proof['binaries'].items():
            assert path.startswith('/build/')
            assert hashlib.sha256((work/path.removeprefix('/build/')).read_bytes()).hexdigest()==sha
    if name=='adwaita-fonts':
        work=Path('/mnt/lfs/sources/phase2/work/adwaita-fonts-1')
        proof=json.loads((work/'font-inputs.json').read_text())
        assert proof['source_fonts_byte_identical'] and len(proof['fonts'])==6
        assert json.loads((log/'adwaita-fonts-1.job.json').read_text())['command'][-1]=='/src/toddy-build.sh'
        for row in proof['fonts']:
            path=work/'stage/usr/share/fonts/Adwaita'/row['file']
            assert path.parent==work/'stage/usr/share/fonts/Adwaita'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    if name=='llvm':
        assert (log/'llvm-1.exit').read_text().strip()=='0'
        assert json.loads((log/'llvm-qualify-2.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/llvm-qualify.sh').read_text()
        directory=Path('/mnt/lfs/sources/phase2/work/llvm-1/critical-tests')
        proof=json.loads((directory/'qualified.json').read_text())
        required_suites={'llvm-unit','clang-unit','llvm-transforms','llvm-x86','llvm-execution-engine','clang-codegen','clang-codegen-cxx'}
        assert {r['name'] for r in proof['suites']}==required_suites and len(proof['suites'])==7
        assert proof['required_poison_select_regression']=='PASS'
        for row in proof['suites']:
            report=directory/(row['name']+'.json');raw=report.read_bytes()
            assert hashlib.sha256(raw).hexdigest()==row['report_sha256']
            tests=json.loads(raw)['tests'];counts=dict(collections.Counter(t['code'] for t in tests))
            assert row['exit']==0 and tests and counts==row['counts'] and counts.get('PASS',0)>0
            assert set(counts)<={'PASS','XFAIL','UNSUPPORTED'}
    if name=='harfbuzz':
        assert (log/'harfbuzz-1.exit').read_text().strip()=='1'
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/harfbuzz-1/dependency-recovery/qualified.json').read_text())
        assert proof['original_core_libraries_unchanged'] and proof['before']==proof['after']
        assert json.loads((log/'harfbuzz-resume-2.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/harfbuzz-resume.sh').read_text()
    if name=='wayland':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/wayland-1/qualified-tests.json').read_text())
        assert proof['total']==26 and proof['original_passed']==6 and proof['corrected_passed']==20 and proof['compiled_binaries_unchanged']
        command=json.loads((log/'wayland-recheck-2.job.json').read_text())['command']
        assert command[-1]==(ROOT/'scripts/build/phase2/wayland-recheck.sh').read_text()
    if name in ('wayland-protocols','pixman','fontconfig','fribidi','harfbuzz','graphene','shared-mime-info'):
        rows=[json.loads(line) for line in (Path('/mnt/lfs/sources/phase2/work')/(name+'-1')/'compile/meson-logs/testlog.json').read_text().splitlines()]
        if name=='harfbuzz':
            # Frozen BLFS optional FontTools is absent; upstream explicitly skips
            # only these Python-oracle repack drivers, not native API regressions.
            optional={'subset+repack - harfbuzz:'+n for n in ['basic','prioritization','table_duplication','isolation','advanced_prioritization','space_splitting','duplicate_before_mutation']}
            skipped={r['name'] for r in rows if r['result']=='SKIP'}
            assert skipped==optional
            assert len(rows)==218 and sum(r['result']=='OK' for r in rows)==211
            assert all(r['returncode']==0 and not r['is_fail'] and (r['result']=='OK' or (r['name'] in optional and r['result']=='SKIP' and r.get('stdout','').strip()=='# fonttools is not present, skipping test.')) for r in rows)
        else:
            assert rows and all(r['result']=='OK' and r['returncode']==0 and not r['is_fail'] for r in rows)
    if name=='gi-desktop-types':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/gi-desktop-types-1/test-results.json').read_text())
        assert {r['name'] for r in proof['types']}=={'freetype2-2.0','fontconfig-2.0','libxml2-2.0','cairo-1.0'}
        command=json.loads((log/'gi-desktop-types-1.job.json').read_text())['command']
        assert command[-1]==(ROOT/'scripts/build/phase2/gi-desktop-types-build.sh').read_text()
    if name=='cairo':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/cairo-1/test-results.json').read_text())
        assert proof['full_upstream_suite']=='not qualified; BLFS states not working'
        assert proof['registered_driver_failures']==0
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
    archives=[archive]
    if name in ('shared-mime-info','llvm'):
        extra_name='xdgmime-tests' if name=='shared-mime-info' else 'llvm-upstream-fix'
        row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==extra_name)
        archives.append(row['filename'])
    write_copyright(destination, name, archives)
    source_args=[arg for item in archives for arg in ['--source',item]]
    if name=='llvm':
        runtime=destination.with_name('phase2-llvm-runtime')
        partition=split_runtime(destination,runtime)
        write_copyright(runtime,'llvm-runtime',archives)
        (log/'llvm-runtime-partition.json').write_text(json.dumps(partition,indent=2)+'\n')
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'llvm-runtime',
                        version+'-1+toddy1',str(runtime),*source_args,
                        '--recipe','scripts/build/phase2/llvm-install.sh',
                        '--depends','glibc (>= 2.44-1), gcc (>= 16.2.0-1), libffi (>= 3.8.0-1), zlib (>= 1.3.2-1), zstd (>= 1.5.7-1)',
                        '--install'],cwd=ROOT,check=True)
    conffiles=[]
    if name in ('fontconfig','llvm'):
        for relative,row in before['entries'].items():
            if relative.startswith('etc/') and 'sha256' in row: conffiles+=['--conffile','/'+relative]
    subprocess.run([sys.executable, str(ROOT/'scripts/build/stage_package.py'), name,
                    version+'-1+toddy1', str(destination), *source_args,
                    '--recipe', 'scripts/build/phase2/'+name+'-install.sh',
                    '--depends', depends, '--install', *conffiles], cwd=ROOT, check=True)
