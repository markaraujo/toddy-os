#!/bin/bash
# Private keygen test SDK only: no installation, sshd or network-service claim.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --sysconfdir=/etc/ssh --without-pam \
    --without-libedit --without-kerberos5 --without-selinux --without-security-key-builtin
make -j4 ssh-keygen ssh
make regress-prep
make -j4 regress/unittests/sshkey/test_sshkey regress/unittests/crypto/test_crypto
mkdir /build/unit-data
cp -a /src/regress/unittests/sshkey/testdata /build/unit-data/sshkey
cp -a /src/regress/unittests/crypto/testdata /build/unit-data/crypto
./regress/unittests/sshkey/test_sshkey -v -d /build/unit-data/sshkey > /build/original-sshkey.log 2>&1
./regress/unittests/crypto/test_crypto -v -d /build/unit-data/crypto > /build/original-crypto.log 2>&1
python3 /src/toddy-probe.py /build/compile > /build/native-consumer.json
mkdir -p /stage/private-test-sdk/bin
cp /build/compile/ssh-keygen /stage/private-test-sdk/bin/
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');version=(Path('/src/version.h')).read_text();assert re.search(r'#define SSH_VERSION\s+"OpenSSH_10[.]5"',version) and re.search(r'#define SSH_PORTABLE\s+"p1"',version)
result={'scope':'Private qualified keygen/crypto test SDK only; no installed OpenSSH package/server/network/SSH-agent acceptance','compile_exit':0,'stage_exit':0,'source_version':'10.5p1','original_programs':[{'name':n,'exit':0,'log_sha256':hashlib.sha256((p/('original-'+n+'.log')).read_bytes()).hexdigest()} for n in ['sshkey','crypto']],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'sdk_sha256':hashlib.sha256((Path('/stage/private-test-sdk/bin/ssh-keygen')).read_bytes()).hexdigest()}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
