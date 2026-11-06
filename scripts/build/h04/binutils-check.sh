#!/bin/bash
source /opt/toddy-build/scripts/build/h04/common.sh
"$LFS_TGT-ld" --version | head -1
"$LFS_TGT-as" --version | head -1
"$LFS_TGT-ld" --verbose | grep SEARCH_DIR > "$LFS/sources/evidence/h04-binutils-search.txt"
grep -q 'SEARCH_DIR("=' "$LFS/sources/evidence/h04-binutils-search.txt"
[[ $(command -v "$LFS_TGT-ld") == "$LFS/tools/bin/$LFS_TGT-ld" ]]
