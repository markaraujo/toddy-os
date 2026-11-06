#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
check_native /usr/bin/python3 3.14.7
chroot_run <<'INNER'
python3 -c 'import decimal, zlib; assert decimal.Decimal("1.5") * 2 == 3; assert zlib.decompress(zlib.compress(b"ok")) == b"ok"; print("Native Python decimal/zlib work")'
INNER
