#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' curl) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
curl --version | tee /tmp/toddy-curl-version
grep -F 'curl 8.23.0' /tmp/toddy-curl-version
grep -F HTTP2 /tmp/toddy-curl-version
curl --fail --show-error --max-time 60 https://example.com/ -o /tmp/toddy-https-example
grep -F 'Example Domain' /tmp/toddy-https-example
# Upstream-owned negative TLS endpoint: an untrusted certificate must fail.
set +e
curl --fail --show-error --max-time 60 https://self-signed.badssl.com/ -o /tmp/toddy-untrusted
result=$?
set -e
[[ $result == 60 ]]
rm -f /tmp/toddy-{curl-version,https-example,untrusted}
INNER
