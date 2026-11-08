#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion shared-mime-info) == 2.5.1 ]]
[[ $(dpkg-query -W -f='${Status}' shared-mime-info) == 'install ok installed' ]]
dpkg-query -S /usr/share/mime/mime.cache | grep -q '^shared-mime-info:'
test -s /usr/share/mime/mime.cache
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-mime-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <gio/gio.h>
#include <string.h>
int main(void) {
    gboolean uncertain=TRUE;gchar *type;GList *registered;
    static const guchar png[]={137,80,78,71,13,10,26,10};
    type=g_content_type_guess("proof.txt",(const guchar*)"Toddy text\n",strlen("Toddy text\n"),&uncertain);
    if (!type || strcmp(type,"text/plain") || uncertain) return 1;g_free(type);
    type=g_content_type_guess("proof.png",png,sizeof(png),&uncertain);
    if (!type || strcmp(type,"image/png") || uncertain) return 2;g_free(type);
    type=g_content_type_guess("proof.json",(const guchar*)"{}",2,&uncertain);
    if (!type || strcmp(type,"application/json") || uncertain) return 3;g_free(type);
    registered=g_content_types_get_registered();if (g_list_length(registered)<100) return 4;
    g_list_free_full(registered,g_free);return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs gio-2.0) -o "$work/probe"
"$work/probe"
NATIVE
