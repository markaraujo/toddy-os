#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gnupg) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
gpg --version | grep -F '2.5.24'
export GNUPGHOME=$(mktemp -d /tmp/toddy-signing.XXXXXX)
cleanup() { gpgconf --kill all; rm -rf "$GNUPGHOME"; }
trap cleanup EXIT
gpg --batch --pinentry-mode loopback --passphrase '' --quick-generate-key \
 'Toddy ephemeral signing fixture <build@example.invalid>' ed25519 sign 0
printf 'native signing contract\n' > "$GNUPGHOME/message"
gpg --batch --pinentry-mode loopback --passphrase '' --detach-sign "$GNUPGHOME/message"
gpg --batch --export > "$GNUPGHOME/public.gpg"
gpgv --keyring "$GNUPGHOME/public.gpg" "$GNUPGHOME/message.sig" "$GNUPGHOME/message"
printf 'tampered\n' >> "$GNUPGHOME/message"
set +e
gpgv --keyring "$GNUPGHOME/public.gpg" "$GNUPGHOME/message.sig" "$GNUPGHOME/message"
result=$?
set -e
[[ $result == 1 ]]
printf 'Native detached signing, scoped verification and tamper rejection passed\n'
INNER
