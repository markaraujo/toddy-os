#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" kbd-2.10.0.tar.xz
python3 "$SOURCE_TOOL" --verify-only kbd-2.10.0-backspace-1.patch
python3 "$SOURCE_TOOL" --verify-only kbd-2.10.0-backspace-context-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/kbd-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py kbd 2.10.0-1 \
 "$LFS/sources/stage/kbd" --depends 'glibc (>= 2.44-1)' --source kbd-2.10.0.tar.xz --source kbd-2.10.0-backspace-1.patch --source kbd-2.10.0-backspace-context-1.patch \
 --recipe /opt/toddy-build/scripts/build/h07/kbd.sh --install
