#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' ca-certificates) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf '%s  %s\n' 427c064216761a1e72a8b30f0d954d08cb6e4435a82091fb865afd20c8497285 /etc/ssl/certs/ca-certificates.crt | sha256sum -c -
[[ $(grep -c -- '-----BEGIN CERTIFICATE-----' /etc/ssl/cert.pem) == 118 ]]
openssl crl2pkcs7 -nocrl -certfile /etc/ssl/cert.pem | openssl pkcs7 -print_certs -noout > /tmp/toddy-public-ca-subjects
[[ $(grep -c '^subject=' /tmp/toddy-public-ca-subjects) == 118 ]]
rm /tmp/toddy-public-ca-subjects
python3 -c 'import ssl; c=ssl.create_default_context(); assert c.cert_store_stats()["x509_ca"]==118; print("Python default trust: 118 frozen public roots")'
INNER
