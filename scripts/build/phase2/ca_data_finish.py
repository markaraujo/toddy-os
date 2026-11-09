"""Finalize only the private compatibility file after genuine CA tests passed."""
from pathlib import Path
import hashlib,json,os,re,ssl,subprocess
source=Path('/src');work=Path('/build');r=json.loads((source/'toddy-ca-data.json').read_text());assert os.geteuid()==101
assert not (work/'data-results.json').exists() and (work/'generation.exit').read_text().strip()=='0' and (work/'original-trust-store.exit').read_text().strip()=='0'
assert (work/'root-verify.log').read_text().strip().endswith(': OK')
log=(work/'generation.log').read_text();assert 'Failed!!!' not in log and 'Could not find or decode certificate' not in log
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert digest(source/'trust-store')==r['gnutls_original_trust_store_sha256'] and digest(source/'nss-certdata.txt')==r['certdata_sha256']
anchors=list(Path('/etc/pki/anchors').glob('*.p11-kit'));assert len(anchors)==172
bundle=Path('/etc/pki/tls/certs/ca-bundle.crt')
def certificates(path):return {hashlib.sha256(ssl.PEM_cert_to_DER_cert(b.decode())).hexdigest() for b in re.findall(rb'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',path.read_bytes(),re.S)}
old=certificates(source/'ssl-template/certs/ca-certificates.crt');new=certificates(bundle);assert len(old)==118 and len(new)==121
trustlog=work/'trust-list.log';assert 'pkcs11:' in trustlog.read_text()
legacy=Path('/etc/ssl/certs/ca-certificates.crt');assert not legacy.exists() and not legacy.is_symlink()
directory=legacy.parent;assert directory.stat().st_uid==101 and directory.stat().st_mode&0o777==0o555
before={str(p.relative_to(work)):digest(p) for name in ['candidate-pki','candidate-ssl'] for p in (work/name).rglob('*') if p.is_file() and not p.is_symlink()}
# trust extract deliberately seals its output directory0555. Restore the
# compatibility file in this PRIVATE output only, then retain the sealed mode.
directory.chmod(0o755)
legacy.write_bytes((source/'ssl-template/certs/ca-certificates.crt').read_bytes() if old==new else bundle.read_bytes());legacy.chmod(0o644);directory.chmod(0o555)
for name,sha in before.items():assert digest(work/name)==sha
for name in ['openssl.cnf','openssl.cnf.dist','ct_log_list.cnf','ct_log_list.cnf.dist']:assert digest(Path('/etc/ssl')/name)==digest(source/'ssl-template'/name)
manifest={str(p.relative_to(work)):digest(p) for name in ['candidate-pki','candidate-ssl'] for p in (work/name).rglob('*') if p.is_file() and not p.is_symlink()}
result={'scope':'Real frozen NSS3.126 CA policy/make-ca/P11/default GnuTLS/ISRG verification in private worker paths only. Original generation and consumer results reused; only own compatibility-file metadata finalization corrected. Installed provider/store/update hook/native GNOME/remote DNS/TLS pending','uid':os.geteuid(),'no_new_privileges':True,'input_config_readonly':True,'certdata_sha256':r['certdata_sha256'],'generation_exit':0,'anchors':len(anchors),'server_auth_certificates':len(new),'baseline_server_auth_certificates':len(old),'server_auth_DER_membership_unchanged':old==new,'added_server_auth_DER_sha256':sorted(new-old),'removed_server_auth_DER_sha256':sorted(old-new),'foundation_bundle_bytes_preserved':old==new and digest(legacy)==r['baseline_CA_sha256'],'original_trust_store_exit':0,'original_trust_store_ELF_sha256':digest(source/'trust-store'),'ISRG_Root_X1_verification_exit':0,'generation_and_original_trust_test_not_repeated':True,'preexisting_candidate_files_unchanged':True,'generated_manifest':manifest,'generation_log_sha256':digest(work/'generation.log'),'original_trust_store_log_sha256':digest(work/'original-trust-store.log'),'trust_list_log_sha256':digest(trustlog),'sealed_certificate_directory_mode':'0555'}
(work/'data-results.json').write_text(json.dumps(result,indent=2)+'\n')
