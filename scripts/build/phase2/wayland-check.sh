#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
for module in wayland-client wayland-server wayland-scanner wayland-cursor;do
    [[ $(pkg-config --modversion "$module") == 1.26.0 ]]
done
# Upstream egl/meson.build declares distinct public pkg-config API versions.
[[ $(pkg-config --modversion wayland-egl) == 18.1.0 ]]
[[ $(pkg-config --modversion wayland-egl-backend) == 3 ]]
[[ $(dpkg-query -W -f='${Status}' wayland) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-wayland-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
wayland-scanner --version 2>&1 | grep -F '1.26.0'
wayland-scanner client-header /usr/share/wayland/wayland.xml "$work/core-client.h"
cat > "$work/probe.c" <<'C'
#include <wayland-client.h>
#include <wayland-server.h>
#include <sys/socket.h>
#include <unistd.h>
#include <stdint.h>
static void complete(void *data, struct wl_callback *callback, uint32_t serial) {
    (void)serial; *(int *)data=1; wl_callback_destroy(callback);
}
int main(void) {
    int pair[2],done=0; struct wl_display *server,*client; struct wl_callback *callback;
    const struct wl_callback_listener listener={complete};
    alarm(3);
    if (socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,pair)) return 1;
    server=wl_display_create(); if (!server || !wl_client_create(server,pair[0])) return 2;
    client=wl_display_connect_to_fd(pair[1]); if (!client) return 3;
    callback=wl_display_sync(client); if (!callback) return 4;
    if (wl_callback_add_listener(callback,&listener,&done)) return 5;
    if (wl_display_flush(client)<0) return 6;
    if (wl_event_loop_dispatch(wl_display_get_event_loop(server),0)<0) return 7;
    wl_display_flush_clients(server);
    if (wl_display_dispatch(client)<0 || !done || wl_display_get_error(client)) return 8;
    wl_display_disconnect(client); wl_display_destroy_clients(server); wl_display_destroy(server);
    alarm(0); return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs wayland-client wayland-server) -o "$work/probe"
"$work/probe"
NATIVE
