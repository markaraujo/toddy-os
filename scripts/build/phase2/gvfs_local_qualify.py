"""Reuse original local passes; retain append-position failure and run only remainder."""
from pathlib import Path
import hashlib,json,os,re,subprocess

work=Path('/build')
assert os.geteuid()==101 and not (work/'stage-results.json').exists()
assert json.loads((work/'resources.json').read_text())[0]['exit']==0
assert json.loads((work/'resources.json').read_text())[1]['exit']==0
original=(work/'outputstream.stdout').read_text()
prefix=re.findall(r'^ok\s+\d+\s+([^\n]+)',original,re.M)
assert len(prefix)==11 and prefix[-1]=='/write/append-truncate'
assert 'not ok /write/append-tell' in original and '(0 == 26)' in original
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
artifacts={str(p.relative_to(work/'compile')):digest(p) for p in (work/'compile').rglob('*')
           if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}
stage={str(p.relative_to('/stage')):digest(p) for p in Path('/stage').rglob('*')
       if p.is_file() and not p.is_symlink()}
assert 'usr/libexec/gvfsd-trash' in stage and 'usr/libexec/gvfsd-admin' in stage
directory=work/'remaining-local-data';directory.mkdir()
runs=[]
for suffix in ['nonexistent','existent-file','existent-dir','seek','truncate','tell']:
    name='/write/replace-'+suffix
    r=subprocess.run([str(work/'compile/test/unit/outputstream'),str(directory),'-p',name],
                     capture_output=True,text=True,timeout=20)
    row={'name':name,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    runs.append(row)
    (work/'remaining-local-results.json').write_text(json.dumps(runs,indent=2)+'\n')
    assert r.returncode==0 and re.search(r'^ok 1 '+re.escape(name)+r'\s*$',r.stdout,re.M)
    assert not re.search(r'(?im)\b(?:SKIP|TODO)\b|^not ok',r.stdout)
probe=work/'local-append-probe'
source=work/'local-append-probe.c'
flags=subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0'],text=True).split()
subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(probe),*flags],check=True)
linked=subprocess.check_output(['ldd',str(probe)],text=True)
assert 'gvfs' not in linked and 'not found' not in linked
r=subprocess.run([str(probe),str(directory/'append-proof')],capture_output=True,text=True,timeout=15)
assert r.returncode==0 and 'append_preserves_prior_bytes=true' in r.stdout
assert all(digest(work/'compile'/p)==sha for p,sha in artifacts.items())
assert all(digest(Path('/stage')/p)==sha for p,sha in stage.items())
proof={'scope':'Original local-file outputstream11passes reused plus six previously unrun replace cases. Original append-tell failure remains unqualified (baseline GLocalVfs initial offset0 versus expected26). Separate GLib-only byte-append consumer preserves prior bytes. No new Gvfs backend/native Trash/admin/network acceptance.',
       'compile_exit':0,'stage_exit':0,'reused_original_cases':prefix,'remaining_original_runs':runs,
       'original_cases_passed':17,'original_append_tell_failed':True,
       'baseline_append_consumer':{'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'linkage':linked},
       'artifacts':artifacts,'stage_sha256':stage,'resources':json.loads((work/'resources.json').read_text()),
       'original_compiler_stage_unchanged_during_followup':True}
(work/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'passed_original_cases':17,'original_append_tell_failed':True,
                  'baseline_append_bytes_preserved':True,'ELFs':len(artifacts),'stage_files':len(stage)}))
