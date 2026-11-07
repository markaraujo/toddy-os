#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion gio-2.0) == 2.88.3 ]]
[[ $(dpkg-query -W -f='${Status}' glib) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-glib-check.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <gio/gio.h>
#include <string.h>
int main(void) {
  GVariant *v = g_variant_ref_sink(g_variant_new("(st)", "toddy", (guint64)42));
  const char *name; guint64 sequence;
  g_variant_get(v, "(&st)", &name, &sequence);
  if (strcmp(name, "toddy") || sequence != 42) return 1;
  g_variant_unref(v);
  GDBusNodeInfo *node = g_dbus_node_info_new_for_xml(
    "<node><interface name='io.github.markaraujo.Toddy.Service1'>"
    "<method name='GetCapabilities'><arg type='s' direction='out'/></method>"
    "</interface></node>", NULL);
  if (!node) return 2;
  g_dbus_node_info_unref(node);
  return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs gio-2.0) -o "$work/probe"
"$work/probe"
NATIVE
