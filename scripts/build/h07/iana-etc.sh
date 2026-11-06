#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
[[ ! -e stage/iana-etc ]] || { echo 'Inspect existing stage before retry'; exit 1; }
python3 "$SOURCE_TOOL" iana-etc-20260805.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/iana-etc-inner.sh
install -d "$LFS/sources/stage/iana-etc/usr/share/doc/iana-etc"
cat /opt/toddy-build/LICENSES/IANA-REGISTRY-NOTICE.txt \
    /opt/toddy-build/LICENSES/IANA-ETC-MIT.txt > "$LFS/sources/stage/iana-etc/usr/share/doc/iana-etc/copyright"
python3 /opt/toddy-build/scripts/build/stage_package.py iana-etc 20260805-1 \
    "$LFS/sources/stage/iana-etc" --architecture all --source iana-etc-20260805.tar.gz \
    --conffile /etc/services --conffile /etc/protocols \
    --recipe /opt/toddy-build/scripts/build/h07/iana-etc.sh --install
rm -rf "$LFS/sources/iana-etc-20260805"
