#!/bin/bash
source /opt/toddy-build/scripts/build/h04/common.sh
test -f "$LFS/usr/lib/libstdc++.so.6"
test -f "$LFS/tools/$LFS_TGT/include/c++/16.2.0/vector"
! find "$LFS/usr/lib" -name 'libstdc++*.la' | grep .
"$LFS_TGT-readelf" -d "$LFS/usr/lib/libstdc++.so.6" | grep NEEDED
