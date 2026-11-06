#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only cacert-2026-11-05.pem
chroot_run <<'INNER'
set -euo pipefail
test ! -e /sources/stage/ca-certificates
mkdir -p /sources/stage/ca-certificates/{etc/ssl/certs,usr/share/doc/ca-certificates}
install -m644 /sources/cacert-2026-11-05.pem /sources/stage/ca-certificates/etc/ssl/certs/ca-certificates.crt
ln -s certs/ca-certificates.crt /sources/stage/ca-certificates/etc/ssl/cert.pem
ln -s ca-certificates.crt /sources/stage/ca-certificates/etc/ssl/certs/ca-bundle.crt
INNER
install -m644 /opt/toddy-build/LICENSES/MPL-2.0.txt "$LFS/sources/stage/ca-certificates/usr/share/doc/ca-certificates/copyright"
python3 /opt/toddy-build/scripts/build/stage_package.py ca-certificates 2026.11.05-1 \
 "$LFS/sources/stage/ca-certificates" --depends 'openssl' --source cacert-2026-11-05.pem \
 --conffile /etc/ssl/certs/ca-certificates.crt \
 --recipe /opt/toddy-build/scripts/build/h07/ca-certificates.sh --install
