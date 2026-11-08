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
from llvm_recover import merge_support_results
from rust_std_tests import qualify_preserved_log

ROOT = Path('/opt/toddy-build')
PROFILES = {
    'gdk-pixbuf': ('2.44.7', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), libpng (>= 1.6.58-1+toddy1), libjpeg-turbo (= 3.2.0-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)',
                    'gdk-pixbuf-2.44.7.tar.xz', 'usr/lib/girepository-1.0/GdkPixbuf-2.0.typelib'),
    'libepoxy': ('1.5.10', 'glibc (>= 2.44-1), mesa (= 26.1.7-1+toddy1)',
                 'libepoxy-1.5.10.tar.xz', 'usr/lib/libepoxy.so.0'),
    'mesa': ('26.1.7', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), llvm-runtime (= 22.1.8-1+toddy1), libdrm (= 2.4.134-1+toddy1), wayland (>= 1.26.0-1+toddy1), systemd (>= 261.2-1), libelf (>= 0.195-1), expat (>= 2.10.0-1), zlib (>= 1.3.2-1), zstd (>= 1.5.7-1)',
             'mesa-26.1.7.tar.xz', 'usr/lib/libEGL.so.1'),
    'pyyaml': ('6.0.3', 'python (>= 3.14), python (<< 3.15)',
               'pyyaml-6.0.3.tar.gz', 'usr/lib/python3.14/site-packages/yaml/__init__.py'),
    'libpciaccess': ('0.19', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1)',
                     'libpciaccess-0.19.tar.xz', 'usr/lib/libpciaccess.so.0'),
    'libdrm': ('2.4.134', 'glibc (>= 2.44-1), libpciaccess (= 0.19-1+toddy1)',
                'libdrm-2.4.134.tar.xz', 'usr/lib/libdrm_intel.so.1'),
    'mako': ('1.4.1', 'python (>= 3.14), python (<< 3.15), markupsafe (>= 2.0)',
              'mako-1.4.1.tar.gz', 'usr/lib/python3.14/site-packages/mako/__init__.py'),
    'rustc': ('1.97.1', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), llvm-runtime (= 22.1.8-1+toddy1), curl (>= 8.23.0-1), openssl (>= 4.0.3-1), sqlite (>= 3.53.4-1), zlib (>= 1.3.2-1)',
               'rustc-1.97.1-src.tar.xz', 'usr/bin/rustc'),
    'dejavu-fonts': ('2.37', 'fontconfig (>= 2.18.3-1+toddy1)',
                     'dejavu-fonts-ttf-2.37.tar.bz2', 'usr/share/fonts/dejavu/DejaVuSerif.ttf'),
    'psutil': ('7.2.2', 'python (>= 3.14), python (<< 3.15), glibc (>= 2.44-1)',
               'psutil-7.2.2.tar.gz', 'usr/lib/python3.14/site-packages/psutil/__init__.py'),
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
    llvm_resume=name=='llvm' and (log/'llvm-qualify-resume-3.job.json').exists()
    llvm_recovery=name=='llvm' and (log/'llvm-qualify-recovery-4.job.json').exists()
    rust_legacy=name=='rustc' and (log/'rustc-tools-finish-8.job.json').exists()
    mako_resume=name=='mako' and (log/'mako-resume-2.job.json').exists()
    qualifier=('rustc-tools-finish-8' if rust_legacy else 'rustc-stage-4') if name=='rustc' else 'mako-resume-2' if mako_resume else 'pango-stage-6' if name=='pango' else 'llvm-qualify-recovery-4' if llvm_recovery else 'llvm-qualify-resume-3' if llvm_resume else 'llvm-qualify-2' if name=='llvm' else 'wayland-recheck-2' if name=='wayland' else 'harfbuzz-resume-2' if name=='harfbuzz' else name+'-1'
    mesa_resume=name=='mesa' and (log/'mesa-resume-2.job.json').exists()
    if mesa_resume:qualifier='mesa-resume-2'
    mesa_finish=name=='mesa' and (log/'mesa-finish-3.job.json').exists()
    if mesa_finish:qualifier='mesa-finish-3'
    pci_resume=name=='libpciaccess' and (log/'libpciaccess-resume-2.job.json').exists()
    if pci_resume:qualifier='libpciaccess-resume-2'
    assert (log / (qualifier+'.exit')).read_text().strip() == '0', 'Reconcile actual compiler/test exit first'
    if name=='rustc':
        work=Path('/mnt/lfs/sources/phase2/work/rustc-1')
        assert (log/'rustc-1.exit').read_text().strip()=='0'
        assert (log/'rustc-compiler-3.exit').read_text().strip()=='0'
        std_exit=(log/'rustc-std-2.exit').read_text().strip()
        if std_exit=='1':
            assert 'stage2/bin/clippy-driver' in (log/'rustc-std-2.log').read_text()
        else:
            assert std_exit=='0'
            assert (work/'std-tests-2-native.exit').read_text().strip()=='0'
        summaries=qualify_preserved_log((work/'std-tests-2.log').read_text())
        assert sum(r['passed'] for r in summaries)==6223
        assert sum(r['ignored'] for r in summaries)==5
        compiler=json.loads((work/'compiler-tests-3/results.json').read_text())
        assert compiler['native_exit']==0
        assert compiler['summaries']==[['ok','1552','0','7','0','19666']]
        assert (work/'compiler-tests-3/native.exit').read_text().strip()=='0'
        assert hashlib.sha256((work/'compiler-tests-3/native.log').read_bytes()).hexdigest()==compiler['log_sha256']
        assert json.loads((log/'rustc-compiler-3.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/rust_compiler_tests.py').read_text()
        canonical_probe=(ROOT/'scripts/build/phase2/rust_tools_probe.py').read_text()
        stage_job=json.loads((log/'rustc-stage-4.job.json').read_text())
        if rust_legacy:
            for job in ['rustc-stage-4','rustc-tools-recovery-5','rustc-tools-recovery-6','rustc-tools-recovery-7']:
                assert (log/(job+'.exit')).read_text().strip()=='1'
            assert hashlib.sha256(stage_job['command'][-3].encode()).hexdigest()=='b081cf6b85698b41a927d587fbf5593e359c565c38bf30e00689e5e5c6d1c1c4'
            proof=json.loads((work/'tool-docs-8/qualified.json').read_text())
            assert proof['qualification_exit']==0 and proof['rustdoc_native_exit']==0
            assert proof['stage_unchanged_by_probe']
            assert proof['original_wrapper_exits']=={'stage4':1,'guard5':1,'probe6':1,'collector7':1}
            record=json.loads((log/'rustc-tools-finish-8.job.json').read_text())
            assert record['command'][-3]==(ROOT/'scripts/build/phase2/rust_finish_tools.py').read_text()
            assert record['command'][-2]==canonical_probe
            assert record['command'][-1]==canonical_probe.replace("101, 'clippy::eq-op'", "101, 'clippy::eq_op'")
            assert json.loads((log/'rustc-tools-recovery-7.job.json').read_text())['command'][-2]==record['command'][-1]
            assert hashlib.sha256((work/'stage-tests-recovery-7/tools.log').read_bytes()).hexdigest()==proof['previous_tools_log_sha256']
            expected={'c-ffi-compile':0,'c-ffi-archive':0,'rustfmt-reject':1,'rustfmt-format':0,
                      'rustfmt-check':0,'cargo-test':0,'cargo-clippy':0,'clippy-reject':101,'rustdoc':0}
            assert {r['name'] for r in proof['checks']}==set(expected) and len(proof['checks'])==9
            for row in proof['checks']:
                name_=row['name']
                directory=work/('tool-docs-8' if name_=='rustdoc' else 'tool-consumers-7')
                assert hashlib.sha256((directory/(name_+'.log')).read_bytes()).hexdigest()==row['log_sha256']
                assert row.get('native_exit',row.get('expected_exit'))==expected[name_]
            assert (work/'tool-docs-8/rustdoc.exit').read_text().strip()=='0'
        else:
            proof=json.loads((work/'stage-tests-4/results.json').read_text())
            assert proof['install_exit']==0 and proof['tools_exit']==0
            assert stage_job['command'][-3]==(ROOT/'scripts/build/phase2/rust_stage.py').read_text()
            assert stage_job['command'][-2]==canonical_probe
            assert (work/'stage-tests-4/tools.exit').read_text().strip()=='0'
            assert hashlib.sha256((work/'stage-tests-4/tools.log').read_bytes()).hexdigest()==proof['tools_log_sha256']
        assert proof['probe_sha256']==hashlib.sha256(canonical_probe.encode()).hexdigest()
        assert (work/'stage-tests-4/install.exit').read_text().strip()=='0'
        assert hashlib.sha256((work/'stage-tests-4/install.log').read_bytes()).hexdigest()==proof['install_log_sha256']
        actual={str(p.relative_to(work/'stage')) for p in (work/'stage').rglob('*')
                if p.is_file() or p.is_symlink()}
        assert actual==set(proof['entries']), 'Unexpected stage payload'
        for relative,row in proof['entries'].items():
            path=work/'stage'/relative
            assert path.is_relative_to(work/'stage') and '..' not in Path(relative).parts
            if 'symlink' in row:assert path.is_symlink() and path.readlink().as_posix()==row['symlink']
            else:assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    if name in ('libpciaccess','libdrm'):
        work=Path('/mnt/lfs/sources/phase2/work')/(name+'-1')
        input_=Path('/mnt/lfs/sources/phase2/inputs')/(name+'-'+version)
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2'/(name+'-build.sh')).read_bytes()
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2'/(name+'-probe.c')).read_bytes()
        assert json.loads((log/(name+'-1.job.json')).read_text())['command'][-1]=='/src/toddy-build.sh'
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==0
        if name=='libdrm':
            assert proof['registered_upstream_tests']>3
            assert proof['log_sha256']==hashlib.sha256((work/'compile/meson-logs/testlog.json').read_bytes()).hexdigest()
            assert all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in proof['tests'])
        else:
            assert proof['registered_upstream_tests']==0
            if pci_resume:
                assert (log/'libpciaccess-1.exit').read_text().strip()=='1'
                assert 'toddy-probe.c: No such file or directory' in (log/'libpciaccess-1.log').read_text()
                assert json.loads((log/'libpciaccess-resume-2.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/libpciaccess-resume.sh').read_text()
                assert proof['stage_regular_files_unchanged']>0

    if name=='mesa':
        input_=Path('/mnt/lfs/sources/phase2/inputs/mesa-26.1.7')
        work=Path('/mnt/lfs/sources/phase2/work/mesa-1')
        canonical=(ROOT/'scripts/build/phase2/mesa-build.sh').read_text()
        if mesa_resume:
            assert (log/'mesa-1.exit').read_text().strip()=='1'
            assert hashlib.sha256((input_/'toddy-build.sh').read_bytes()).hexdigest()=='40f33d0c1b92b6e3f6107069f094a5632f2e19d1f5b631d291d272382f864744'
            added='# These registered test dependencies are explicitly build_by_default:false.\nninja -C /build/compile -j4 src/compiler/glsl/glcpp/glcpp src/compiler/glsl/glsl_compiler\n'
            assert canonical.count(added)==1 and canonical.count(' -Wl,-rpath-link,/stage/usr/lib')==1
            assert canonical.replace(added,'').replace(' -Wl,-rpath-link,/stage/usr/lib','')==(input_/'toddy-build.sh').read_text()
            recovery_job=json.loads((log/'mesa-resume-2.job.json').read_text())
            assert recovery_job['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/mesa_resume.py').read_text()]
            assert recovery_job['harness_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
        else:
            assert (input_/'toddy-build.sh').read_text()==canonical
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/mesa-probe.c').read_bytes()
        job=json.loads((log/'mesa-1.job.json').read_text())
        assert job['command'][-1]=='/src/toddy-build.sh'
        assert job['harness_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['consumer_exit']==0 and proof['registered_tests']>10
        assert all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in proof['tests'])
        path=work/'compile/meson-logs/testlog.json'
        assert proof['upstream_log_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        if mesa_resume:
            assert len(rows)==48 and sum(r['result']=='OK' and r['returncode']==0 for r in rows)==43
            failed=[r for r in rows if r['result']!='OK']
            assert len(failed)==5 and all(r['returncode']==1 and 'FileNotFoundError' in r['stderr'] for r in failed)
            corrected_path=work/'compile/meson-logs/testlog-recovery-2.json'
            corrected=[json.loads(line) for line in corrected_path.read_text().splitlines()]
            assert len(corrected)==5 and all(r['result']=='OK' and r['returncode']==0 for r in corrected)
            assert {r['name'] for r in failed}=={r['name'] for r in corrected}
            assert proof['affected_recheck']['log_sha256']==hashlib.sha256(corrected_path.read_bytes()).hexdigest()
            merged={r['name']:{k:r[k] for k in ['name','result','returncode']} for r in rows}
            for r in corrected:merged[r['name']]={k:r[k] for k in ['name','result','returncode']}
            assert list(merged.values())==proof['tests'] and proof['original_wrapper_exit']==1
            for label in ['missing-test-tools','affected-tests','first-stage']:
                assert (work/'mesa-recovery-2'/(label+'.exit')).read_text().strip()=='0'
            if mesa_finish:
                assert (log/'mesa-resume-2.exit').read_text().strip()=='1'
                assert (work/'mesa-recovery-2/consumer-compile.exit').read_text().strip()=='1'
                final_job=json.loads((log/'mesa-finish-3.job.json').read_text())
                assert final_job['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/mesa_finish.py').read_text()]
                assert final_job['harness_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
                for label in ['consumer-compile','render']:
                    assert (work/'mesa-finish-3'/(label+'.exit')).read_text().strip()=='0'
                assert proof['stage_unchanged_by_consumer'] and proof['consumer_runtime_rpath'] is False
                from xorg_sdk_build import entries as stage_entries
                assert stage_entries(work/'stage')==proof['stages']
            else:
                for label in ['consumer-compile','render']:
                    assert (work/'mesa-recovery-2'/(label+'.exit')).read_text().strip()=='0'
        else:
            assert [{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows]==proof['tests']
        assert proof['native_render_sha256']==hashlib.sha256((work/'native-render.log').read_bytes()).hexdigest()
        assert 'renderer: llvmpipe' in proof['native_render_stdout']
        binaries=json.loads((work/'compiled-binaries.json').read_text())
        assert len(binaries)==proof['unchanged_compiled_elfs']
        for relative,sha in binaries.items():
            path=work/relative
            assert path.resolve().is_relative_to(work) and not path.is_symlink()
            with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
    if name=='gdk-pixbuf':
        input_=Path('/mnt/lfs/sources/phase2/inputs/gdk-pixbuf-2.44.7')
        work=Path('/mnt/lfs/sources/phase2/work/gdk-pixbuf-1')
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/gdk-pixbuf-build.sh').read_bytes()
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/gdk-pixbuf-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==0 and proof['registered_tests']>10
        assert proof['upstream_log_sha256']==hashlib.sha256((work/'compile/meson-logs/testlog.json').read_bytes()).hexdigest()
        assert all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in proof['tests'])
        cache=work/'stage'/proof['generated_cache']['path']
        assert cache.resolve().is_relative_to(work/'stage') and not cache.is_symlink()
        assert hashlib.sha256(cache.read_bytes()).hexdigest()==proof['generated_cache']['sha256']
        assert proof['generated_cache']['external_module_records']==0
    if name=='libepoxy':
        input_=Path('/mnt/lfs/sources/phase2/inputs/libepoxy-1.5.10')
        work=Path('/mnt/lfs/sources/phase2/work/libepoxy-1')
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libepoxy-build.sh').read_bytes()
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libepoxy-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==0 and proof['registered_tests']==4
        assert proof['upstream_log_sha256']==hashlib.sha256((work/'compile/meson-logs/testlog.json').read_bytes()).hexdigest()
        assert all(r['result']=='OK' and r['returncode']==0 for r in proof['tests'])
        assert 'renderer: llvmpipe' in proof['native_render_stdout']
    if name=='pyyaml':
        input_=Path('/mnt/lfs/sources/phase2/inputs/pyyaml-6.0.3')
        work=Path('/mnt/lfs/sources/phase2/work/pyyaml-1')
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/pyyaml-build.sh').read_bytes()
        assert (input_/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/pyyaml-probe.py').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['native_exit']==0 and proof['upstream_boolean_result'] and proof['pure_python_upstream_cases']>1000
        assert proof['upstream_log_sha256']==hashlib.sha256((work/'upstream-tests.log').read_bytes()).hexdigest()
        assert proof['staged_consumer']['uid']==101 and proof['staged_consumer']['version']=='6.0.3'
        assert proof['staged_consumer']['safe_unicode_roundtrip'] and proof['staged_consumer']['unsafe_constructor_rejected']
    if name=='psutil':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/psutil-1/consumer.json').read_text())
        assert proof['version']=='7.2.2' and proof['uid']==101
        assert proof['own_process_memory_cpu'] and proof['timeout_then_terminate_exit']==-15
        assert proof['recursive_child_kill_and_reap']
    if name=='mako':
        source=Path('/mnt/lfs/sources/phase2/inputs/mako-1.4.1')
        work=Path('/mnt/lfs/sources/phase2/work/mako-1')
        proof=json.loads((work/'consumer.json').read_text())
        assert proof['version']=='1.4.1' and proof['uid']==101 and proof['c_consumer_exit']==0
        assert proof['checks']==['unicode-expression','html-escape','loop','lookup-inheritance-cache',
                                 'invalid-syntax-rejected','generated-c-compile-execute']
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/mako-build.sh').read_bytes()
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/mako-probe.py').read_bytes()
        assert json.loads((log/'mako-1.job.json').read_text())['command'][-1]=='/src/toddy-build.sh'
        if mako_resume:
            assert (log/'mako-1.exit').read_text().strip()=='1'
            assert 'Permission denied' in (log/'mako-1.log').read_text()
            assert json.loads((log/'mako-resume-2.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/mako-resume.sh').read_text()
        receipt=json.loads((source/'toddy-prepared.json').read_text())
        assert receipt['source_patches']==[{'path':'doc/build/changelog.rst','before_mode':0o600,'after_mode':0o644,
                'content_sha256':'a5620499d6c083972b0ba7ea307b99b06e783966fa46b3e5c73d00fe96f51e31',
                'reason':'Public release doc is owner-readable only; expose unchanged bytes to unprivileged read-only-input compiler'}]
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
    if name=='dejavu-fonts':
        work=Path('/mnt/lfs/sources/phase2/work/dejavu-fonts-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/dejavu-fonts-ttf-2.37')
        proof=json.loads((work/'font-inputs.json').read_text())
        expected={'DejaVuSerif.ttf','DejaVuSerif-Bold.ttf',
                  'DejaVuSerif-Italic.ttf','DejaVuSerif-BoldItalic.ttf'}
        assert proof['source_fonts_byte_identical']
        assert {r['file'] for r in proof['fonts']}==expected and len(proof['fonts'])==4
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/dejavu-fonts-build.sh').read_bytes()
        assert json.loads((log/'dejavu-fonts-1.job.json').read_text())['command'][-1]=='/src/toddy-build.sh'
        for row in proof['fonts']:
            path=work/'stage/usr/share/fonts/dejavu'/row['file']
            assert path.parent==work/'stage/usr/share/fonts/dejavu'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
            assert path.read_bytes()==(source/'ttf'/row['file']).read_bytes()
    if name=='llvm':
        assert (log/'llvm-1.exit').read_text().strip()=='0'
        if llvm_resume or llvm_recovery:assert (log/'llvm-qualify-2.exit').read_text().strip()=='1'
        if llvm_recovery:assert (log/'llvm-qualify-resume-3.exit').read_text().strip()=='1'
        recipe='llvm_recover.py' if llvm_recovery else 'llvm-resume.sh' if llvm_resume else 'llvm-qualify.sh'
        assert json.loads((log/(qualifier+'.job.json')).read_text())['command'][-1]==(ROOT/'scripts/build/phase2'/recipe).read_text()
        work=Path('/mnt/lfs/sources/phase2/work/llvm-1')
        directory=work/('critical-tests-recovery-4' if llvm_recovery else 'critical-tests-resume' if llvm_resume else 'critical-tests')
        proof=json.loads((directory/'qualified.json').read_text())
        required_suites={'llvm-unit','clang-unit','llvm-transforms','llvm-x86','llvm-execution-engine','clang-codegen','clang-codegen-cxx'}
        assert {r['name'] for r in proof['suites']}==required_suites and len(proof['suites'])==7
        assert proof['required_poison_select_regression']=='PASS'
        if llvm_recovery:
            assert proof['binaries_unchanged'] and proof['unit_recovery']['cwd']=='/build/compile'
            original=work/'critical-tests-resume/llvm-unit.json';corrected=directory/'llvm-unit-support.json'
            recovery=proof['unit_recovery']
            assert hashlib.sha256(original.read_bytes()).hexdigest()==recovery['original_report_sha256']
            assert hashlib.sha256(corrected.read_bytes()).hexdigest()==recovery['affected_report_sha256']
            merged=merge_support_results(json.loads(original.read_text())['tests'],json.loads(corrected.read_text())['tests'])
            derived=json.loads((directory/'llvm-unit.json').read_text())
            assert derived['tests']==merged and derived['qualification']==recovery
            for path,sha in proof['binary_inputs'].items():
                assert path.startswith('/build/compile/')
                actual=work/path.removeprefix('/build/')
                assert actual.resolve().is_relative_to((work/'compile').resolve())
                assert hashlib.sha256(actual.read_bytes()).hexdigest()==sha
        for row in proof['suites']:
            report=directory/(row['name']+'.json');raw=report.read_bytes()
            assert hashlib.sha256(raw).hexdigest()==row['report_sha256']
            tests=json.loads(raw)['tests'];counts=dict(collections.Counter(t['code'] for t in tests))
            if llvm_recovery and row['name']=='llvm-unit':
                assert row['qualification_exit']==0 and row['original_native_exit']==1 and row['affected_native_exit']==0
            else:assert row['exit']==0
            assert tests and counts==row['counts'] and counts.get('PASS',0)>0
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
    assert not (source/'.toddy-retired.json').exists(),'Stage retired under verified archive custody; reuse the native package, no promotion replay'
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
    if name in ('fontconfig','llvm','rustc'):
        for relative,row in before['entries'].items():
            if relative.startswith('etc/') and 'sha256' in row: conffiles+=['--conffile','/'+relative]
    subprocess.run([sys.executable, str(ROOT/'scripts/build/stage_package.py'), name,
                    version+'-1+toddy1', str(destination), *source_args,
                    '--recipe', 'scripts/build/phase2/'+name+'-install.sh',
                    '--depends', depends, '--install', *conffiles], cwd=ROOT, check=True)
