"""Recover only the custom data probe; never rebuild/restage original artifacts."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess


def main():
    assert os.getuid()==101
    work=Path('/build');source=Path('/src')
    def sha(p):
        with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    def artifacts():
        result={}
        for p in (work/'compile').rglob('*'):
            if not p.is_file() or p.is_symlink():continue
            with p.open('rb') as f:is_elf=f.read(4)==b'\x7fELF'
            if is_elf:result[str(p.relative_to(work))]=sha(p)
        return result
    def stage():
        return {str(p.relative_to(work/'stage')):sha(p) for p in (work/'stage').rglob('*') if p.is_file() and not p.is_symlink()}
    before=artifacts();payload=stage();assert len(before)>=27 and len(payload)>50
    env={**os.environ,'PKG_CONFIG_PATH':'/stage/usr/lib/pkgconfig','LD_LIBRARY_PATH':'/stage/usr/lib'}
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','gtksourceview-5'],env=env,text=True))
    subprocess.run(['cc','-Wall','-Wextra','-Werror',str(source/'toddy-probe.c'),'-o','/build/native-consumer-2','-I/stage/usr/include/gtksourceview-5','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',*flags],env=env,check=True)
    with (work/'native-consumer-2.log').open('xb') as log:subprocess.run(['/build/native-consumer-2'],env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
    env['GI_TYPELIB_PATH']='/stage/usr/lib/girepository-1.0'
    code="import gi;gi.require_version('GtkSource','5');from gi.repository import GtkSource;assert (GtkSource.get_major_version(),GtkSource.get_minor_version(),GtkSource.get_micro_version())==(5,20,0);assert GtkSource.Encoding.get_from_charset('UTF-8') is not None;assert GtkSource.Encoding.get_from_charset('TODDY-INVALID-ENCODING') is None"
    with (work/'native-gi-2.log').open('xb') as log:subprocess.run(['python3','-B','-c',code],env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
    assert before==artifacts() and payload==stage()
    registered=json.loads((work/'compile/meson-info/intro-tests.json').read_text());assert len(registered)==26
    proof={'scope':'Native compile/data/ABI only; original26display drivers pending, no promotion/editor UI acceptance','native_build_exit':0,'stage_exit':0,'c_version_data_exit':0,'gi_version_exit':0,'upstream_tests_state':'pending_native_display','registered_tests_pending':[r['name'] for r in registered],'compiled_elf_sha256':before,'compiled_elf_files_unchanged':len(before),'stage_regular_files_unchanged':len(payload),'probe_recovery':'Custom probe incorrectly replaced embedded resource language search path with schemas-only filesystem directory. Restore supported default resource path, no library/original test/data changes.'}
    (work/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')

if __name__=='__main__':main()
