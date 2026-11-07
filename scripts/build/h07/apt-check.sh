#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
apt-get --version | head -n1 | grep -F 'apt 3.0.4'
apt-config dump | grep -F 'APT::Sandbox::User "_apt"'
apt-config dump | grep -Fx 'APT::Sandbox::Seccomp "true";'
test -x /usr/libexec/apt/methods/gpgv
test -x /usr/libexec/apt/methods/https
getent passwd _apt
INNER
install -Dm644 /opt/toddy-build/scripts/build/h07/apt-worker-probe.py \
 "$LFS/sources/evidence/h07-apt/apt-worker-probe.py"
chroot_run < /opt/toddy-build/scripts/build/h07/apt-repository-check-inner.sh

# ADR-0092: validate the actual installed Berkeley consumer and cache recovery.
install -Dm644 /opt/toddy-build/scripts/build/h07/apt-cache-check.py \
 "$LFS/sources/evidence/h07-apt/apt-cache-check.py"
chroot_run <<'CACHE'
set -euo pipefail
work=$(mktemp -d /tmp/toddy-apt-cache-parent.XXXXXX)
chown tester:tester "$work"
su tester -c "python3 -B /sources/evidence/h07-apt/apt-cache-check.py --work $work/check" \
 | tee /sources/evidence/h07-apt/native-cache.log
cp "$work/check/result.json" /sources/evidence/h07-apt/native-cache-result.json
CACHE
