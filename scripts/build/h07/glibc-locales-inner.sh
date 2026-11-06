#!/bin/bash
# Frozen LFS 13.1-systemd 8.5 minimum test locales plus Portuguese product locale.
set -euo pipefail
stage=/sources/stage/glibc-locales
test ! -e "$stage"
mkdir -p "$stage/usr/lib/locale" "$stage/usr/share/doc/glibc-locales"
localedef --prefix=/sources/stage/glibc-locales -i C -f UTF-8 C.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i cs_CZ -f UTF-8 cs_CZ.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i de_DE -f ISO-8859-1 de_DE
localedef --prefix=/sources/stage/glibc-locales -i de_DE@euro -f ISO-8859-15 de_DE@euro
localedef --prefix=/sources/stage/glibc-locales -i de_DE -f UTF-8 de_DE.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i el_GR -f ISO-8859-7 el_GR
localedef --prefix=/sources/stage/glibc-locales -i en_GB -f ISO-8859-1 en_GB
localedef --prefix=/sources/stage/glibc-locales -i en_GB -f UTF-8 en_GB.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i en_HK -f ISO-8859-1 en_HK
localedef --prefix=/sources/stage/glibc-locales -i en_PH -f ISO-8859-1 en_PH
localedef --prefix=/sources/stage/glibc-locales -i en_US -f ISO-8859-1 en_US
localedef --prefix=/sources/stage/glibc-locales -i en_US -f UTF-8 en_US.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i es_ES -f ISO-8859-15 es_ES@euro
localedef --prefix=/sources/stage/glibc-locales -i es_MX -f ISO-8859-1 es_MX
localedef --prefix=/sources/stage/glibc-locales -i fa_IR -f UTF-8 fa_IR
localedef --prefix=/sources/stage/glibc-locales -i fr_FR -f ISO-8859-1 fr_FR
localedef --prefix=/sources/stage/glibc-locales -i fr_FR@euro -f ISO-8859-15 fr_FR@euro
localedef --prefix=/sources/stage/glibc-locales -i fr_FR -f UTF-8 fr_FR.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i is_IS -f ISO-8859-1 is_IS
localedef --prefix=/sources/stage/glibc-locales -i is_IS -f UTF-8 is_IS.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i it_IT -f ISO-8859-1 it_IT
localedef --prefix=/sources/stage/glibc-locales -i it_IT -f ISO-8859-15 it_IT@euro
localedef --prefix=/sources/stage/glibc-locales -i it_IT -f UTF-8 it_IT.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i ja_JP -f EUC-JP ja_JP
localedef --prefix=/sources/stage/glibc-locales -i ja_JP -f UTF-8 ja_JP.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i nl_NL@euro -f ISO-8859-15 nl_NL@euro
localedef --prefix=/sources/stage/glibc-locales -i ru_RU -f KOI8-R ru_RU.KOI8-R
localedef --prefix=/sources/stage/glibc-locales -i ru_RU -f UTF-8 ru_RU.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i se_NO -f UTF-8 se_NO.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i ta_IN -f UTF-8 ta_IN.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i tr_TR -f UTF-8 tr_TR.UTF-8
localedef --prefix=/sources/stage/glibc-locales -i zh_CN -f GB18030 zh_CN.GB18030
localedef --prefix=/sources/stage/glibc-locales -i zh_HK -f BIG5-HKSCS zh_HK.BIG5-HKSCS
localedef --prefix=/sources/stage/glibc-locales -i zh_TW -f UTF-8 zh_TW.UTF-8
localedef --prefix="$stage" -i pt_BR -f UTF-8 pt_BR.UTF-8
cp /usr/share/doc/glibc/copyright "$stage/usr/share/doc/glibc-locales/copyright"
