#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
apt-get --version | head -n1 | grep -F 'apt 3.0.4'
apt-config dump | grep -F 'APT::Sandbox::User "_apt"'
test -x /usr/libexec/apt/methods/gpgv
test -x /usr/libexec/apt/methods/https
getent passwd _apt
INNER
chroot_run < /opt/toddy-build/scripts/build/h07/apt-repository-check-inner.sh
