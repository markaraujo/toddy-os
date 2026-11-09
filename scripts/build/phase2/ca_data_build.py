"""Generate real Mozilla CA data in private trust paths, not installed /etc."""
from pathlib import Path
import ctypes,errno,hashlib,json,os,re,ssl,subprocess,sys
source=Path('/src');work=Path('/build');proof=source/'toddy-ca-data.json';r=json.loads(proof.read_text())
assert os.geteuid()==101 and not (work/'data-results.json').exists()
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert digest(source/'nss-certdata.txt')==r['certdata_sha256']
status=Path('/proc/self/status').read_text()
assert re.search(r'^NoNewPrivs:\s+1$',status,re.M)
for field in ['CapInh','CapPrm','CapEff','CapAmb']:assert int(re.search(r'^'+field+r':\s+(\w+)$',status,re.M)[1],16)==0
for path in ['/src/nss-certdata.txt','/etc/ssl/openssl.cnf','/etc/nsswitch.conf']:
 try:
  with open(path,'ab'):pass
 except OSError as error:assert error.errno in [errno.EROFS,errno.EACCES]
 else:raise AssertionError('Unexpected writable input/configuration')
assert not list(Path('/etc/pki').iterdir()) and digest(Path('/etc/ssl/certs/ca-certificates.crt'))==r['baseline_CA_sha256']
tool=source/'tool/usr/sbin/make-ca';assert digest(tool)==r['make_ca_stage']['usr/sbin/make-ca']
with (work/'generation.log').open('x') as log:
 result=subprocess.run([str(tool),'-f','-C','/src/nss-certdata.txt','-n','/etc/pki/nssdb'],env={**os.environ,'OPENSSL_CONF':'/etc/ssl/openssl.cnf'},stdout=log,stderr=subprocess.STDOUT,timeout=180)
(work/'generation.exit').write_text(str(result.returncode)+'\n');assert result.returncode==0
logtext=(work/'generation.log').read_text();assert 'Failed!!!' not in logtext
anchors=list(Path('/etc/pki/anchors').glob('*.p11-kit'));assert anchors and len(anchors)<=172
bundle=Path('/etc/pki/tls/certs/ca-bundle.crt');assert bundle.is_file()
def certificates(path):
 return {hashlib.sha256(ssl.PEM_cert_to_DER_cert(b.decode())).hexdigest() for b in re.findall(rb'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',path.read_bytes(),re.S)}
old=certificates(source/'ssl-template/certs/ca-certificates.crt');new=certificates(bundle);assert len(old)==118 and new
trust=subprocess.run(['trust','list','--filter=ca-anchors'],capture_output=True,text=True,timeout=30,check=True);(work/'trust-list.log').write_text(trust.stdout);assert 'pkcs11:' in trust.stdout
issuer=subprocess.run(['openssl','verify','-CAfile',str(bundle),str(source/'tool/etc/make-ca/ISRG_Root_X1.pem')],capture_output=True,text=True,timeout=15)
(work/'root-verify.log').write_text(issuer.stdout+issuer.stderr);assert issuer.returncode==0
# No fake trust file/module override: this is the unchanged original program
# against the real default p11-kit path, mapped to proposed generated outputs.
env={**os.environ,'LD_LIBRARY_PATH':'/src/gnutls-lib'};assert not any(k in env for k in ['GNUTLS_SYSTEM_TRUST_FILE','GNUTLS_SYSTEM_PRIORITY_FILE','P11_KIT_TRUST_PATHS'])
original=subprocess.run(['/src/trust-store'],env=env,capture_output=True,text=True,timeout=30)
(work/'original-trust-store.log').write_text(original.stdout+original.stderr);(work/'original-trust-store.exit').write_text(str(original.returncode)+'\n');assert original.returncode==0
assert digest(source/'trust-store')==r['gnutls_original_trust_store_sha256']
# New process loads the exact same production library, preserving clean loader
# inputs; result contains counts only, never certificate/key bodies.
code="""import ctypes,json
lib=ctypes.CDLL('/src/gnutls-lib/libgnutls.so.30')
lib.gnutls_certificate_allocate_credentials.argtypes=[ctypes.POINTER(ctypes.c_void_p)]
lib.gnutls_certificate_set_x509_system_trust.argtypes=[ctypes.c_void_p]
lib.gnutls_certificate_free_credentials.argtypes=[ctypes.c_void_p]
assert lib.gnutls_global_init()==0
cred=ctypes.c_void_p();assert lib.gnutls_certificate_allocate_credentials(ctypes.byref(cred))==0
count=lib.gnutls_certificate_set_x509_system_trust(cred);assert count>0
lib.gnutls_certificate_free_credentials(cred);lib.gnutls_global_deinit()
print(json.dumps({'default_GnuTLS_system_CA_count':count}))
"""
counts=subprocess.run(['python3','-c',code],env=env,capture_output=True,text=True,timeout=30,check=True);native=json.loads(counts.stdout)
# Preserve the accepted foundation bundle byte-for-byte when trust sets match.
# Report any real CA membership change for explicit controlled promotion review.
legacy=Path('/etc/ssl/certs/ca-certificates.crt')
if legacy.exists() or legacy.is_symlink():legacy.unlink()
legacy.write_bytes((source/'ssl-template/certs/ca-certificates.crt').read_bytes() if old==new else bundle.read_bytes());legacy.chmod(0o644)
for name in ['openssl.cnf','openssl.cnf.dist','ct_log_list.cnf','ct_log_list.cnf.dist']:assert digest(Path('/etc/ssl')/name)==digest(source/'ssl-template'/name)
assert digest(source/'nss-certdata.txt')==r['certdata_sha256']
manifest={}
for directory in ['candidate-pki','candidate-ssl']:
 for p in (work/directory).rglob('*'):
  if p.is_file() and not p.is_symlink():manifest[str(p.relative_to(work))]=digest(p)
result={'scope':'Real frozen Mozilla/NSS3.126 policy generated with make-ca1.16.1 and actual production p11-kit/GnuTLS/OpenSSL in private worker paths. No installed-store/package mutation, remote TLS/DNS/native GNOME or update-hook/recovery acceptance','uid':os.geteuid(),'no_new_privileges':True,'input_config_readonly':True,'certdata_sha256':r['certdata_sha256'],'generation_exit':0,'anchors':len(anchors),'server_auth_certificates':len(new),'baseline_server_auth_certificates':len(old),'server_auth_DER_membership_unchanged':old==new,'added_server_auth_DER_sha256':sorted(new-old),'removed_server_auth_DER_sha256':sorted(old-new),'foundation_bundle_bytes_preserved':old==new and digest(legacy)==r['baseline_CA_sha256'],'default_GnuTLS_system_CA_count':native['default_GnuTLS_system_CA_count'],'original_trust_store_exit':original.returncode,'original_trust_store_ELF_sha256':digest(source/'trust-store'),'ISRG_Root_X1_verification_exit':issuer.returncode,'generated_manifest':manifest}
(work/'data-results.json').write_text(json.dumps(result,indent=2)+'\n')
