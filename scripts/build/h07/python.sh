#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" Python-3.14.10.tar.xz
python3 "$SOURCE_TOOL" --verify-only Python-3.14.7-openssl_4-1.patch
python3 "$SOURCE_TOOL" --verify-only Python-3.14.10-openssl_4-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/python-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py python 3.14.10-1 \
 "$LFS/sources/stage/python" --depends 'glibc (>= 2.44-1), openssl, expat, libffi, sqlite, mpdecimal, zlib, bzip2, xz, gdbm, ncurses, readline' --source Python-3.14.10.tar.xz --source Python-3.14.7-openssl_4-1.patch --source Python-3.14.10-openssl_4-1.patch --conffile /etc/pip.conf \
 --recipe /opt/toddy-build/scripts/build/h07/python.sh --install
