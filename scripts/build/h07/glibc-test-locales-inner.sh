#!/bin/bash
# LFS 13.1-systemd 8.39 explicitly requires these for complete Bash locale tests.
set -euo pipefail
stage=/sources/stage/glibc-test-locales
test ! -e "$stage"
mkdir -p "$stage/usr/lib/locale" "$stage/usr/share/doc/glibc-test-locales"
# These legacy encodings intentionally are not ASCII-compatible. Disable only
# that named localedef warning; all other generation errors remain fatal.
# --no-archive prevents collision with the existing glibc-locales owned archive.
localedef --no-warnings=ascii --no-archive --prefix="$stage" -i ja_JP -f SHIFT_JIS ja_JP.SJIS
localedef --no-warnings=ascii --no-archive --prefix="$stage" -i zh_TW -f BIG5 zh_TW.BIG5
cp /usr/share/doc/glibc/copyright "$stage/usr/share/doc/glibc-test-locales/copyright"
