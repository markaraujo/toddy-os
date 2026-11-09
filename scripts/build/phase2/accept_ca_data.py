"""Accept only actual private CA results plus zero installed-root changes."""
from pathlib import Path
import fcntl,hashlib,json,subprocess,sys
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
sys.path.insert(0,str(ROOT/'scripts/build'))
from run_step import snapshot
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=Path('/var/log/toddy/build/build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
receipt=LOG/'ca-data-acceptance-1.json';assert not receipt.exists()
prepared=json.loads((LOG/'ca-data-prepared-2.json').read_text());source=Path(prepared['source']);work=Path(prepared['work'])
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert json.loads((source/'toddy-ca-data.json').read_text())==prepared
for name,script,exitcode in [('make-ca-data-2','ca_data_build.py','1'),('make-ca-data-finish-3','ca_data_finish.py','0')]:
 assert (LOG/(name+'.exit')).read_text().strip()==exitcode
 assert json.loads((LOG/(name+'.job.json')).read_text())['command'][2:]==[str(source),str(work),'python3','-c',(ROOT/'scripts/build/phase2'/script).read_text()]
r=json.loads((work/'data-results.json').read_text());assert r['uid']==101 and r['no_new_privileges'] and r['input_config_readonly']
assert r['generation_exit']==r['original_trust_store_exit']==r['ISRG_Root_X1_verification_exit']==0
assert r['anchors']==172 and r['server_auth_certificates']==121 and r['baseline_server_auth_certificates']==118
assert r['generation_and_original_trust_test_not_repeated'] and r['preexisting_candidate_files_unchanged']
assert r['certdata_sha256']==prepared['certdata_sha256']==digest(source/'nss-certdata.txt') and r['original_trust_store_ELF_sha256']==prepared['gnutls_original_trust_store_sha256']==digest(source/'trust-store')
for name,sha in r['generated_manifest'].items():assert digest(work/name)==sha
for name,key in [('generation.log','generation_log_sha256'),('original-trust-store.log','original_trust_store_log_sha256'),('trust-list.log','trust_list_log_sha256')]:assert digest(work/name)==r[key]
assert not (TARGET/'etc/pki').exists() and digest(TARGET/'etc/ssl/certs/ca-certificates.crt')==prepared['baseline_CA_sha256']
before=LOG/'ca-data-prepared-2-root-before.json';assert digest(before)==prepared['installed_root_before_manifest_sha256']
actual=snapshot();assert actual==json.loads(before.read_text()),'Installed root changed; inspect exact postconditions, no replay'
result={'state':'private-stage-data-qualified-not-installed','scope':r['scope'],'installed_root_entries_unchanged':len(actual),'installed_root_changed_paths':0,'private_data_result_sha256':digest(work/'data-results.json'),'certdata_sha256':r['certdata_sha256'],'anchors':r['anchors'],'server_auth_certificates':r['server_auth_certificates'],'baseline_server_auth_certificates':r['baseline_server_auth_certificates'],'added_server_auth_DER_sha256':r['added_server_auth_DER_sha256'],'removed_server_auth_DER_sha256':r['removed_server_auth_DER_sha256'],'original_GnuTLS_trust_store_passed':True,'ISRG_Root_X1_verified':True,'source':str(source),'work':str(work),'native_install_provider_hook_update_recovery_pending':True,'recovery':'Keep immutable inputs and failed candidates1; do not rerun generation/original trust/metadata completion/acceptance. Native promotion must use verified staged data and preserve ownership/user configuration under its own controlled transaction.'}
receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
