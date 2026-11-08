#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion fontconfig) == 2.18.3 ]]
[[ $(dpkg-query -W -f='${Status}' fontconfig) == 'install ok installed' ]]
dpkg-query -W -f='${Conffiles}' fontconfig | grep -q ' /etc/fonts/fonts.conf '
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-fontconfig-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <fontconfig/fontconfig.h>
#include <fontconfig/fcfreetype.h>
int main(int argc,char **argv) {
    FcConfig *config;FcPattern *font,*pattern,*match;FcResult result;int count;
    if (argc!=2 || FcGetVersion()!=21803) return 1;
    config=FcInitLoadConfig();if (!config) return 2;
    font=FcFreeTypeQuery((const FcChar8*)argv[1],0,NULL,&count);
    if (!font || count<1) return 3;
    FcPatternDestroy(font);
    if (!FcConfigAppFontAddFile(config,(const FcChar8*)argv[1])) return 4;
    pattern=FcNameParse((const FcChar8*)"monospace");if (!pattern) return 5;
    FcConfigSubstitute(config,pattern,FcMatchPattern);FcConfigSetDefaultSubstitute(config,pattern);
    match=FcFontMatch(config,pattern,&result);if (!match || result!=FcResultMatch) return 6;
    FcPatternDestroy(match);FcPatternDestroy(pattern);FcConfigDestroy(config);FcFini();return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs fontconfig) -o "$work/probe"
"$work/probe" /sources/phase2/inputs/fontconfig-2.18.3/test/4x6.pcf
fc-scan --format '%{family}\n' /sources/phase2/inputs/fontconfig-2.18.3/test/4x6.pcf > "$work/scanned"
test -s "$work/scanned"
NATIVE
