#!/bin/bash
# Run inside the verified new root, before any service. See ADR-0075.
set -euo pipefail
export LC_ALL=C
[[ $EUID == 0 && $# == 1 && -f $1 && ! -L $1 ]] || exit 1
sidecar=$1
declare -a paths=()
declare -A seen=()
while IFS= read -r line || [[ -n $line ]]; do
 [[ $line == '# file: '* ]] || continue
 encoded=${line#\# file: }
 # Accept exactly ACL 2.4.0's escaped backslash/newline/carriage-return names.
 remainder=$encoded
 while [[ $remainder == *\\* ]]; do
  remainder=${remainder#*\\}
  case $remainder in
   \\*) remainder=${remainder:1} ;;
   012*|015*) remainder=${remainder:3} ;;
   *) printf 'Unreviewed ACL filename escape\n' >&2; exit 1 ;;
  esac
 done
 printf -v path '%b' "$encoded"
 path=${path#./}
 case $path in
  ''|/*|..|../*|*/..|*/../*|./*|*/./*|*/.|*//*|*/) printf 'Noncanonical ACL path\n' >&2; exit 1 ;;
 esac
 [[ ! ${seen[$path]+present} ]] || { printf 'Duplicate ACL path\n' >&2; exit 1; }
 seen[$path]=1
 parent=.
 remainder=$path
 while [[ $remainder == */* ]]; do
  parent+=/${remainder%%/*}
  [[ -d $parent && ! -L $parent ]] || { printf 'Redirected ACL parent\n' >&2; exit 1; }
  remainder=${remainder#*/}
 done
 [[ ! -L $path && ( -f $path || -d $path ) ]] || { printf 'Missing or redirected ACL entry\n' >&2; exit 1; }
 paths+=("$path")
done < "$sidecar"

# OverlayFS checks the current real inode's set_acl operation before copy-up.
# Squashfs has none. Copy only declared ACL paths to the indexed tmpfs upper
# first, keeping the current mode unchanged; never rewrite their file contents.
for path in "${paths[@]}"; do
 chmod --reference="$path" -- "$path"
done
setfacl -P --restore="$sidecar"
