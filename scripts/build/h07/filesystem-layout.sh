#!/bin/bash
# Native layout synthesized from frozen LFS 13.1 sections 4.2 and 7.5/7.6.
source /opt/toddy-build/scripts/build/h06/common.sh
stage="$LFS/sources/stage/filesystem-layout"
[[ ! -e "$stage" ]]
mkdir -p "$stage"/{usr/{bin,lib,sbin,local/{bin,lib,sbin,share}},lib64,home,media,mnt,opt,srv,var/{cache,lib,log,opt,spool}}
ln -s usr/bin "$stage/bin"
ln -s usr/lib "$stage/lib"
ln -s usr/sbin "$stage/sbin"
ln -s ../lib/ld-linux-x86-64.so.2 "$stage/lib64/ld-linux-x86-64.so.2"
ln -s ../lib/ld-linux-x86-64.so.2 "$stage/lib64/ld-lsb-x86-64.so.3"
ln -s bash "$stage/usr/bin/sh"
install -Dm644 /opt/toddy-build/LICENSES/LFS-MIT.txt "$stage/usr/share/doc/filesystem-layout/copyright"
cp /opt/toddy-build/config/books.lock.json "$stage/usr/share/doc/filesystem-layout/book-sources.json"
python3 /opt/toddy-build/scripts/build/stage_package.py filesystem-layout 13.1-1 \
 "$stage" --depends 'glibc, bash' --recipe /opt/toddy-build/scripts/build/h07/filesystem-layout.sh --install
