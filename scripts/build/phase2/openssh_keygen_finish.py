"""Reconcile only a whitespace-sensitive final version gate; no compiler/test replay."""
from pathlib import Path
import hashlib,json,re
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=Path('/build');assert not (p/'stage-results.json').exists()
version=Path('/src/version.h').read_text();assert re.search(r'#define SSH_VERSION\s+"OpenSSH_10[.]5"',version) and re.search(r'#define SSH_PORTABLE\s+"p1"',version)
programs=[]
for name,count in [('sshkey',101),('crypto',18)]:
 log=p/('original-'+name+'.log');text=log.read_text();assert re.search(r'^\s*'+str(count)+r' tests ok$',text,re.M)
 assert len(re.findall(r'^test \d+ .*: OK$',text,re.M))==count and not re.search(r'FAILED|FAILURE|not ok',text)
 programs.append({'name':name,'exit':0,'observed_original_cases':count,'log_sha256':digest(log)})
consumer=json.loads((p/'native-consumer.json').read_text());assert consumer=={'version':'10.5p1','ephemeral_ed25519_generate_derive_match':True,'malformed_key_refused':True,'recovery_fingerprint':True,'temporary_keys_removed':True,'key_material_retained':False,'scope':'Private keygen fixture tool only; no SSH network/client/server qualification'}
assert digest(p/'stage/private-test-sdk/bin/ssh-keygen')==digest(p/'compile/ssh-keygen')
assert not any((p/'compile'/name).exists() for name in ['sshd','sshd-session','sshd-auth'])
artifacts={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
assert artifacts
result={'scope':'Private keygen/crypto SDK only; final source version whitespace gate repaired without compile/test/stage/consumer replay. No installed OpenSSH package/server/network acceptance','compile_exit':0,'stage_exit':0,'source_version':'10.5p1','original_programs':programs,'consumer':consumer,'unchanged_original_elfs':artifacts,'sdk_sha256':digest(p/'stage/private-test-sdk/bin/ssh-keygen')}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
