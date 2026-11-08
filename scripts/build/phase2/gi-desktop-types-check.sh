#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status}' gi-desktop-types) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
for namespace in freetype2 fontconfig libxml2 cairo; do
    gi-inspect-typelib --print-shlibs --print-typelibs "$namespace"
done
work=$(mktemp -d /tmp/toddy-gi-types-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <girepository.h>
int main(void) {
    const char *names[]={"freetype2","fontconfig","libxml2","cairo"};
    const char *versions[]={"2.0","2.0","2.0","1.0"};
    const char *types[]={"Face","Pattern","Node","Surface"};
    GIRepository *repo=g_irepository_get_default();
    for (int i=0;i<4;i++) {
        GError *error=NULL;GIBaseInfo *info;
        if (!g_irepository_require(repo,names[i],versions[i],0,&error) || error) return 1;
        info=g_irepository_find_by_name(repo,names[i],types[i]);
        if (!info || g_base_info_get_type(info)!=GI_INFO_TYPE_STRUCT) return 2;
        g_base_info_unref(info);
    }
    return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs gobject-introspection-1.0) -o "$work/probe"
"$work/probe"
NATIVE
