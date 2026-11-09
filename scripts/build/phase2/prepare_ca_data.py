"""Prepare a new CA data input; no installed trust store or package is changed."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,sys,tarfile
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
sys.path.insert(0,str(ROOT/'scripts/build'))
from run_step import snapshot
from stage_package import payload
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=Path('/var/log/toddy/build/build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
variant=sys.argv[1] if len(sys.argv)==2 else '1';assert variant in ['1','2']
source=TARGET/('sources/phase2/inputs/make-ca-data-'+variant);work=TARGET/('sources/phase2/work/make-ca-data-'+variant);receipt=LOG/('ca-data-prepared-'+variant+'.json')
assert not source.exists() and not work.exists() and not receipt.exists() and not list(LOG.glob('make-ca-data-'+variant+'.*'))
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert (LOG/'make-ca-1.exit').read_text().strip()=='0'
tool_source=TARGET/'sources/phase2/inputs/make-ca-1.16.1';tool_work=TARGET/'sources/phase2/work/make-ca-1'
assert (tool_source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/make-ca-build.sh').read_bytes() and (tool_source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/make-ca-probe.py').read_bytes()
tool=json.loads((tool_work/'stage-results.json').read_text());assert tool['build_exit']==tool['stage_exit']==0 and tool['consumer']['temporary_data_removed']
for name,sha in tool['stage_sha256'].items():assert digest(tool_work/'stage'/name)==sha
archive=TARGET/'sources/nss-3.126.tar.gz';assert digest(archive)=='7aa07c758be1453d82d739240b249ffb7aef0041be488067e1c0f348e1f9e337'
with tarfile.open(archive) as tar:certdata=tar.extractfile('nss-3.126/nss/lib/ckfw/builtins/certdata.txt').read()
certfile=TARGET/'sources/phase2/inputs/nss-3.126/nss/lib/ckfw/builtins/certdata.txt';assert certfile.read_bytes()==certdata
assert not (TARGET/'etc/pki').exists() and not list((TARGET/'etc/ssl/private').iterdir()),'Do not copy owner private data'
old_ssl=payload(TARGET/'etc/ssl');assert digest(TARGET/'etc/ssl/certs/ca-certificates.crt')=='427c064216761a1e72a8b30f0d954d08cb6e4435a82091fb865afd20c8497285'
old_ca=json.loads(Path('/var/log/toddy/packages/ca-certificates_2026.11.05-1+toddy1_amd64.json').read_text());assert old_ca['installed']
gnu=TARGET/'sources/phase2/work/gnutls-1';assert (LOG/'gnutls-1.exit').read_text().strip()==(LOG/'gnutls-remaining-2.exit').read_text().strip()=='2'
assert (gnu/'compile/tests/trust-store.trs').read_text().find(':test-result: FAIL')>=0 and 'no certificates were found in system trust store' in (gnu/'compile/tests/trust-store.log').read_text()
initial=json.loads((gnu/'initial-ELFs-before-remaining-2.json').read_text());libs=[p for p in (gnu/'compile/lib/.libs').glob('libgnutls.so.*') if p.is_file() and not p.is_symlink()];assert len(libs)==1
library=libs[0];assert initial[str(library.relative_to(gnu/'compile'))]==digest(library)
binary=gnu/'compile/tests/trust-store';assert binary.is_file() and binary.read_bytes()[:4]==b'\x7fELF'
before=snapshot();root_before=LOG/('ca-data-prepared-'+variant+'-root-before.json')
if variant=='2':
 assert (LOG/'make-ca-data-1.exit').read_text().strip()=='1'
 failed=TARGET/'sources/phase2/work/make-ca-data-1'
 assert 'loading certificate from /dev/stdin: No such file or directory' in (failed/'generation.log').read_text()
 assert not (failed/'data-results.json').exists()
 original=LOG/'ca-data-prepared-1-root-before.json';assert before==json.loads(original.read_text()),'Installed root changed; reconcile before preparing another variant'
 (LOG/'ca-data-failed-1-root-verify.json').write_text(json.dumps({'installed_root_entries_unchanged':len(before),'root_before_sha256':digest(original),'failed_candidates_retained':True,'cause':'Missing standard /dev/stdin descriptor alias in sandbox; generator exit0 was rejected by explicit missing-anchor postcondition'},indent=2)+'\n')
root_before.write_text(json.dumps(before,sort_keys=True)+'\n')
source.mkdir();work.mkdir();os.chown(work,101,101)
(source/'nss-certdata.txt').write_bytes(certdata);shutil.copytree(tool_work/'stage',source/'tool',symlinks=True);shutil.copytree(TARGET/'etc/ssl',source/'ssl-template',symlinks=True)
(source/'gnutls-lib').mkdir();shutil.copy2(library,source/'gnutls-lib'/library.name)
for p in (gnu/'compile/lib/.libs').glob('libgnutls.so*'):
 if p.is_symlink():
  target=os.readlink(p);assert '/' not in target;(source/'gnutls-lib'/p.name).symlink_to(target)
shutil.copy2(binary,source/'trust-store');(source/'trust-store').chmod(0o755)
shutil.copytree(TARGET/'etc/ssl',work/'candidate-ssl',symlinks=True);os.chown(work/'candidate-ssl',101,101);os.chown(work/'candidate-ssl/certs',101,101)
(work/'candidate-pki').mkdir();os.chown(work/'candidate-pki',101,101)
record={'state':'prepared','source':str(source),'work':str(work),'original_SSL_template':old_ssl,'baseline_CA_sha256':digest(TARGET/'etc/ssl/certs/ca-certificates.crt'),'certdata_sha256':hashlib.sha256(certdata).hexdigest(),'NSS_source_sha256':digest(archive),'make_ca_stage':tool['stage_sha256'],'gnutls_original_trust_store_sha256':digest(binary),'gnutls_library':{'name':library.name,'sha256':digest(library)},'installed_root_before_entries':len(before),'installed_root_before_manifest_sha256':digest(root_before),'candidate_inodes':{name:(work/name).stat().st_ino for name in ['candidate-ssl','candidate-pki']},'recovery':'Inspect actual receipt/job/candidate data before resumption; never prepare or generate again under an uncertain state. Installed root unchanged; root-before manifest retained.'}
(source/'toddy-ca-data.json').write_text(json.dumps(record,indent=2)+'\n');receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'state':record['state'],'installed_root_entries':len(before),'certdata_sha256':record['certdata_sha256'],'source':str(source),'work':str(work)}))
