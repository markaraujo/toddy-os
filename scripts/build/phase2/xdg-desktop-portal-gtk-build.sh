#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# GNOME backend provides wallpaper with the selected GNOME4 desktop library.
# GTK wallpaper would add an otherwise unselected legacy GNOME3 desktop library.
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
 --wrap-mode=nofallback -Dwallpaper=disabled -Dsettings=enabled \
 -Dappchooser=enabled -Dlockdown=enabled
ninja -C /build/compile -j4
meson install -C /build/compile --destdir /stage --no-rebuild
python3 /src/toddy-build-result.py xdg-desktop-portal-gtk 1.15.3 usr/libexec/xdg-desktop-portal-gtk
