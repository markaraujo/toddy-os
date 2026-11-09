#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,re,ssl,subprocess
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'}
receipt=json.loads(Path('/var/log/toddy/phase2/ca-native-transaction-1.json').read_text());assert receipt['state']=='complete'
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','ca-certificates'],text=True)=='install ok installed 2026.11.09-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
base=Path('/mnt/lfs');work=base/'sources/phase2/work/make-ca-data-2';source=base/'sources/phase2/inputs/make-ca-data-2'
expected=json.loads((work/'data-results.json').read_text())
def hashes(p):
    return {hashlib.sha256(ssl.PEM_cert_to_DER_cert(b.decode())).hexdigest() for b in re.findall(rb'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',p.read_bytes(),re.S)}
assert len(hashes(base/'etc/ssl/certs/ca-certificates.crt'))==121
assert hashes(base/'etc/ssl/certs/ca-certificates.crt')==hashes(work/'candidate-pki/tls/certs/ca-bundle.crt')
assert len(list((base/'etc/pki/anchors').glob('*.p11-kit')))==172
assert os.readlink(base/'etc/ssl/cert.pem')=='certs/ca-certificates.crt'
assert os.readlink(base/'etc/ssl/certs/ca-bundle.crt')=='ca-certificates.crt'
assert not (base/'etc/pki/nssdb').exists() and not (base/'etc/pki/tls/java').exists()
trust=subprocess.run(prefix+['trust','list','--filter=ca-anchors'],env=env,capture_output=True,text=True,timeout=30,check=True)
assert 'pkcs11:' in trust.stdout
# Actual unchanged original and production library, with default installed trust.
# No GNUTLS/P11 override and no private candidate /etc aliases in this process.
binary=source/'trust-store';assert hashlib.sha256(binary.read_bytes()).hexdigest()==expected['original_trust_store_ELF_sha256']
env['LD_LIBRARY_PATH']='/sources/phase2/inputs/make-ca-data-2/gnutls-lib'
r=subprocess.run(['chroot','--userspec=101:101','/mnt/lfs','/sources/phase2/inputs/make-ca-data-2/trust-store'],env=env,capture_output=True,text=True,timeout=30)
Path('/var/log/toddy/phase2/ca-native-original-trust.log').write_text(r.stdout+r.stderr);assert r.returncode==0
root='/sources/phase2/inputs/make-ca-data-2/tool/etc/make-ca/ISRG_Root_X1.pem'
r=subprocess.run(prefix+['openssl','verify',root],env=env,capture_output=True,text=True,timeout=20)
assert r.returncode==0 and r.stdout.strip().endswith(': OK')
Path('/var/log/toddy/phase2/ca-native-installed-consumer.json').write_text(json.dumps({'scope':'Installed factory trust/P11/default GnuTLS original/OpenSSL default bundle and owned legacy aliases only. Local trust update hook/recovery, NSS unified alias, remote DNS/TLS and native desktop pending.', 'server_auth_certificates':121,'anchors':172,'original_default_GnuTLS_trust_store_exit':0,'OpenSSL_default_ISRG_root_exit':0,'package_audit_exit':0,'real_credentials_used':False},indent=2)+'\n')
PY
