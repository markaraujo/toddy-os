"""Qualify the co-installable frozen Gcr3 C ABI; native GTK3 UI stays pending."""
import hashlib,json
from pathlib import Path
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/gcr-3.41.2-ssh-agent-1');work=Path('/mnt/lfs/sources/phase2/work/gcr3-patched-1');log=Path('/var/log/toddy/phase2')
 patch=json.loads((root/'config/phase2/gcr3-patches.lock.json').read_text());assert digest(root/patch['patch_file'])==patch['patch_sha256'] and digest(source/'meson.build')==patch['after_sha256']
 prepared=json.loads((log/'gcr3-patched-input-1.json').read_text());assert prepared['state']=='complete' and prepared['original_source_unchanged'] and prepared['changed_source_paths']==['meson.build'] and prepared['patch']==patch
 assert digest(Path(prepared['source'])/'meson.build')==patch['before_sha256']
 for a,b in [('toddy-build.sh','gcr3-build.sh'),('toddy-probe.c','gcr3-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (log/'gcr3-patched-2.exit').read_text().strip()=='0'
 assert json.loads((log/'gcr3-patched-2.job.json').read_text())['command'][2:]==[str(source),str(work),'dbus-run-session','--','bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['registered_original_programs']==result['selected_original_programs']==43 and result['original_nested_skips']==[]
 rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()];assert len(rows)==43 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
 assert result['original_tests']==[{k:r[k] for k in ['name','result','returncode']} for r in rows]
 assert result['consumer']=={'libgcrypt_transport_roundtrip':True,'malformed_exchange_refused':True,'prior_state_preserved':True,'recovery_cycles':2,'real_credentials_used':False}
 sdk=json.loads((source/'toddy-prepared.json').read_text())['private_test_sdk'];assert sdk['original_key_crypto_cases_reused']==119 and digest(source/'toddy-test-sdk/bin/ssh-keygen')==sdk['sha256']
 sample=source/'gcr/fixtures/pem-rsa-enc.key';assert digest(sample)==digest(work/'source-fixtures/pem-rsa-enc.key')=='55b32dbd31618e5e949be919fb42ed7ca519f8e4ad5b352c9136ab7202e6ef4e' and sample.stat().st_mode&0o7777==0o644
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 old=json.loads(Path('/var/log/toddy/packages/gcr_4.4.0.1-1+toddy1_amd64.json').read_text());assert not any('/'+p in old['payload'] for p in result['stage_sha256']),'Inspect overlap, never force overwrite Gcr4'
 return result
