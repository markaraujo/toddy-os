#!/bin/bash
# A real ownership conflict against the installed native database must fail.
source /opt/toddy-build/scripts/build/h06/common.sh
stage=$LFS/sources/stage/ownership-probe
[[ ! -e $stage ]] || { echo 'Inspect previous ownership probe stage'; exit 1; }
mkdir -p "$stage/usr/share/man/man2" "$stage/usr/share/doc/toddy-ownership-probe"
cp -a "$LFS/usr/share/man/man2/open.2" "$stage/usr/share/man/man2/open.2"
cp "$LFS/usr/share/doc/man-pages/copyright" "$stage/usr/share/doc/toddy-ownership-probe/copyright"
before=$(sha256sum "$LFS/usr/share/man/man2/open.2")
if python3 /opt/toddy-build/scripts/build/stage_package.py toddy-ownership-probe 0.1 \
    "$stage" --architecture all --source man-pages-6.18.tar.xz \
    --recipe /opt/toddy-build/scripts/build/h07/ownership-probe.sh \
    > /var/log/toddy/ownership-probe.log 2>&1; then
    echo 'Ownership preflight incorrectly accepted conflicting package' >&2
    exit 1
fi
grep 'Native package ownership conflict before install:' /var/log/toddy/ownership-probe.log
[[ $(sha256sum "$LFS/usr/share/man/man2/open.2") == "$before" ]]
[[ ! -e /var/cache/toddy/packages/toddy-ownership-probe_0.1_all.deb ]]
dpkg-query --admindir="$LFS/var/lib/dpkg" -S /usr/share/man/man2/open.2
