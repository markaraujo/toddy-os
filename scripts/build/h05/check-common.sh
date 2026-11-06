#!/bin/bash
source /opt/toddy-build/scripts/build/h04/common.sh
target_run() {
    local binary=$1
    shift
    "$LFS/usr/lib/ld-linux-x86-64.so.2" --inhibit-cache --library-path "$LFS/usr/lib" "$LFS$binary" "$@"
}
check_tool() {
    local package=$1 binary=$2 version=$3
    "$LFS_TGT-readelf" -l "$LFS$binary" | grep 'interpreter: /lib64/ld-linux-x86-64.so.2'
    ! "$LFS_TGT-readelf" -d "$LFS$binary" | grep -E '\((RPATH|RUNPATH)\)'
    local dependencies="$LFS/sources/evidence/h05-$package-libraries.txt"
    "$LFS/usr/lib/ld-linux-x86-64.so.2" --inhibit-cache --library-path "$LFS/usr/lib" --list "$LFS$binary" > "$dependencies"
    while read -r library arrow path rest; do
        if [[ $arrow == '=>' && $path == /* ]]; then
            [[ $path == "$LFS/"* && $(realpath -e "$path") == "$LFS/"* ]] || { echo "Host library leak: $path" >&2; return 1; }
        fi
    done < "$dependencies"
    target_run "$binary" --version > "$LFS/sources/evidence/h05-$package-version.txt"
    grep -F "$version" "$LFS/sources/evidence/h05-$package-version.txt"
}
