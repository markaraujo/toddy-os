"""Reconcile only an own count gate: five originals plus three original corpus drivers."""
from pathlib import Path
import hashlib,json
p=Path('/build');assert not (p/'stage-results.json').exists()
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
artifacts={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());assert len(rows)==len(registered)==8
assert {r['name'] for r in rows}=={'libpsl:'+r['name'] for r in registered} and all(r['result']=='OK' and r['returncode']==0 for r in rows)
consumer=json.loads((p/'native-consumer.json').read_text());assert consumer=={'builtin_public_suffix_and_registrable_domain':True,'public_suffix_cookie_refused':True,'ICU_UTF8_lowercase':True,'invalid_converter_refused':True,'private_runtime_wildcard_and_exception':True,'recovery_cycles':2}
stage={str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()};assert 'usr/lib/pkgconfig/libpsl.pc' in stage and 'usr/include/libpsl.h' in stage
assert {name:digest(p/'compile'/name) for name in artifacts}==artifacts
(p/'stage-results.json').write_text(json.dumps({'scope':'Eight original programs (five suffix/cookie/Unicode plus three finite corpus drivers, not a fuzz campaign); actual ICU/private-runtime-list/refusal/recovery, no browser/network acceptance','compile_exit':0,'stage_exit':0,'metadata_only_reconciliation':True,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':consumer,'artifacts':artifacts,'stage_sha256':stage},indent=2)+'\n')
