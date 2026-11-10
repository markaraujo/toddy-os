#!/usr/bin/env python3
"""Promote a declared successful compiler stage through the native backend only.

Invoked inside run_step's full-root transaction, never by the compiler namespace.
"""
import collections
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from verify_stage import inspect_stage
from package_copyright import write_copyright
from llvm_runtime import split_runtime
from llvm_recover import merge_support_results
from rust_std_tests import qualify_preserved_log

ROOT = Path('/opt/toddy-build')
PROFILES = {
    'cups': ('2.4.19', 'glibc (>= 2.44-1+toddy1), gcc (= 16.2.0-1+toddy2), acl (= 2.4.0-1+toddy1), gnutls (= 3.8.13-1+toddy1), linux-pam (= 1.7.2-1+toddy2), libusb (= 1.0.30-1+toddy1), libxcrypt (= 4.5.2-1+toddy1), zlib (>= 1.3.2-1), dbus (>= 1.16.2-1), systemd (>= 261.2-1+toddy3), shadow (>= 4.20.2-1)', 'cups-2.4.19-source.tar.gz', 'usr/lib/pkgconfig/cups.pc'),
    'mitkrb': ('1.22.2', 'glibc (>= 2.44-1+toddy1), e2fsprogs (= 1.47.4-1+toddy1), openssl (= 4.0.3-1+toddy1)', 'krb5-1.22.2.tar.gz', 'usr/lib/pkgconfig/krb5.pc'),
    'libgtop': ('2.41.3', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), libxau (= 1.0.12-1+toddy1)', 'libgtop-2.41.3.tar.xz', 'usr/lib/pkgconfig/libgtop-2.0.pc'),
    'colord-gtk': ('0.3.1', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), colord (= 1.4.8-1+toddy1), gtk (>= 4.22.4-1+toddy9), gtk3 (= 3.24.52-1+toddy2)', 'colord-gtk-0.3.1.tar.xz', 'usr/lib/pkgconfig/colord-gtk4.pc'),
    'modemmanager': ('1.24.2', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), libmbim (= 1.34.0-1+toddy1), libqmi (= 1.38.0-1+toddy1), libgudev (= 238-1+toddy1), polkit (= 127-1+toddy1), dbus (>= 1.16.2-1), systemd (>= 261.2-1+toddy3)', 'ModemManager-1.24.2.tar.gz', 'usr/lib/pkgconfig/mm-glib.pc'),
    'libqmi': ('1.38.0', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), libmbim (= 1.34.0-1+toddy1), libgudev (= 238-1+toddy1)', 'libqmi-1.38.0.tar.gz', 'usr/lib/pkgconfig/qmi-glib.pc'),
    'libmbim': ('1.34.0', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2)', 'libmbim-1.34.0.tar.gz', 'usr/lib/pkgconfig/mbim-glib.pc'),
    'gnome-bluetooth': ('47.2', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy9), libadwaita (= 1.9.3-1+toddy1), gsound (= 1.0.3-1+toddy2), libnotify (= 0.8.8-1+toddy1), upower (= 1.91.3-1+toddy1), systemd (>= 261.2-1+toddy3)', 'gnome-bluetooth-47.2.tar.xz', 'usr/lib/pkgconfig/gnome-bluetooth-ui-3.0.pc'),
    'gsound': ('1.0.3', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), libcanberra (= 0.30-1+toddy2)', 'gsound-1.0.3.tar.xz', 'usr/lib/pkgconfig/gsound.pc'),
    'libpwquality': ('1.4.5', 'glibc (>= 2.44-1+toddy1), cracklib (= 2.10.3-1+toddy1), linux-pam (= 1.7.2-1+toddy2)', 'libpwquality-1.4.5.tar.bz2', 'usr/lib/pkgconfig/pwquality.pc'),
    'cracklib': ('2.10.3', 'glibc (>= 2.44-1+toddy1), zlib (= 1.3.2-1+toddy1)', 'cracklib-2.10.3.tar.xz', 'usr/include/crack.h'),
    'gnome-online-accounts': ('3.58.1', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy9), libadwaita (= 1.9.3-1+toddy1), librest (= 0.10.2-1+toddy1), libsecret (= 0.21.7-1+toddy1), libsoup (= 3.6.6-1+toddy1), json-glib (= 1.10.8-1+toddy1), libxml2 (= 2.15.3-1+toddy1)', 'gnome-online-accounts-3.58.1.tar.xz', 'usr/lib/pkgconfig/goa-backend-1.0.pc'),
    'librest': ('0.10.2', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), libsoup (= 3.6.6-1+toddy1), json-glib (= 1.10.8-1+toddy1), libxml2 (= 2.15.3-1+toddy1)', 'librest-0.10.2.tar.xz', 'usr/lib/pkgconfig/rest-1.0.pc'),
    'tecla': ('50.0', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy9), libadwaita (= 1.9.3-1+toddy1), libxkbcommon (= 1.13.2-1+toddy1)', 'tecla-50.0.tar.xz', 'usr/bin/tecla'),
    'gnome-text-editor': ('50.1', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy8), gtksourceview (= 5.20.0-1+toddy1), libadwaita (= 1.9.3-1+toddy1), libspelling (= 0.4.11-1+toddy1), editorconfig (= 0.12.11-1+toddy1)', 'gnome-text-editor-50.1.tar.xz', 'usr/bin/gnome-text-editor'),
    'editorconfig': ('0.12.11', 'glibc (>= 2.44-1+toddy1), pcre2 (= 10.49-1+toddy1)', 'editorconfig-0.12.11.tar.gz', 'usr/lib/pkgconfig/editorconfig.pc'),
    'libspelling': ('0.4.11', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy8), gtksourceview (= 5.20.0-1+toddy1), enchant (= 2.8.19-1+toddy1), icu (= 78.3-1+toddy1)', 'libspelling-0.4.11.tar.xz', 'usr/lib/pkgconfig/libspelling-1.pc'),
    'enchant': ('2.8.19', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2), glib (= 2.88.3-1+toddy2), aspell (= 0.60.8.2-1+toddy1)', 'enchant-2.8.19.tar.gz', 'usr/lib/pkgconfig/enchant-2.pc'),
    'aspell': ('0.60.8.2', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2), ncurses (= 6.6-1+toddy1)', 'aspell-0.60.8.2.tar.gz', 'usr/include/aspell.h'),
    'gexiv2': ('0.16.2', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2), glib (= 2.88.3-1+toddy2), exiv2 (= 0.28.8-1+toddy1), pygobject (= 3.56.3-1+toddy1), python (>= 3.14), python (<< 3.15)', 'gexiv2-0.16.2.tar.xz', 'usr/lib/pkgconfig/gexiv2-0.16.pc'),
    'exiv2': ('0.28.8', 'glibc (= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2), zlib (= 1.3.2-1+toddy1), expat (= 2.10.0-1+toddy1), brotli (= 1.2.0-1+toddy1), inih (= 62-1+toddy1)', 'exiv2-0.28.8.tar.gz', 'usr/lib/pkgconfig/exiv2.pc'),
    'brotli': ('1.2.0', 'glibc (>= 2.44-1+toddy1)', 'brotli-1.2.0.tar.gz', 'usr/lib/pkgconfig/libbrotlidec.pc'),
    'inih': ('62', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2)', 'inih-r62.tar.gz', 'usr/lib/pkgconfig/inih.pc'),
    'blueprint-compiler': ('0.22.2', 'python (>= 3.14), python (<< 3.15), pygobject (= 3.56.3-1+toddy1), gtk (>= 4.22.4-1+toddy8), gobject-introspection (>= 1.86.0-1+toddy1)', 'blueprint-compiler-0.22.2.tar.xz', 'usr/bin/blueprint-compiler'),
    'glycin-gtk4': ('2.1.0', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), glycin (= 2.1.5-1+toddy1), gtk (>= 4.22.4-1+toddy8), glib (= 2.88.3-1+toddy2), lcms2 (= 2.19.1-1+toddy1), libseccomp (= 2.6.1-1+toddy1)', 'glycin-2.1.5.tar.xz', 'usr/lib/pkgconfig/glycin-gtk4-2.pc'),
    'tinysparql': ('3.11.1', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), icu (= 78.3-1+toddy1), json-glib (= 1.10.8-1+toddy1), libxml2 (= 2.15.3-1+toddy1), sqlite (= 3.53.4-1+toddy1), libsoup (= 3.6.6-1+toddy1)', 'tinysparql-3.11.1.tar.xz', 'usr/lib/pkgconfig/tinysparql-3.0.pc'),
    'gnome-autoar': ('0.4.5', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk3 (= 3.24.52-1+toddy2), libarchive (= 3.8.11-1+toddy1)', 'gnome-autoar-0.4.5.tar.xz', 'usr/lib/pkgconfig/gnome-autoar-0.pc'),
    'libportal': ('0.9.1', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk3 (= 3.24.52-1+toddy2), gtk (>= 4.22.4-1+toddy8)', 'libportal-0.9.1.tar.xz', 'usr/lib/pkgconfig/libportal-gtk4.pc'),
    'gnome-terminal': ('3.60.0', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2), glib (= 2.88.3-1+toddy2), gtk3 (= 3.24.52-1+toddy2), vte (= 0.84.1-1+toddy1), libhandy (= 1.8.3-1+toddy1), pcre2 (= 10.49-1+toddy1), gsettings-desktop-schemas (= 50.1-1+toddy1), util-linux (>= 2.42.4-1), dconf (= 0.49.0-1+toddy1)', 'gnome-terminal-3.60.0.tar.gz', 'usr/bin/gnome-terminal'),
    'libxslt': ('1.1.45', 'glibc (>= 2.44-1+toddy1), libxml2 (= 2.15.3-1+toddy1)', 'libxslt-1.1.45.tar.xz', 'usr/lib/pkgconfig/libxslt.pc'),
    'libhandy': ('1.8.3', 'glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), gtk3 (= 3.24.52-1+toddy2), fribidi (= 1.0.16-1+toddy1)', 'libhandy-1.8.3.tar.xz', 'usr/lib/pkgconfig/libhandy-1.pc'),
    'vte': ('0.84.1', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2), glib (= 2.88.3-1+toddy2), gtk3 (= 3.24.52-1+toddy2), pango (= 1.58.2-1+toddy1), cairo (= 1.18.4-1+toddy1), pcre2 (= 10.49-1+toddy1), lz4 (= 1.10.0-1+toddy1), simdutf (= 9.0.0-1+toddy1), fribidi (= 1.0.16-1+toddy1), gnutls (= 3.8.13-1+toddy1), icu (= 78.3-1+toddy1), systemd (>= 261.2-1+toddy3), at-spi2-core (= 2.60.6-1+toddy1)', 'vte-0.84.1.tar.gz', 'usr/lib/pkgconfig/vte-2.91.pc'),
    'simdutf': ('9.0.0', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2)', 'simdutf-9.0.0.tar.gz', 'usr/lib/pkgconfig/simdutf.pc'),
    'fmt': ('12.2.0', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1+toddy2)', 'fmt-12.2.0.tar.gz', 'usr/lib/pkgconfig/fmt.pc'),
    'fast-float': ('8.2.10', '', 'fast_float-8.2.10.tar.gz', 'usr/share/cmake/FastFloat/FastFloatConfig.cmake'),
    'gst-plugins-base': ('1.28.6', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gstreamer (= 1.28.6-1+toddy1), alsa-lib (= 1.2.16.1-1+toddy1), libogg (= 1.3.6-1+toddy1), libvorbis (= 1.3.7-1+toddy1), pango (= 1.58.2-1+toddy1), iso-codes (= 4.20.1-1+toddy1), libgudev (= 238-1+toddy1), mesa (= 26.1.7-1+toddy1), graphene (= 1.10.8-1+toddy1), libjpeg-turbo (= 3.2.0-1+toddy1), libpng (= 1.6.58-1+toddy1), wayland (= 1.26.0-1+toddy1), libdrm (= 2.4.134-1+toddy1)', 'gst-plugins-base-1.28.6.tar.xz', 'usr/lib/pkgconfig/gstreamer-video-1.0.pc'),
    'gstreamer': ('1.28.6', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2)', 'gstreamer-1.28.6.tar.xz', 'usr/lib/pkgconfig/gstreamer-1.0.pc'),
    'gnome-shell': ('50.4', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), mutter (= 50.4-1+toddy1), gjs (= 1.88.1-1+toddy1), gtk (>= 4.22.4-1+toddy7), evolution-data-server (= 3.60.2-1+toddy1), gcr (= 4.4.0.1-1+toddy1), gnome-desktop (= 44.5-1+toddy1), libnma (= 1.10.6-1+toddy1), networkmanager (= 1.58.1-1+toddy1), gdm (= 50.2-1+toddy1), libgweather (= 4.6.0-1+toddy1), ibus (= 1.5.34~rc2-1+toddy1), libsecret (= 0.21.7-1+toddy1), pipewire (= 1.6.8-1+toddy1), gsettings-desktop-schemas (= 50.1-1+toddy1), at-spi2-core (= 2.60.6-1+toddy1), libxml2 (= 2.15.3-1+toddy1), json-glib (= 1.10.8-1+toddy1), libcanberra (= 0.30-1+toddy2), polkit (= 127-1+toddy1), systemd (>= 261.2-1+toddy3)', 'gnome-shell-50.4.tar.xz', 'usr/bin/gnome-shell'),
    'gnome-settings-daemon': ('50.1', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gnome-desktop (= 44.5-1+toddy1), gsettings-desktop-schemas (= 50.1-1+toddy1), geocode-glib (= 3.26.4-1+toddy1), libgweather (= 4.6.0-1+toddy1), geoclue (= 2.8.2-1+toddy1), libcanberra (= 0.30-1+toddy2), libnotify (= 0.8.8-1+toddy1), pulseaudio (= 17.0-1+toddy2), polkit (= 127-1+toddy1), upower (= 1.91.3-1+toddy1), systemd (>= 261.2-1+toddy3), libgudev (= 238-1+toddy1), gcr (= 4.4.0.1-1+toddy1), colord (= 1.4.8-1+toddy1), networkmanager (= 1.58.1-1+toddy1), alsa-lib (= 1.2.16.1-1+toddy1)', 'gnome-settings-daemon-50.1.tar.xz', 'usr/lib/pkgconfig/gnome-settings-daemon.pc'),
    'gdm': ('50.2', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), libgudev (= 238-1+toddy1), accountsservice (= 26.27.3-1+toddy1), polkit (= 127-1+toddy1), systemd (>= 261.2-1+toddy3), linux-pam (= 1.7.2-1+toddy2), toddy-login-policy (= 0.1.0-1+toddy1), dconf (= 0.49.0-1+toddy1), json-glib (= 1.10.8-1+toddy1), dbus (>= 1.16.2-1)', 'gdm-50.2.tar.xz', 'usr/lib/pkgconfig/gdm.pc'),
    'libnma': ('1.10.6', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy7), gtk3 (>= 3.24.52-1+toddy2), networkmanager (= 1.58.1-1+toddy1), gcr (= 4.4.0.1-1+toddy1), iso-codes (= 4.20.1-1+toddy1)', 'libnma-1.10.6.tar.xz', 'usr/lib/pkgconfig/libnma-gtk4.pc'),
    'networkmanager': ('1.58.1', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), libndp (= 1.9-1+toddy1), gnutls (= 3.8.13-1+toddy1), libpsl (= 0.23.3-1+toddy1), curl (>= 8.23.0-1), readline (>= 8.3-1), util-linux (>= 2.42.4-1), dbus (>= 1.16.2-1), systemd (>= 261.2-1+toddy3), polkit (= 127-1+toddy1)', 'NetworkManager-1.58.1.tar.xz', 'usr/lib/pkgconfig/libnm.pc'),
    'libndp': ('1.9', 'glibc (>= 2.44-1+toddy1)', 'libndp-1.9.tar.gz', 'usr/lib/pkgconfig/libndp.pc'),
    'geoclue': ('2.8.2', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), libsoup (= 3.6.6-1+toddy1), json-glib (= 1.10.8-1+toddy1), systemd (>= 261.2-1+toddy3), gobject-introspection (>= 1.86.0-1+toddy1)', 'geoclue-2.8.2.tar.bz2', 'usr/lib/pkgconfig/libgeoclue-2.0.pc'),
    'libgweather': ('4.6.0', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), libsoup (= 3.6.6-1+toddy1), libxml2 (= 2.15.3-1+toddy1), json-glib (= 1.10.8-1+toddy1), geocode-glib (= 3.26.4-1+toddy1), gweather-locations (= 2026.2-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)', 'libgweather-4.6.0.tar.xz', 'usr/lib/pkgconfig/gweather4.pc'),
    'gweather-locations': ('2026.2', 'glib (>= 2.88.3-1+toddy2)', 'gweather-locations-2026.2.tar.xz', 'usr/lib/gweather-locations/Locations.bin'),
    'geocode-glib': ('3.26.4', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), json-glib (= 1.10.8-1+toddy1), libsoup (= 3.6.6-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)', 'geocode-glib-3.26.4.tar.xz', 'usr/lib/pkgconfig/geocode-glib-2.0.pc'),
    'ibus': ('1.5.34~rc2', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy5), gtk3 (>= 3.24.52-1+toddy1), dconf (= 0.49.0-1+toddy1), dbus (>= 1.16.2-1), wayland (>= 1.26.0-1+toddy1), libxkbcommon (= 1.13.2-1+toddy1), libnotify (= 0.8.8-1+toddy1), libevdev (= 1.13.6-1+toddy1), libx11 (= 1.8.13-1+toddy1), python (>= 3.14), python (<< 3.15), pygobject (= 3.56.3-1+toddy1), gnome-desktop (= 44.5-1+toddy1), iso-codes (= 4.20.1-1+toddy1), xkeyboard-config (= 2.48-1+toddy1), systemd (>= 261.2-1+toddy3)', 'ibus-1.5.34.tar.gz', 'usr/lib/pkgconfig/ibus-1.0.pc'),
    'unicode-ucd': ('17.0.0', '', 'UCD-17.0.0.zip', 'usr/share/unicode/ucd/UnicodeData.txt'),
    'vala': ('0.56.19', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gcc (>= 16.2.0-1), pkgconf (>= 2.5.1-1)', 'vala-0.56.19.tar.xz', 'usr/lib/pkgconfig/libvala-0.56.pc'),
    'evolution-data-server': ('3.60.2', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1), glib (>= 2.88.3-1+toddy2), libsoup (= 3.6.6-1+toddy1), libical (= 4.0.5-1+toddy1), libsecret (= 0.21.7-1+toddy1), libxml2 (= 2.15.3-1+toddy1), json-glib (= 1.10.8-1+toddy1), nss (= 3.126-1+toddy1), nspr (= 4.40-1+toddy1), sqlite (= 3.53.4-1+toddy1), icu (= 78.3-1+toddy1), gtk (>= 4.22.4-1+toddy4), gtk3 (>= 3.24.52-1+toddy1), zlib (>= 1.3.2-1), util-linux (>= 2.42.4-1)', 'evolution-data-server-3.60.2.tar.xz', 'usr/lib/pkgconfig/libecal-2.0.pc'),
    'libsoup': ('3.6.6', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), glib-networking (= 2.80.1-1+toddy1), nghttp2 (= 1.71.0-1+toddy1), libpsl (= 0.23.3-1+toddy1), sqlite (= 3.53.4-1+toddy1), zlib (>= 1.3.2-1)', 'libsoup-3.6.6.tar.xz', 'usr/lib/pkgconfig/libsoup-3.0.pc'),
    'glib-networking': ('2.80.1', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gnutls (= 3.8.13-1+toddy1), libproxy (= 0.5.12-1+toddy1), gsettings-desktop-schemas (= 50.1-1+toddy1)', 'glib-networking-2.80.1.tar.xz', 'usr/lib/gio/modules/libgiognutls.so'),
    'libproxy': ('0.5.12', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), curl (>= 8.23.0-1), duktape (= 2.7.0-1+toddy1), gsettings-desktop-schemas (= 50.1-1+toddy1)', 'libproxy-0.5.12.tar.gz', 'usr/lib/pkgconfig/libproxy-1.0.pc'),
    'gnutls': ('3.8.13', 'glibc (>= 2.44-1+toddy1), nettle (= 4.0-1+toddy1), libunistring (= 1.4.2-1+toddy1), libidn2 (= 2.3.8-1+toddy1), libtasn1 (= 4.21.0-1+toddy1), p11-kit (>= 0.26.5-1+toddy1), p11-kit (<< 0.26.6), ca-certificates (>= 2026.11.09-1+toddy1)', 'gnutls-3.8.13.tar.xz', 'usr/lib/pkgconfig/gnutls.pc'),
    'libidn2': ('2.3.8', 'glibc (>= 2.44-1+toddy1), libunistring (= 1.4.2-1+toddy1)', 'libidn2-2.3.8.tar.gz', 'usr/lib/pkgconfig/libidn2.pc'),
    'libunistring': ('1.4.2', 'glibc (>= 2.44-1+toddy1)', 'libunistring-1.4.2.tar.xz', 'usr/include/unistring/version.h'),
    'nettle': ('4.0', 'glibc (>= 2.44-1+toddy1), gmp (= 6.3.0-1+toddy1)', 'nettle-4.0.tar.gz', 'usr/lib/pkgconfig/hogweed.pc'),
    'libpsl': ('0.23.3', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1), icu (= 78.3-1+toddy1)', 'libpsl-0.23.3.tar.gz', 'usr/lib/pkgconfig/libpsl.pc'),
    'nss': ('3.126', 'glibc (>= 2.44-1+toddy1), nspr (= 4.40-1+toddy1), sqlite (= 3.53.4-1+toddy1), zlib (= 1.3.2-1+toddy1)', 'nss-3.126.tar.gz', 'usr/lib/pkgconfig/nss.pc'),
    'nspr': ('4.40', 'glibc (>= 2.44-1+toddy1)', 'nspr-4.40.tar.gz', 'usr/lib/pkgconfig/nspr.pc'),
    'libical': ('4.0.5', 'glibc (>= 2.44-1+toddy1), gcc (>= 16.2.0-1), glib (>= 2.88.3-1+toddy2), icu (= 78.3-1+toddy1), libxml2 (= 2.15.3-1+toddy1)', 'libical-4.0.5.tar.gz', 'usr/lib/pkgconfig/libical-glib.pc'),
    'gnome-keyring': ('50.0', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gcr3 (= 3.41.2-1+toddy1), libgcrypt (>= 1.12.4-1), p11-kit (= 0.26.5-1+toddy1), linux-pam (= 1.7.2-1+toddy2), libsecret (= 0.21.7-1+toddy1)', 'gnome-keyring-50.0.tar.xz', 'usr/bin/gnome-keyring-daemon'),
    'gcr3': ('3.41.2', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gtk3 (>= 3.24.52-1+toddy1), p11-kit (= 0.26.5-1+toddy1), libgcrypt (>= 1.12.4-1), gnupg (>= 2.5.24-1)', 'gcr-3.41.2.tar.xz', 'usr/lib/pkgconfig/gcr-base-3.pc'),
    'libsecret': ('0.21.7', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), libgcrypt (>= 1.12.4-1)', 'libsecret-0.21.7.tar.xz', 'usr/lib/pkgconfig/libsecret-1.pc'),
    'gcr': ('4.4.0.1', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gtk (>= 4.22.4-1+toddy4), p11-kit (= 0.26.5-1+toddy1), libgcrypt (>= 1.12.4-1), gnupg (>= 2.5.24-1)', 'gcr-4.4.0.1.tar.xz', 'usr/lib/pkgconfig/gcr-4.pc'),
    'p11-kit': ('0.26.5', 'glibc (>= 2.44-1+toddy1), libffi (>= 3.8.0-1), libtasn1 (= 4.21.0-1+toddy1)', 'p11-kit-0.26.5.tar.xz', 'usr/lib/pkgconfig/p11-kit-1.pc'),
    'libtasn1': ('4.21.0', 'glibc (>= 2.44-1+toddy1)', 'libtasn1-4.21.0.tar.gz', 'usr/lib/pkgconfig/libtasn1.pc'),
    'gnome-session': ('50.1', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), gnome-desktop (= 44.5-1+toddy1), json-glib (= 1.10.8-1+toddy1), upower (= 1.91.3-1+toddy1), systemd (>= 261.2-1+toddy3)', 'gnome-session-50.1.tar.xz', 'usr/bin/gnome-session'),
    'upower': ('1.91.3', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), libgudev (= 238-1+toddy1), polkit (= 127-1+toddy1), systemd (>= 261.2-1+toddy3)', 'upower-v1.91.3.tar.bz2', 'usr/lib/pkgconfig/upower-glib.pc'),
    'accountsservice': ('26.27.3', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), polkit (= 127-1+toddy1), json-c (= 0.19-1+toddy1), libxcrypt (= 4.5.2-1+toddy1), systemd (>= 261.2-1+toddy3), shadow (>= 4.20.2-1)', 'accountsservice-26.27.3.tar.bz2', 'usr/lib/pkgconfig/accountsservice.pc'),
    'json-c': ('0.19', 'glibc (>= 2.44-1+toddy1)', 'json-c-0.19.tar.gz', 'usr/lib/pkgconfig/json-c.pc'),
    'polkit': ('127', 'glibc (>= 2.44-1+toddy1), glib (>= 2.88.3-1+toddy2), linux-pam (= 1.7.2-1+toddy2), duktape (= 2.7.0-1+toddy1), systemd (>= 261.2-1+toddy3), expat (>= 2.10.0-1+toddy1), dbus (>= 1.16.2-1), shadow (>= 4.20.2-1)', 'polkit-127.tar.gz', 'usr/lib/pkgconfig/polkit-gobject-1.pc'),
    'dconf': ('0.49.0', 'glib (>= 2.88.3-1+toddy2), dbus (>= 1.16.2-1), systemd (>= 261.2-1+toddy3)', 'dconf-0.49.0.tar.xz', 'usr/lib/pkgconfig/dconf.pc'),
    'python-dbusmock': ('0.38.1', 'python (>= 3.14), python (<< 3.15), dbus-python (= 1.4.0-1+toddy1), pygobject (>= 3.56.3-1+toddy1)', 'python_dbusmock-0.38.1.tar.gz', 'usr/lib/python3.14/site-packages/dbusmock/__init__.py'),
    'dbus-python': ('1.4.0', 'python (>= 3.14), python (<< 3.15), dbus (>= 1.16.2-1), glib (>= 2.88.3-1+toddy2)', 'dbus-python-1.4.0.tar.xz', 'usr/lib/pkgconfig/dbus-python.pc'),
    'duktape': ('2.7.0', 'glibc (>= 2.44-1)', 'duktape-2.7.0.tar.xz', 'usr/lib/pkgconfig/duktape.pc'),
    'linux-pam': ('1.7.2', 'glibc (>= 2.44-1), libxcrypt (= 4.5.2-1+toddy1), systemd (>= 261.2-1+toddy2)', 'Linux-PAM-1.7.2.tar.xz', 'usr/lib/pkgconfig/pam.pc'),
    'gjs': ('1.88.1', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), glib (>= 2.88.3-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1), cairo (= 1.18.4-1+toddy1), libffi (>= 3.8.0-1), mozjs (= 140.17.0-1+toddy1), readline (>= 8.3-1)', 'gjs-1.88.1.tar.xz', 'usr/lib/pkgconfig/gjs-1.0.pc'),
    'mozjs': ('140.17.0', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), icu (= 78.3-1+toddy1), readline (>= 8.3-1), zlib (>= 1.3.2-1)', 'firefox-140.17.0esr.source.tar.xz', 'usr/lib/pkgconfig/mozjs-140.pc'),
    'gtksourceview': ('5.20.0', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), gtk (>= 4.22.4-1+toddy4), pcre2 (>= 10.49-1+toddy1), libxml2 (= 2.15.3-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)', 'gtksourceview-5.20.0.tar.xz', 'usr/lib/pkgconfig/gtksourceview-5.pc'),
    'cbindgen': ('0.29.4', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1)', 'cbindgen-0.29.4.tar.gz', 'usr/bin/cbindgen'),
    'icu': ('78.3', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1)', 'icu4c-78.3-sources.tgz', 'usr/lib/pkgconfig/icu-uc.pc'),
    'libadwaita': ('1.9.3', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), gtk (>= 4.22.4-1+toddy4), pango (= 1.58.2-1+toddy1), fribidi (= 1.0.16-1+toddy1), graphene (= 1.10.8-1+toddy1), appstream (= 1.1.6-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)', 'libadwaita-1.9.3.tar.xz', 'usr/lib/pkgconfig/libadwaita-1.pc'),
    'gi-gl-types': ('1.86.0', 'gobject-introspection (>= 1.86.0-1+toddy1)', 'gobject-introspection-1.86.0.tar.xz', 'usr/share/gir-1.0/GL-1.0.gir'),
    'docutils': ('0.23', 'python (>= 3.14), python (<< 3.15)', 'docutils-0.23.tar.gz', 'usr/bin/rst2man'),
    'colord': ('1.4.8', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), lcms2 (= 2.19.1-1+toddy1), libgusb (= 0.4.9-1+toddy1), libgudev (= 238-1+toddy1), systemd (>= 261.2-1+toddy2)', 'colord-1.4.8.tar.xz', 'usr/lib/pkgconfig/colord.pc'),
    'libgusb': ('0.4.9', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), json-glib (= 1.10.8-1+toddy1), libusb (= 1.0.30-1+toddy1), hwdata (= 0.410-1+toddy1)', 'libgusb-0.4.9.tar.xz', 'usr/lib/pkgconfig/gusb.pc'),
    'libusb': ('1.0.30', 'glibc (>= 2.44-1), systemd (>= 261.2-1)', 'libusb-1.0.30.tar.bz2', 'usr/lib/pkgconfig/libusb-1.0.pc'),
    'libcanberra': ('0.30', 'glibc (>= 2.44-1), libvorbis (= 1.3.7-1+toddy1), alsa-lib (= 1.2.16.1-1+toddy1), pulseaudio (= 17.0-1+toddy1), libtool (>= 2.5.4-1)', 'libcanberra-0.30.tar.xz', 'usr/lib/pkgconfig/libcanberra.pc'),
    'pulseaudio': ('17.0', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), dbus (>= 1.16.2-1), systemd (>= 261.2-1), libsndfile (= 1.2.2-1+toddy1)', 'pulseaudio-17.0.tar.xz', 'usr/lib/pkgconfig/libpulse.pc'),
    'libsndfile': ('1.2.2', 'glibc (>= 2.44-1), alsa-lib (= 1.2.16.1-1+toddy1)', 'libsndfile-1.2.2.tar.xz', 'usr/lib/pkgconfig/sndfile.pc'),
    'libvorbis': ('1.3.7', 'glibc (>= 2.44-1), libogg (= 1.3.6-1+toddy1)', 'libvorbis-1.3.7.tar.xz', 'usr/lib/pkgconfig/vorbis.pc'),
    'libogg': ('1.3.6', 'glibc (>= 2.44-1)', 'libogg-1.3.6.tar.xz', 'usr/lib/pkgconfig/ogg.pc'),
    'json-glib': ('1.10.8', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1)',
                  'json-glib-1.10.8.tar.xz', 'usr/lib/pkgconfig/json-glib-1.0.pc'),
    'gnome-desktop': ('44.5', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), gtk (>= 4.22.4-1+toddy3), gdk-pixbuf (= 2.44.7-1+toddy2), fontconfig (>= 2.18.3-1+toddy1), xkeyboard-config (= 2.48-1+toddy1), iso-codes (= 4.20.1-1+toddy1), systemd (>= 261.2-1), libseccomp (= 2.6.1-1+toddy1), bubblewrap (= 0.11.2-1+toddy1)',
                       'gnome-desktop-44.5.tar.xz', 'usr/lib/pkgconfig/gnome-desktop-4.pc'),
    'libwacom': ('2.19.1', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), libgudev (= 238-1+toddy1), libevdev (= 1.13.6-1+toddy1), python (>= 3.14)',
                 'libwacom-2.19.1.tar.xz', 'usr/lib/pkgconfig/libwacom.pc'),
    'libgudev': ('238', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), systemd (>= 261.2-1)',
                 'libgudev-238.tar.xz', 'usr/lib/pkgconfig/gudev-1.0.pc'),
    'libnotify': ('0.8.8', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), gdk-pixbuf (= 2.44.7-1+toddy2), dbus (>= 1.16.2-1)',
                  'libnotify-0.8.8.tar.xz', 'usr/lib/pkgconfig/libnotify.pc'),
    'wireplumber': ('0.5.15', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), systemd (>= 261.2-1), pipewire (= 1.6.8-1+toddy1), lua (= 5.4.8-1+toddy1)',
                    'wireplumber-0.5.15.tar.bz2', 'usr/lib/pkgconfig/wireplumber-0.5.pc'),
    'lua': ('5.4.8', 'glibc (>= 2.44-1)',
            'lua-5.4.8.tar.gz', 'usr/lib/pkgconfig/lua.pc'),
    'pipewire': ('1.6.8', 'glibc (>= 2.44-1), systemd (>= 261.2-1), dbus (>= 1.16.2-1), glib (>= 2.88.3-1+toddy1), alsa-lib (= 1.2.16.1-1+toddy1)',
                 'pipewire-1.6.8.tar.bz2', 'usr/lib/pkgconfig/libpipewire-0.3.pc'),
    'alsa-lib': ('1.2.16.1', 'glibc (>= 2.44-1)',
                 'alsa-lib-1.2.16.1.tar.bz2', 'usr/lib/pkgconfig/alsa.pc'),
    'libinput': ('1.31.3', 'glibc (>= 2.44-1), systemd (>= 261.2-1), libevdev (= 1.13.6-1+toddy1), mtdev (= 1.1.7-1+toddy1)',
                  'libinput-1.31.3.tar.gz', 'usr/lib/pkgconfig/libinput.pc'),
    'libei': ('1.6.0', 'glibc (>= 2.44-1), systemd (>= 261.2-1), libevdev (= 1.13.6-1+toddy1), libxkbcommon (= 1.13.2-1+toddy1)',
               'libei-1.6.0.tar.bz2', 'usr/lib/pkgconfig/libei-1.0.pc'),
    'libxcvt': ('0.1.3', 'glibc (>= 2.44-1)',
                 'libxcvt-0.1.3.tar.xz', 'usr/lib/pkgconfig/libxcvt.pc'),
    'libevdev': ('1.13.6', 'glibc (>= 2.44-1)',
                  'libevdev-1.13.6.tar.xz', 'usr/lib/pkgconfig/libevdev.pc'),
    'mtdev': ('1.1.7', 'glibc (>= 2.44-1)',
               'mtdev-1.1.7.tar.bz2', 'usr/lib/pkgconfig/mtdev.pc'),
    'libdisplay-info': ('0.4.0', 'glibc (>= 2.44-1), hwdata (>= 0.410-1+toddy1)',
                        'libdisplay-info-0.4.0.tar.xz', 'usr/lib/pkgconfig/libdisplay-info.pc'),
    'bubblewrap': ('0.11.2', 'glibc (>= 2.44-1), libcap (>= 2.78-1)',
                   'bubblewrap-0.11.2.tar.xz', 'usr/bin/bwrap'),
    'hwdata': ('0.410', '', 'hwdata-0.410.tar.gz', 'usr/share/hwdata/pnp.ids'),
    'lcms2': ('2.19.1', 'glibc (>= 2.44-1), libjpeg-turbo (= 3.2.0-1+toddy1), tiff (= 4.7.2-1+toddy1)',
              'lcms2-2.19.1.tar.gz', 'usr/lib/pkgconfig/lcms2.pc'),
    'at-spi2-core': ('2.60.6', 'glib (>= 2.88.3-1+toddy1), dbus (>= 1.16.2-1), systemd (>= 261.2-1)',
                     'at-spi2-core-2.60.6.tar.xz', 'usr/lib/pkgconfig/atspi-2.pc'),
    'gi-dbus-types': ('1.86.0', 'gobject-introspection (>= 1.86.0-1+toddy1), dbus (>= 1.16.2-1)',
                      'gobject-introspection-1.86.0.tar.xz', 'usr/share/gir-1.0/DBus-1.0.gir'),
    'sassc': ('3.6.2', 'libsass (= 3.6.6-1+toddy1), glibc (>= 2.44-1), gcc (>= 16.2.0-1)',
              'sassc-3.6.2.tar.gz', 'usr/bin/sassc'),
    'libsass': ('3.6.6', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1)',
               'libsass-3.6.6.tar.gz', 'usr/lib/pkgconfig/libsass.pc'),
    'appstream': ('1.1.6', 'glib (>= 2.88.3-1+toddy1), curl (>= 8.23.0-1), libxml2 (= 2.15.3-1+toddy1), libfyaml (= 0.9.6-1+toddy1), libxmlb (= 0.3.29-1+toddy1), zstd (>= 1.5.7-1)',
                   'AppStream-1.1.6.tar.xz', 'usr/lib/pkgconfig/appstream.pc'),
    'libfyaml': ('0.9.6', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1)',
                 'libfyaml-0.9.6.tar.gz', 'usr/lib/pkgconfig/libfyaml.pc'),
    'libxmlb': ('0.3.29', 'glib (>= 2.88.3-1+toddy1), xz (>= 5.8.3-1), zstd (>= 1.5.7-1)',
                'libxmlb-0.3.29.tar.xz', 'usr/lib/pkgconfig/xmlb.pc'),
    'itstool': ('2.0.7', 'python (= 3.14.10-1+toddy2), libxml2-python (= 2.15.3-1+toddy1), gettext (>= 1.0-1)',
                'itstool-2.0.7.tar.gz', 'usr/bin/itstool'),
    'libxml2-python': ('2.15.3', 'libxml2 (= 2.15.3-1+toddy1), python (= 3.14.10-1+toddy2)',
                       'libxml2-2.15.3.tar.xz', 'usr/lib/python3.14/site-packages/libxml2.py'),
    'doxygen': ('1.18.0', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), sqlite (>= 3.53.4-1)',
                'doxygen-1.18.0.src.tar.gz', 'usr/bin/doxygen'),
    'gtk': ('4.22.4', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), pango (= 1.58.2-1+toddy1), cairo (>= 1.18.4-1+toddy1), harfbuzz (>= 14.3.1-1+toddy1), fribidi (>= 1.0.16-1+toddy1), fontconfig (>= 2.18.3-1+toddy1), gdk-pixbuf (= 2.44.7-1+toddy2), graphene (= 1.10.8-1+toddy1), libepoxy (= 1.5.10-1+toddy1), wayland (>= 1.26.0-1+toddy1), libxkbcommon (= 1.13.2-1+toddy1), libpng (>= 1.6.58-1+toddy1), libjpeg-turbo (= 3.2.0-1+toddy1), tiff (= 4.7.2-1+toddy1), librsvg (= 2.62.3-1+toddy1), iso-codes (= 4.20.1-1+toddy1)',
            'gtk-4.22.4.tar.xz', 'usr/lib/girepository-1.0/Gtk-4.0.typelib'),
    'iso-codes': ('4.20.1', 'glibc (>= 2.44-1)',
                  'iso-codes-v4.20.1.tar.gz', 'usr/share/iso-codes/json/iso_3166-1.json'),
    'tiff': ('4.7.2', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), libjpeg-turbo (= 3.2.0-1+toddy1), zlib (>= 1.3.2-1), xz (>= 5.8.3-1), zstd (>= 1.5.7-1)',
             'tiff-4.7.2.tar.gz', 'usr/lib/libtiff.so.6'),
    'gdk-pixbuf': ('2.44.7', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), libpng (>= 1.6.58-1+toddy1), libjpeg-turbo (= 3.2.0-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)',
                    'gdk-pixbuf-2.44.7.tar.xz', 'usr/lib/girepository-1.0/GdkPixbuf-2.0.typelib'),
    'libepoxy': ('1.5.10', 'glibc (>= 2.44-1), mesa (= 26.1.7-1+toddy1)',
                 'libepoxy-1.5.10.tar.xz', 'usr/lib/libepoxy.so.0'),
    'mesa': ('26.1.7', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), llvm-runtime (= 22.1.8-1+toddy1), libdrm (= 2.4.134-1+toddy1), wayland (>= 1.26.0-1+toddy1), systemd (>= 261.2-1), libelf (>= 0.195-1), expat (>= 2.10.0-1), zlib (>= 1.3.2-1), zstd (>= 1.5.7-1)',
             'mesa-26.1.7.tar.xz', 'usr/lib/libEGL.so.1'),
    'pyyaml': ('6.0.3', 'python (>= 3.14), python (<< 3.15)',
               'pyyaml-6.0.3.tar.gz', 'usr/lib/python3.14/site-packages/yaml/__init__.py'),
    'libpciaccess': ('0.19', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1)',
                     'libpciaccess-0.19.tar.xz', 'usr/lib/libpciaccess.so.0'),
    'libdrm': ('2.4.134', 'glibc (>= 2.44-1), libpciaccess (= 0.19-1+toddy1)',
                'libdrm-2.4.134.tar.xz', 'usr/lib/libdrm_intel.so.1'),
    'mako': ('1.4.1', 'python (>= 3.14), python (<< 3.15), markupsafe (>= 2.0)',
              'mako-1.4.1.tar.gz', 'usr/lib/python3.14/site-packages/mako/__init__.py'),
    'rustc': ('1.97.1', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), llvm-runtime (= 22.1.8-1+toddy1), curl (>= 8.23.0-1), openssl (>= 4.0.3-1), sqlite (>= 3.53.4-1), zlib (>= 1.3.2-1)',
               'rustc-1.97.1-src.tar.xz', 'usr/bin/rustc'),
    'dejavu-fonts': ('2.37', 'fontconfig (>= 2.18.3-1+toddy1)',
                     'dejavu-fonts-ttf-2.37.tar.bz2', 'usr/share/fonts/dejavu/DejaVuSerif.ttf'),
    'psutil': ('7.2.2', 'python (>= 3.14), python (<< 3.15), glibc (>= 2.44-1)',
               'psutil-7.2.2.tar.gz', 'usr/lib/python3.14/site-packages/psutil/__init__.py'),
    'libjpeg-turbo': ('3.2.0', 'glibc (>= 2.44-1)',
                      'libjpeg-turbo-3.2.0.tar.gz', 'usr/lib/libjpeg.so'),
    'adwaita-fonts': ('50.0', 'fontconfig (>= 2.18.3-1+toddy1)',
                      'adwaita-fonts-50.0.tar.xz', 'usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf'),
    'llvm': ('22.1.8', 'llvm-runtime (= 22.1.8-1+toddy1), glibc (>= 2.44-1), gcc (>= 16.2.0-1)',
             'llvm-project-22.1.8.src.tar.xz', 'usr/bin/llvm-config'),
    'shared-mime-info': ('2.5.1', 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), glib (>= 2.88.3-1+toddy1), libxml2 (>= 2.15.3-1+toddy1)',
                         'shared-mime-info-2.5.1.tar.gz', 'usr/share/mime/mime.cache'),
    'graphene': ('1.10.8', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1)',
                 'graphene-1.10.8.tar.xz', 'usr/lib/girepository-1.0/Graphene-1.0.typelib'),
    'pango': ('1.58.2', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), freetype (>= 2.14.3-1+toddy1), fontconfig (>= 2.18.3-1+toddy1), fribidi (>= 1.0.16-1+toddy1), harfbuzz (>= 14.3.1-1+toddy1), cairo (>= 1.18.4-1+toddy1), gi-desktop-types (>= 1.86.0-1+toddy1)',
              'pango-1.58.2.tar.xz', 'usr/lib/girepository-1.0/PangoCairo-1.0.typelib'),
    'gi-desktop-types': ('1.86.0', 'gobject-introspection (>= 1.86.0-1+toddy1), freetype (>= 2.14.3-1+toddy1), fontconfig (>= 2.18.3-1+toddy1), libxml2 (>= 2.15.3-1+toddy1), cairo (>= 1.18.4-1+toddy1)',
                        'gobject-introspection-1.86.0.tar.xz', 'usr/lib/girepository-1.0/freetype2-2.0.typelib'),
    'cairo': ('1.18.4', 'glibc (>= 2.44-1), pixman (>= 0.46.4-1+toddy1), libpng (>= 1.6.58-1+toddy1), freetype (>= 2.14.3-1+toddy1), fontconfig (>= 2.18.3-1+toddy1), glib (>= 2.88.3-1+toddy1), zlib (>= 1.3.2-1)',
              'cairo-1.18.4.tar.xz', 'usr/lib/pkgconfig/cairo-gobject.pc'),
    'harfbuzz': ('14.3.1', 'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), freetype (>= 2.14.3-1+toddy1), zlib (>= 1.3.2-1)',
                 'harfbuzz-14.3.1.tar.xz', 'usr/lib/girepository-1.0/HarfBuzz-0.0.typelib'),
    'fribidi': ('1.0.16', 'glibc (>= 2.44-1)',
                'fribidi-1.0.16.tar.xz', 'usr/lib/pkgconfig/fribidi.pc'),
    'fontconfig': ('2.18.3', 'glibc (>= 2.44-1), freetype (>= 2.14.3-1+toddy1), libxml2 (>= 2.15.3-1+toddy1)',
                   'fontconfig-2.18.3.tar.xz', 'usr/lib/pkgconfig/fontconfig.pc'),
    'freetype': ('2.14.3', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1), bzip2 (>= 1.0.8-1), libpng (>= 1.6.58-1+toddy1)',
                 'freetype-2.14.3.tar.xz', 'usr/lib/pkgconfig/freetype2.pc'),
    'libpng': ('1.6.58', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1)',
               'libpng-1.6.58.tar.xz', 'usr/lib/pkgconfig/libpng16.pc'),
    'pixman': ('0.46.4', 'glibc (>= 2.44-1)',
               'pixman-0.46.4.tar.gz', 'usr/lib/pkgconfig/pixman-1.pc'),
    'wayland': ('1.26.0', 'glibc (>= 2.44-1), libffi (>= 3.8.0-1), libxml2 (>= 2.15.3-1+toddy1)',
                'wayland-1.26.0.tar.xz', 'usr/lib/libwayland-client.so.0'),
    'wayland-protocols': ('1.49', 'wayland (>= 1.26.0-1+toddy1)',
                          'wayland-protocols-1.49.tar.xz', 'usr/share/pkgconfig/wayland-protocols.pc'),
    'libxml2': ('2.15.3', 'glibc (>= 2.44-1), zlib (>= 1.3.2-1)',
               'libxml2-2.15.3.tar.xz', 'usr/lib/pkgconfig/libxml-2.0.pc'),
    'qtsvg': ('6.11.2', 'qtbase (>= 6.11.2-1+toddy1)',
              'qtsvg-everywhere-src-6.11.2.tar.xz', 'usr/lib/libQt6Svg.so.6.11.2'),
    'qttools-linguist': ('6.11.2', 'qtbase (>= 6.11.2-1+toddy1)',
                        'qttools-everywhere-src-6.11.2.tar.xz', 'usr/bin/lrelease'),
    'extra-cmake-modules': ('6.29.0', 'cmake (>= 4.4.2-1)',
                          'extra-cmake-modules-6.29.0.tar.xz', 'usr/share/ECM/cmake/ECMConfig.cmake'),
    'kcoreaddons': ('6.29.0', 'qtbase (>= 6.11.2-1+toddy1), util-linux (>= 2.42.4-1), systemd (>= 261.2-1)',
                   'kcoreaddons-6.29.0.tar.xz', 'usr/lib/libKF6CoreAddons.so.6.29.0'),
    'yaml-cpp': ('0.9.0', 'gcc (>= 16.2.0-1), glibc (>= 2.44-1)',
                 'yaml-cpp-yaml-cpp-0.9.0.tar.gz', 'usr/lib/libyaml-cpp.so.0.9.0'),
}

if __name__ == '__main__':
    name, = sys.argv[1:]
    version, depends, archive, required = PROFILES[name]
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    from dependency_preflight import native as verify_native_dependencies
    verify_native_dependencies(depends)
    log = Path('/var/log/toddy/phase2')
    llvm_resume=name=='llvm' and (log/'llvm-qualify-resume-3.job.json').exists()
    llvm_recovery=name=='llvm' and (log/'llvm-qualify-recovery-4.job.json').exists()
    rust_legacy=name=='rustc' and (log/'rustc-tools-finish-8.job.json').exists()
    mako_resume=name=='mako' and (log/'mako-resume-2.job.json').exists()
    qualifier=('rustc-tools-finish-8' if rust_legacy else 'rustc-stage-4') if name=='rustc' else 'mako-resume-2' if mako_resume else 'pango-stage-6' if name=='pango' else 'llvm-qualify-recovery-4' if llvm_recovery else 'llvm-qualify-resume-3' if llvm_resume else 'llvm-qualify-2' if name=='llvm' else 'wayland-recheck-2' if name=='wayland' else 'harfbuzz-resume-2' if name=='harfbuzz' else name+'-1'
    mesa_resume=name=='mesa' and (log/'mesa-resume-2.job.json').exists()
    if mesa_resume:qualifier='mesa-resume-2'
    mesa_finish=name=='mesa' and (log/'mesa-finish-3.job.json').exists()
    if mesa_finish:qualifier='mesa-finish-3'
    pci_resume=name=='libpciaccess' and (log/'libpciaccess-resume-2.job.json').exists()
    if pci_resume:qualifier='libpciaccess-resume-2'
    doxygen_finish=name=='doxygen' and (log/'doxygen-finish-2.job.json').exists()
    if doxygen_finish:qualifier='doxygen-finish-2'
    if name=='libsass' and (log/'libsass-qualify-2.job.json').exists():qualifier='libsass-qualify-2'
    if name=='appstream' and (log/'appstream-probe-4.job.json').exists():qualifier='appstream-probe-4'
    if name=='libfyaml' and (log/'libfyaml-finish-2.job.json').exists():qualifier='libfyaml-finish-2'
    if name=='colord-gtk' and (log/'colord-gtk-collect-3.job.json').exists():qualifier='colord-gtk-collect-3'
    if name=='libgtop' and (log/'libgtop-mode-3.job.json').exists():qualifier='libgtop-mode-3'
    if name=='mitkrb':qualifier='mitkrb-metadata-4'
    if name=='cups':qualifier='cups-layout-finish-2'
    if name=='itstool' and (log/'itstool-recovery-2.job.json').exists():qualifier='itstool-recovery-2'
    if name=='itstool' and (log/'itstool-dtd-finish-3.job.json').exists():qualifier='itstool-dtd-finish-3'
    if name=='at-spi2-core' and (log/'atspi-finish-4.job.json').exists():qualifier='atspi-finish-4'
    if name=='bubblewrap':qualifier='bubblewrap-stage-6'
    if name=='colord':qualifier='colord-finish-3'
    if name=='libgusb':qualifier='libgusb-probe-3'
    if name=='pulseaudio':qualifier='pulseaudio-probe-2'
    if name=='libsndfile':qualifier='libsndfile-qualify-2'
    if name=='libvorbis':qualifier='libvorbis-probe-2'
    if name=='libei':qualifier='libei-dtd-2'
    if name=='libinput':qualifier='libinput-probe-2'
    if name=='alsa-lib':qualifier='alsa-lib-probe-2'
    if name=='lua':qualifier='lua-probe-3'
    if name=='wireplumber':qualifier='wireplumber-pot-3'
    if name=='gnome-desktop':qualifier='gnome-desktop-finish-3'
    if name=='libadwaita':qualifier='libadwaita-build-2'
    if name=='gtksourceview':qualifier='gtksourceview-patched-verify-9'
    if name=='mozjs':qualifier='mozjs-signal-check-4'
    if name=='json-c' and (log/'json-c-finish-3.exit').exists():qualifier='json-c-finish-3'
    if name=='polkit':qualifier='polkit-full-1'
    if name=='gcr3':qualifier='gcr3-patched-2'
    if name=='gnome-keyring':qualifier='gnome-keyring-backend-4'
    if name=='libical':qualifier='libical-finish-2'
    if name=='libpsl':qualifier='libpsl-metadata-2'
    if name=='nettle':qualifier='nettle-consumer-2'
    if name=='gnutls':qualifier='gnutls-stage-5'
    if name=='glib-networking':qualifier='glib-networking-consumer-3'
    if name=='evolution-data-server':qualifier='evolution-data-server-private-4'
    if name=='ibus':qualifier='ibus-machine-5'
    if name=='libgweather':qualifier='libgweather-stage-2'
    if name=='libnma':qualifier='libnma-stage-2'
    if name=='gnome-shell' and (log/'gnome-shell-probe-2.exit').exists():qualifier='gnome-shell-probe-2'
    if name=='gexiv2' and (log/'gexiv2-probe-2.exit').exists():qualifier='gexiv2-probe-2'
    if name=='exiv2':qualifier='exiv2-probe-7'
    if name=='inih' and (log/'inih-collect-2.exit').exists():qualifier='inih-collect-2'
    if name=='blueprint-compiler':qualifier='blueprint-compiler-finish-2'
    if name=='aspell' and (log/'aspell-dictionary-2.exit').exists():qualifier='aspell-dictionary-2'
    if name=='gnome-text-editor':qualifier='gnome-text-editor-metadata-2'
    if name=='libspelling':qualifier='libspelling-options-2'
    if name=='gnome-online-accounts':qualifier='gnome-online-accounts-collect-2'
    if name=='tecla':qualifier='tecla-collect-2'
    if name=='enchant':qualifier='enchant-provider-explicit-5'
    if name=='tinysparql':qualifier='tinysparql-numeric-5'
    if name=='gnome-autoar' and (log/'gnome-autoar-probe-3.exit').exists():qualifier='gnome-autoar-probe-3'
    if name=='gnome-terminal' and (log/'gnome-terminal-probe-3.exit').exists():qualifier='gnome-terminal-probe-3'
    if name=='libhandy' and (log/'libhandy-gi-3.exit').exists():qualifier='libhandy-gi-3'
    if name=='vte' and (log/'vte-probe-3.exit').exists():qualifier='vte-probe-3'
    if name=='vala':qualifier='vala-consumer-2'
    if name=='libunistring':qualifier='libunistring-consumer-2'
    if name=='gcr':qualifier='gcr-finish-4'
    if name=='upower':qualifier='upower-consumer-4'
    if name=='accountsservice':qualifier='accountsservice-locale-5'
    if name=='dconf':qualifier='dconf-gsettings-4'
    if name=='python-dbusmock':qualifier='python-dbusmock-2'
    if name=='linux-pam':qualifier='pam-1'
    if name=='dbus-python' and (log/'dbus-python-verify-2.exit').exists():qualifier='dbus-python-verify-2'
    if name=='libxml2-python':qualifier='libxml2-python-probe-5'
    assert (log / (qualifier+'.exit')).read_text().strip() == '0', 'Reconcile actual compiler/test exit first'
    if name=='rustc':
        work=Path('/mnt/lfs/sources/phase2/work/rustc-1')
        assert (log/'rustc-1.exit').read_text().strip()=='0'
        assert (log/'rustc-compiler-3.exit').read_text().strip()=='0'
        std_exit=(log/'rustc-std-2.exit').read_text().strip()
        if std_exit=='1':
            assert 'stage2/bin/clippy-driver' in (log/'rustc-std-2.log').read_text()
        else:
            assert std_exit=='0'
            assert (work/'std-tests-2-native.exit').read_text().strip()=='0'
        summaries=qualify_preserved_log((work/'std-tests-2.log').read_text())
        assert sum(r['passed'] for r in summaries)==6223
        assert sum(r['ignored'] for r in summaries)==5
        compiler=json.loads((work/'compiler-tests-3/results.json').read_text())
        assert compiler['native_exit']==0
        assert compiler['summaries']==[['ok','1552','0','7','0','19666']]
        assert (work/'compiler-tests-3/native.exit').read_text().strip()=='0'
        assert hashlib.sha256((work/'compiler-tests-3/native.log').read_bytes()).hexdigest()==compiler['log_sha256']
        assert json.loads((log/'rustc-compiler-3.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/rust_compiler_tests.py').read_text()
        canonical_probe=(ROOT/'scripts/build/phase2/rust_tools_probe.py').read_text()
        stage_job=json.loads((log/'rustc-stage-4.job.json').read_text())
        if rust_legacy:
            for job in ['rustc-stage-4','rustc-tools-recovery-5','rustc-tools-recovery-6','rustc-tools-recovery-7']:
                assert (log/(job+'.exit')).read_text().strip()=='1'
            assert hashlib.sha256(stage_job['command'][-3].encode()).hexdigest()=='b081cf6b85698b41a927d587fbf5593e359c565c38bf30e00689e5e5c6d1c1c4'
            proof=json.loads((work/'tool-docs-8/qualified.json').read_text())
            assert proof['qualification_exit']==0 and proof['rustdoc_native_exit']==0
            assert proof['stage_unchanged_by_probe']
            assert proof['original_wrapper_exits']=={'stage4':1,'guard5':1,'probe6':1,'collector7':1}
            record=json.loads((log/'rustc-tools-finish-8.job.json').read_text())
            assert record['command'][-3]==(ROOT/'scripts/build/phase2/rust_finish_tools.py').read_text()
            assert record['command'][-2]==canonical_probe
            assert record['command'][-1]==canonical_probe.replace("101, 'clippy::eq-op'", "101, 'clippy::eq_op'")
            assert json.loads((log/'rustc-tools-recovery-7.job.json').read_text())['command'][-2]==record['command'][-1]
            assert hashlib.sha256((work/'stage-tests-recovery-7/tools.log').read_bytes()).hexdigest()==proof['previous_tools_log_sha256']
            expected={'c-ffi-compile':0,'c-ffi-archive':0,'rustfmt-reject':1,'rustfmt-format':0,
                      'rustfmt-check':0,'cargo-test':0,'cargo-clippy':0,'clippy-reject':101,'rustdoc':0}
            assert {r['name'] for r in proof['checks']}==set(expected) and len(proof['checks'])==9
            for row in proof['checks']:
                name_=row['name']
                directory=work/('tool-docs-8' if name_=='rustdoc' else 'tool-consumers-7')
                assert hashlib.sha256((directory/(name_+'.log')).read_bytes()).hexdigest()==row['log_sha256']
                assert row.get('native_exit',row.get('expected_exit'))==expected[name_]
            assert (work/'tool-docs-8/rustdoc.exit').read_text().strip()=='0'
        else:
            proof=json.loads((work/'stage-tests-4/results.json').read_text())
            assert proof['install_exit']==0 and proof['tools_exit']==0
            assert stage_job['command'][-3]==(ROOT/'scripts/build/phase2/rust_stage.py').read_text()
            assert stage_job['command'][-2]==canonical_probe
            assert (work/'stage-tests-4/tools.exit').read_text().strip()=='0'
            assert hashlib.sha256((work/'stage-tests-4/tools.log').read_bytes()).hexdigest()==proof['tools_log_sha256']
        assert proof['probe_sha256']==hashlib.sha256(canonical_probe.encode()).hexdigest()
        assert (work/'stage-tests-4/install.exit').read_text().strip()=='0'
        assert hashlib.sha256((work/'stage-tests-4/install.log').read_bytes()).hexdigest()==proof['install_log_sha256']
        actual={str(p.relative_to(work/'stage')) for p in (work/'stage').rglob('*')
                if p.is_file() or p.is_symlink()}
        assert actual==set(proof['entries']), 'Unexpected stage payload'
        for relative,row in proof['entries'].items():
            path=work/'stage'/relative
            assert path.is_relative_to(work/'stage') and '..' not in Path(relative).parts
            if 'symlink' in row:assert path.is_symlink() and path.readlink().as_posix()==row['symlink']
            else:assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    if name in ('libpciaccess','libdrm'):
        work=Path('/mnt/lfs/sources/phase2/work')/(name+'-1')
        input_=Path('/mnt/lfs/sources/phase2/inputs')/(name+'-'+version)
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2'/(name+'-build.sh')).read_bytes()
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2'/(name+'-probe.c')).read_bytes()
        assert json.loads((log/(name+'-1.job.json')).read_text())['command'][-1]=='/src/toddy-build.sh'
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==0
        if name=='libdrm':
            assert proof['registered_upstream_tests']>3
            assert proof['log_sha256']==hashlib.sha256((work/'compile/meson-logs/testlog.json').read_bytes()).hexdigest()
            assert all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in proof['tests'])
        else:
            assert proof['registered_upstream_tests']==0
            if pci_resume:
                assert (log/'libpciaccess-1.exit').read_text().strip()=='1'
                assert 'toddy-probe.c: No such file or directory' in (log/'libpciaccess-1.log').read_text()
                assert json.loads((log/'libpciaccess-resume-2.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/libpciaccess-resume.sh').read_text()
                assert proof['stage_regular_files_unchanged']>0

    if name=='mesa':
        input_=Path('/mnt/lfs/sources/phase2/inputs/mesa-26.1.7')
        work=Path('/mnt/lfs/sources/phase2/work/mesa-1')
        canonical=(ROOT/'scripts/build/phase2/mesa-build.sh').read_text()
        if mesa_resume:
            assert (log/'mesa-1.exit').read_text().strip()=='1'
            assert hashlib.sha256((input_/'toddy-build.sh').read_bytes()).hexdigest()=='40f33d0c1b92b6e3f6107069f094a5632f2e19d1f5b631d291d272382f864744'
            added='# These registered test dependencies are explicitly build_by_default:false.\nninja -C /build/compile -j4 src/compiler/glsl/glcpp/glcpp src/compiler/glsl/glsl_compiler\n'
            assert canonical.count(added)==1 and canonical.count(' -Wl,-rpath-link,/stage/usr/lib')==1
            assert canonical.replace(added,'').replace(' -Wl,-rpath-link,/stage/usr/lib','')==(input_/'toddy-build.sh').read_text()
            recovery_job=json.loads((log/'mesa-resume-2.job.json').read_text())
            assert recovery_job['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/mesa_resume.py').read_text()]
            assert recovery_job['harness_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
        else:
            assert (input_/'toddy-build.sh').read_text()==canonical
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/mesa-probe.c').read_bytes()
        job=json.loads((log/'mesa-1.job.json').read_text())
        assert job['command'][-1]=='/src/toddy-build.sh'
        assert job['harness_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['consumer_exit']==0 and proof['registered_tests']>10
        assert all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in proof['tests'])
        path=work/'compile/meson-logs/testlog.json'
        assert proof['upstream_log_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        if mesa_resume:
            assert len(rows)==48 and sum(r['result']=='OK' and r['returncode']==0 for r in rows)==43
            failed=[r for r in rows if r['result']!='OK']
            assert len(failed)==5 and all(r['returncode']==1 and 'FileNotFoundError' in r['stderr'] for r in failed)
            corrected_path=work/'compile/meson-logs/testlog-recovery-2.json'
            corrected=[json.loads(line) for line in corrected_path.read_text().splitlines()]
            assert len(corrected)==5 and all(r['result']=='OK' and r['returncode']==0 for r in corrected)
            assert {r['name'] for r in failed}=={r['name'] for r in corrected}
            assert proof['affected_recheck']['log_sha256']==hashlib.sha256(corrected_path.read_bytes()).hexdigest()
            merged={r['name']:{k:r[k] for k in ['name','result','returncode']} for r in rows}
            for r in corrected:merged[r['name']]={k:r[k] for k in ['name','result','returncode']}
            assert list(merged.values())==proof['tests'] and proof['original_wrapper_exit']==1
            for label in ['missing-test-tools','affected-tests','first-stage']:
                assert (work/'mesa-recovery-2'/(label+'.exit')).read_text().strip()=='0'
            if mesa_finish:
                assert (log/'mesa-resume-2.exit').read_text().strip()=='1'
                assert (work/'mesa-recovery-2/consumer-compile.exit').read_text().strip()=='1'
                final_job=json.loads((log/'mesa-finish-3.job.json').read_text())
                assert final_job['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/mesa_finish.py').read_text()]
                assert final_job['harness_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
                for label in ['consumer-compile','render']:
                    assert (work/'mesa-finish-3'/(label+'.exit')).read_text().strip()=='0'
                assert proof['stage_unchanged_by_consumer'] and proof['consumer_runtime_rpath'] is False
                from xorg_sdk_build import entries as stage_entries
                assert stage_entries(work/'stage')==proof['stages']
            else:
                for label in ['consumer-compile','render']:
                    assert (work/'mesa-recovery-2'/(label+'.exit')).read_text().strip()=='0'
        else:
            assert [{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows]==proof['tests']
        assert proof['native_render_sha256']==hashlib.sha256((work/'native-render.log').read_bytes()).hexdigest()
        assert 'renderer: llvmpipe' in proof['native_render_stdout']
        binaries=json.loads((work/'compiled-binaries.json').read_text())
        assert len(binaries)==proof['unchanged_compiled_elfs']
        for relative,sha in binaries.items():
            path=work/relative
            assert path.resolve().is_relative_to(work) and not path.is_symlink()
            with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
    if name=='gdk-pixbuf':
        input_=Path('/mnt/lfs/sources/phase2/inputs/gdk-pixbuf-2.44.7')
        work=Path('/mnt/lfs/sources/phase2/work/gdk-pixbuf-1')
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/gdk-pixbuf-build.sh').read_bytes()
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/gdk-pixbuf-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==0 and proof['registered_tests']>10
        assert proof['upstream_log_sha256']==hashlib.sha256((work/'compile/meson-logs/testlog.json').read_bytes()).hexdigest()
        assert all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in proof['tests'])
        cache=work/'stage'/proof['generated_cache']['path']
        assert cache.resolve().is_relative_to(work/'stage') and not cache.is_symlink()
        assert hashlib.sha256(cache.read_bytes()).hexdigest()==proof['generated_cache']['sha256']
        assert proof['generated_cache']['external_module_records']==0
    if name=='libepoxy':
        input_=Path('/mnt/lfs/sources/phase2/inputs/libepoxy-1.5.10')
        work=Path('/mnt/lfs/sources/phase2/work/libepoxy-1')
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libepoxy-build.sh').read_bytes()
        assert (input_/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libepoxy-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==0 and proof['registered_tests']==4
        assert proof['upstream_log_sha256']==hashlib.sha256((work/'compile/meson-logs/testlog.json').read_bytes()).hexdigest()
        assert all(r['result']=='OK' and r['returncode']==0 for r in proof['tests'])
        assert 'renderer: llvmpipe' in proof['native_render_stdout']
    if name=='pyyaml':
        input_=Path('/mnt/lfs/sources/phase2/inputs/pyyaml-6.0.3')
        work=Path('/mnt/lfs/sources/phase2/work/pyyaml-1')
        assert (input_/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/pyyaml-build.sh').read_bytes()
        assert (input_/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/pyyaml-probe.py').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['native_exit']==0 and proof['upstream_boolean_result'] and proof['pure_python_upstream_cases']>1000
        assert proof['upstream_log_sha256']==hashlib.sha256((work/'upstream-tests.log').read_bytes()).hexdigest()
        assert proof['staged_consumer']['uid']==101 and proof['staged_consumer']['version']=='6.0.3'
        assert proof['staged_consumer']['safe_unicode_roundtrip'] and proof['staged_consumer']['unsafe_constructor_rejected']
    if name=='psutil':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/psutil-1/consumer.json').read_text())
        assert proof['version']=='7.2.2' and proof['uid']==101
        assert proof['own_process_memory_cpu'] and proof['timeout_then_terminate_exit']==-15
        assert proof['recursive_child_kill_and_reap']
    if name=='mako':
        source=Path('/mnt/lfs/sources/phase2/inputs/mako-1.4.1')
        work=Path('/mnt/lfs/sources/phase2/work/mako-1')
        proof=json.loads((work/'consumer.json').read_text())
        assert proof['version']=='1.4.1' and proof['uid']==101 and proof['c_consumer_exit']==0
        assert proof['checks']==['unicode-expression','html-escape','loop','lookup-inheritance-cache',
                                 'invalid-syntax-rejected','generated-c-compile-execute']
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/mako-build.sh').read_bytes()
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/mako-probe.py').read_bytes()
        assert json.loads((log/'mako-1.job.json').read_text())['command'][-1]=='/src/toddy-build.sh'
        if mako_resume:
            assert (log/'mako-1.exit').read_text().strip()=='1'
            assert 'Permission denied' in (log/'mako-1.log').read_text()
            assert json.loads((log/'mako-resume-2.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/mako-resume.sh').read_text()
        receipt=json.loads((source/'toddy-prepared.json').read_text())
        assert receipt['source_patches']==[{'path':'doc/build/changelog.rst','before_mode':0o600,'after_mode':0o644,
                'content_sha256':'a5620499d6c083972b0ba7ea307b99b06e783966fa46b3e5c73d00fe96f51e31',
                'reason':'Public release doc is owner-readable only; expose unchanged bytes to unprivileged read-only-input compiler'}]
    if name=='libjpeg-turbo':
        import xml.etree.ElementTree as ET
        work=Path('/mnt/lfs/sources/phase2/work/libjpeg-turbo-1')
        report=ET.fromstring((work/'ctest.xml').read_bytes())
        assert report.tag=='testsuite' and int(report.get('tests'))>0
        assert all(int(report.get(k,'0'))==0 for k in ['failures','errors','disabled','skipped'])
        cases=report.findall('testcase');assert len(cases)==int(report.get('tests'))
        assert all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases)
        source=Path('/mnt/lfs/sources/phase2/inputs/libjpeg-turbo-3.2.0')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libjpeg-turbo-build.sh').read_bytes()
    if name=='pango':
        assert (log/'pango-1.exit').read_text().strip()=='1'
        assert (log/'pango-metric-oracle-5.exit').read_text().strip()=='0'
        assert json.loads((log/'pango-metric-oracle-5.job.json').read_text())['command'][-2:]==[(ROOT/'scripts/build/phase2/pango_metric_fixture.py').read_text(),'qualify']
        assert json.loads((log/'pango-stage-6.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/pango-stage.sh').read_text()
        work=Path('/mnt/lfs/sources/phase2/work/pango-1')
        proof=json.loads((work/'portable-qualified.json').read_text())
        assert proof['original_binaries_unchanged'] and (proof['core_passed'],proof['curated_passed'],proof['empty_drivers'],proof['portable_metric_cases_passed'])==(9,17,2,3)
        for relative,sha in proof['proofs'].items():
            assert (work/relative).resolve().is_relative_to(work.resolve())
            assert hashlib.sha256((work/relative).read_bytes()).hexdigest()==sha
        for path,sha in proof['binaries'].items():
            assert path.startswith('/build/')
            assert hashlib.sha256((work/path.removeprefix('/build/')).read_bytes()).hexdigest()==sha
    if name=='adwaita-fonts':
        work=Path('/mnt/lfs/sources/phase2/work/adwaita-fonts-1')
        proof=json.loads((work/'font-inputs.json').read_text())
        assert proof['source_fonts_byte_identical'] and len(proof['fonts'])==6
        assert json.loads((log/'adwaita-fonts-1.job.json').read_text())['command'][-1]=='/src/toddy-build.sh'
        for row in proof['fonts']:
            path=work/'stage/usr/share/fonts/Adwaita'/row['file']
            assert path.parent==work/'stage/usr/share/fonts/Adwaita'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    if name=='dejavu-fonts':
        work=Path('/mnt/lfs/sources/phase2/work/dejavu-fonts-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/dejavu-fonts-ttf-2.37')
        proof=json.loads((work/'font-inputs.json').read_text())
        expected={'DejaVuSerif.ttf','DejaVuSerif-Bold.ttf',
                  'DejaVuSerif-Italic.ttf','DejaVuSerif-BoldItalic.ttf'}
        assert proof['source_fonts_byte_identical']
        assert {r['file'] for r in proof['fonts']}==expected and len(proof['fonts'])==4
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/dejavu-fonts-build.sh').read_bytes()
        assert json.loads((log/'dejavu-fonts-1.job.json').read_text())['command'][-1]=='/src/toddy-build.sh'
        for row in proof['fonts']:
            path=work/'stage/usr/share/fonts/dejavu'/row['file']
            assert path.parent==work/'stage/usr/share/fonts/dejavu'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
            assert path.read_bytes()==(source/'ttf'/row['file']).read_bytes()
    if name=='llvm':
        assert (log/'llvm-1.exit').read_text().strip()=='0'
        if llvm_resume or llvm_recovery:assert (log/'llvm-qualify-2.exit').read_text().strip()=='1'
        if llvm_recovery:assert (log/'llvm-qualify-resume-3.exit').read_text().strip()=='1'
        recipe='llvm_recover.py' if llvm_recovery else 'llvm-resume.sh' if llvm_resume else 'llvm-qualify.sh'
        assert json.loads((log/(qualifier+'.job.json')).read_text())['command'][-1]==(ROOT/'scripts/build/phase2'/recipe).read_text()
        work=Path('/mnt/lfs/sources/phase2/work/llvm-1')
        directory=work/('critical-tests-recovery-4' if llvm_recovery else 'critical-tests-resume' if llvm_resume else 'critical-tests')
        proof=json.loads((directory/'qualified.json').read_text())
        required_suites={'llvm-unit','clang-unit','llvm-transforms','llvm-x86','llvm-execution-engine','clang-codegen','clang-codegen-cxx'}
        assert {r['name'] for r in proof['suites']}==required_suites and len(proof['suites'])==7
        assert proof['required_poison_select_regression']=='PASS'
        if llvm_recovery:
            assert proof['binaries_unchanged'] and proof['unit_recovery']['cwd']=='/build/compile'
            original=work/'critical-tests-resume/llvm-unit.json';corrected=directory/'llvm-unit-support.json'
            recovery=proof['unit_recovery']
            assert hashlib.sha256(original.read_bytes()).hexdigest()==recovery['original_report_sha256']
            assert hashlib.sha256(corrected.read_bytes()).hexdigest()==recovery['affected_report_sha256']
            merged=merge_support_results(json.loads(original.read_text())['tests'],json.loads(corrected.read_text())['tests'])
            derived=json.loads((directory/'llvm-unit.json').read_text())
            assert derived['tests']==merged and derived['qualification']==recovery
            for path,sha in proof['binary_inputs'].items():
                assert path.startswith('/build/compile/')
                actual=work/path.removeprefix('/build/')
                assert actual.resolve().is_relative_to((work/'compile').resolve())
                assert hashlib.sha256(actual.read_bytes()).hexdigest()==sha
        for row in proof['suites']:
            report=directory/(row['name']+'.json');raw=report.read_bytes()
            assert hashlib.sha256(raw).hexdigest()==row['report_sha256']
            tests=json.loads(raw)['tests'];counts=dict(collections.Counter(t['code'] for t in tests))
            if llvm_recovery and row['name']=='llvm-unit':
                assert row['qualification_exit']==0 and row['original_native_exit']==1 and row['affected_native_exit']==0
            else:assert row['exit']==0
            assert tests and counts==row['counts'] and counts.get('PASS',0)>0
            assert set(counts)<={'PASS','XFAIL','UNSUPPORTED'}
    if name=='harfbuzz':
        assert (log/'harfbuzz-1.exit').read_text().strip()=='1'
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/harfbuzz-1/dependency-recovery/qualified.json').read_text())
        assert proof['original_core_libraries_unchanged'] and proof['before']==proof['after']
        assert json.loads((log/'harfbuzz-resume-2.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/harfbuzz-resume.sh').read_text()
    if name=='wayland':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/wayland-1/qualified-tests.json').read_text())
        assert proof['total']==26 and proof['original_passed']==6 and proof['corrected_passed']==20 and proof['compiled_binaries_unchanged']
        command=json.loads((log/'wayland-recheck-2.job.json').read_text())['command']
        assert command[-1]==(ROOT/'scripts/build/phase2/wayland-recheck.sh').read_text()
    if name in ('wayland-protocols','pixman','fontconfig','fribidi','harfbuzz','graphene','shared-mime-info'):
        rows=[json.loads(line) for line in (Path('/mnt/lfs/sources/phase2/work')/(name+'-1')/'compile/meson-logs/testlog.json').read_text().splitlines()]
        if name=='harfbuzz':
            # Frozen BLFS optional FontTools is absent; upstream explicitly skips
            # only these Python-oracle repack drivers, not native API regressions.
            optional={'subset+repack - harfbuzz:'+n for n in ['basic','prioritization','table_duplication','isolation','advanced_prioritization','space_splitting','duplicate_before_mutation']}
            skipped={r['name'] for r in rows if r['result']=='SKIP'}
            assert skipped==optional
            assert len(rows)==218 and sum(r['result']=='OK' for r in rows)==211
            assert all(r['returncode']==0 and not r['is_fail'] and (r['result']=='OK' or (r['name'] in optional and r['result']=='SKIP' and r.get('stdout','').strip()=='# fonttools is not present, skipping test.')) for r in rows)
        else:
            assert rows and all(r['result']=='OK' and r['returncode']==0 and not r['is_fail'] for r in rows)
    if name=='bubblewrap':
        import re
        work=Path('/mnt/lfs/sources/phase2/work/bubblewrap-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/bubblewrap-0.11.2')
        command=json.loads((log/'bubblewrap-stage-6.job.json').read_text())['command']
        assert command[-4:-1]==['python3','-c',(ROOT/'scripts/build/phase2/bubblewrap_stage.py').read_text()]
        qualification=json.loads(command[-1]);proof=json.loads((work/'test-results.json').read_text())
        assert proof['qualification']==qualification and proof['native_namespace_consumer_exit']==0
        assert qualification['consumer_source_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/bubblewrap-probe.py').read_bytes()).hexdigest()
        legacy=hashlib.sha256((source/'toddy-build.sh').read_bytes()).hexdigest()=='6d1847751b1e523579165990c3856c186f8ac745312e8eb8160c6ab877b94f4a'
        if legacy:
            assert hashlib.sha256((source/'toddy-probe.py').read_bytes()).hexdigest()=='b38d6b8f475fa8da5d5c5934e7539144b3973047007ea08ce3bc66058c3c94db'
        else:
            assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/bubblewrap-build.sh').read_bytes()
            assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/bubblewrap-probe.py').read_bytes()
        main_file=qualification.get('native_report_file','bubblewrap-native-runtime-3.json')
        assert re.fullmatch(r'bubblewrap-native-runtime-[0-9]+[.]json',main_file)
        native=json.loads((log/main_file).read_text())
        assert hashlib.sha256(json.dumps(native,sort_keys=True).encode()).hexdigest()==qualification['native_report_sha256']
        assert native['kernel']==qualification['kernel']=='7.1.8-toddy'
        assert native['binary_sha256']==qualification['binary_sha256']
        assert len(native['runs'])>=2 and all(r['exit']==0 for r in native['runs'])
        runs={r['name']:r for r in native['runs']}
        if native.get('reused_native_proof') is not None:
            reused_file=qualification.get('reused_report_file','bubblewrap-native-runtime-2.json')
            assert re.fullmatch(r'bubblewrap-native-runtime-[0-9]+[.]json',reused_file)
            old=json.loads((log/reused_file).read_text())
            assert hashlib.sha256(json.dumps(old,sort_keys=True).encode()).hexdigest()==qualification['reused_report_sha256']==native['reused_native_proof']['report_sha256']
            assert old['kernel']==native['kernel'] and old['binary_sha256']==native['binary_sha256']
            for row in native['reused_native_proof']['runs']:
                original=next(r for r in old['runs'] if r['name']==row['name'])
                assert row['exit']==original['exit']==0
                assert row['name'] not in runs;runs[row['name']]=original
        assert {'namespace-consumer','test-run.sh','test-specifying-pidns.sh','test-specifying-userns.sh'}<=set(runs)
        tests=runs['test-run.sh']['stdout']
        assert len(re.findall(r'^ok\b',tests,re.M))==69 and '1..69' in tests
        assert len(re.findall(r'^ok[^\n]*# SKIP',tests,re.M))==5 and not re.search(r'^not ok',tests,re.M)
        for driver_name in ['test-specifying-pidns.sh','test-specifying-userns.sh']:
            assert '1..1' in runs[driver_name]['stdout'] and len(re.findall(r'^ok\b',runs[driver_name]['stdout'],re.M))==1 and not re.search(r'^not ok',runs[driver_name]['stdout'],re.M)
        assert hashlib.sha256((work/'stage/usr/bin/bwrap').read_bytes()).hexdigest()==qualification['binary_sha256']
        assert (work/'stage/usr/bin/bwrap').stat().st_mode & 0o6000==0
        for relative,digest in json.loads((work/'stage-6/binaries-before.json').read_text()).items():
            with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    if name=='libdisplay-info':
        work=Path('/mnt/lfs/sources/phase2/work/libdisplay-info-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/libdisplay-info-0.4.0')
        for local,canonical in [('toddy-build.sh','libdisplay-info-build.sh'),('toddy-probe.c','libdisplay-info-probe.c')]:
            assert (source/local).read_bytes()==(ROOT/'scripts/build/phase2'/canonical).read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        registered=json.loads((work/'compile/meson-info/intro-tests.json').read_text())
        rows=[json.loads(x) for x in (work/'compile/meson-logs/testlog.json').read_text().splitlines()]
        assert len(rows)==len(registered)>0 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
        assert proof['staged_consumer_exit']==0 and proof['invalid_header_and_truncated_input_refused']
        assert proof['qemu_pnp_make']=='Red Hat, Inc.'
    if name=='hwdata':
        work=Path('/mnt/lfs/sources/phase2/work/hwdata-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/hwdata-0.410')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/hwdata-build.sh').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['upstream_pci_order_exit']==proof['staged_consumer_exit']==0
        assert proof['pnp_records']==2557 and proof['pnp_duplicate_ids']==0 and not proof['modprobe_blacklist_installed']
        assert {r['file'] for r in proof['data_inputs']}=={'pci.ids','usb.ids','oui.txt','iab.txt','pnp.ids'}
        for row in proof['data_inputs']:
            assert row['utf8_exit']==0
            assert (source/row['file']).read_bytes()==(work/'stage/usr/share/hwdata'/row['file']).read_bytes()
            assert hashlib.sha256((source/row['file']).read_bytes()).hexdigest()==row['sha256']
    if name=='lcms2':
        work=Path('/mnt/lfs/sources/phase2/work/lcms2-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/lcms2-2.19.1')
        assert json.loads((log/'lcms2-1.job.json').read_text())['command'][-2:]==['bash','/src/toddy-build.sh']
        for local,canonical in [('toddy-build.sh','lcms2-build.sh'),('toddy-probe.c','lcms2-probe.c')]:
            assert (source/local).read_bytes()==(ROOT/'scripts/build/phase2'/canonical).read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        rows=[json.loads(x) for x in (work/'compile/meson-logs/testlog.json').read_text().splitlines()]
        assert len(rows)==1 and rows[0]['name']=='Little-CMS:testcms'
        assert rows[0]['result']=='OK' and rows[0]['returncode']==0
        assert proof['staged_consumer_exit']==0 and proof['icc_roundtrip'] and proof['malformed_icc_refusal']
    if name=='at-spi2-core':
        work=Path('/mnt/lfs/sources/phase2/work/at-spi2-core-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/at-spi2-core-2.60.6')
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/at-spi2-core-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        expected={'dbind-test','droute-test','memory','testdocument','testrole','testrelation','teststateset','testvalue','atk-test'}
        rows=proof['upstream_drivers']
        assert len(rows)==9 and {r['name'].split(':')[-1] for r in rows}==expected
        assert all(r['native_exit']==0 for r in rows)
        assert proof['staged_consumer_exit']==proof['gi_exit']==0
        if qualifier=='atspi-finish-4':
            command=json.loads((log/(qualifier+'.job.json')).read_text())['command']
            assert command[-5:]==['python3','-c',(ROOT/'scripts/build/phase2/atspi_finish.py').read_text(),(ROOT/'scripts/build/phase2/atspi_private_bus.py').read_text(),(ROOT/'scripts/build/phase2/at-spi2-core-build.sh').read_text()]
            assert proof['reused_passed_drivers']==7 and proof['affected_private_bus_drivers']==2
            for relative,digest in json.loads((work/'finish-4/binaries-before.json').read_text()).items():
                with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
            original=[json.loads(x) for x in (work/'finish-4/original-testlog.json').read_text().splitlines()]
            affected=[json.loads(x) for x in (work/'finish-4/affected-testlog.json').read_text().splitlines()]
            assert len(original)==9 and sum(r['result']=='OK' for r in original)==7
            assert {r['name'].split(':')[-1] for r in original if r['result']!='OK'}=={'memory','atk-test'}
            assert len(affected)==2 and all(r['result']=='OK' and r['returncode']==0 for r in affected)
        else:
            assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/at-spi2-core-build.sh').read_bytes()
            assert (source/'toddy-private-bus.py').read_bytes()==(ROOT/'scripts/build/phase2/atspi_private_bus.py').read_bytes()
    if name=='gi-gl-types':
        work=Path('/mnt/lfs/sources/phase2/work/gi-gl-types-1')
        assert json.loads((log/'gi-gl-types-1.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/gi-gl-types-build.sh').read_text()
        proof=json.loads((work/'test-results.json').read_text());assert proof['native_compiler_exit']==proof['native_import_exit']==0 and proof['records']==13
        source=Path('/mnt/lfs/sources/phase2/inputs/gobject-introspection-1.86.0/gir/GL-1.0.gir')
        assert source.read_bytes()==(work/'stage/usr/share/gir-1.0/GL-1.0.gir').read_bytes()
        assert hashlib.sha256(source.read_bytes()).hexdigest()==proof['source_sha256']
    if name=='gi-dbus-types':
        work=Path('/mnt/lfs/sources/phase2/work/gi-dbus-types-1')
        assert json.loads((log/'gi-dbus-types-1.job.json').read_text())['command'][-1]==(ROOT/'scripts/build/phase2/gi-dbus-types-build.sh').read_text()
        proof=json.loads((work/'test-results.json').read_text());assert proof['native_compiler_exit']==proof['native_enum_consumer_exit']==0
        source=Path('/mnt/lfs/sources/phase2/inputs/gobject-introspection-1.86.0/gir/DBus-1.0.gir')
        assert source.read_bytes()==(work/'stage/usr/share/gir-1.0/DBus-1.0.gir').read_bytes()
        assert hashlib.sha256(source.read_bytes()).hexdigest()==proof['source_sha256']
    if name=='gi-desktop-types':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/gi-desktop-types-1/test-results.json').read_text())
        assert {r['name'] for r in proof['types']}=={'freetype2-2.0','fontconfig-2.0','libxml2-2.0','cairo-1.0'}
        command=json.loads((log/'gi-desktop-types-1.job.json').read_text())['command']
        assert command[-1]==(ROOT/'scripts/build/phase2/gi-desktop-types-build.sh').read_text()
    if name=='cairo':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/cairo-1/test-results.json').read_text())
        assert proof['full_upstream_suite']=='not qualified; BLFS states not working'
        assert proof['registered_driver_failures']==0
    if name=='freetype':
        proof=json.loads(Path('/mnt/lfs/sources/phase2/work/freetype-1/test-results.json').read_text())
        assert proof['staged_consumer_exit']==0 and proof['upstream_suite']=='not provided'
    if name=='libpng':
        counts=json.loads(Path('/mnt/lfs/sources/phase2/work/libpng-1/test-results.json').read_text())
        assert counts['TOTAL']>0 and counts['TOTAL']==counts['PASS']
        assert all(counts[k]==0 for k in ['SKIP','XFAIL','FAIL','XPASS','ERROR'])
    if name=='libxml2':
        status=json.loads((ROOT/'status.json').read_text())
        assert status['owner_review']['phase_2_approved'] is True
        assert next(r for r in status['milestones'] if r['id']=='B02')['status']=='in_progress'
        work=Path('/mnt/lfs/sources/phase2/work/libxml2-1')
        tests=json.loads((work/'test-results.json').read_text())
        assert {t['name'] for t in tests}=={'testdict','testchar','testparser','testrecurse','testcatalog','testapi','runtest'}
        assert len(tests)==7 and all(t['exit']==0 for t in tests)
        assert (work/'test-logs/runtest.log').read_text().rstrip().endswith('Total 3904 tests, no errors')
    if name=='sassc':
        work=Path('/mnt/lfs/sources/phase2/work/sassc-1');source=Path('/mnt/lfs/sources/phase2/inputs/sassc-3.6.2')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/sassc-build.sh').read_bytes()
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/sassc-probe.py').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        checks=proof['consumer']['checks'];assert len(checks)==4
        assert all((r['native_exit']!=0) if r['expected_refusal'] else (r['native_exit']==0) for r in checks)
        assert [r['name'] for r in checks]==['version','nested-unicode','private-include','malformed-refusal']
    if name=='libsass':
        work=Path('/mnt/lfs/sources/phase2/work/libsass-1');source=Path('/mnt/lfs/sources/phase2/inputs/libsass-3.6.6')
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libsass-probe.c').read_bytes()
        if qualifier=='libsass-qualify-2':
            assert (log/'libsass-1.exit').read_text().strip()=='1'
            assert json.loads((log/'libsass-qualify-2.job.json').read_text())['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/libsass_qualify.py').read_text()]
            for relative,digest in json.loads((work/'qualify-2/binaries.json').read_text()).items():
                with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
            for relative,row in json.loads((work/'qualify-2/stage-files.json').read_text()).items():
                path=work/'stage'/relative
                if 'link' in row:assert str(path.readlink())==row['link']
                else:
                    with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
        else:assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libsass-build.sh').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['bundled_upstream_cpp_programs']==2 and proof['bundled_upstream_exit']==proof['staged_consumer_exit']==0
        assert all(r['native_exit']==0 and not r['reserve_stop'] for r in proof['phases'])
        original=source/'include/sass/version.h';generated=work/'compile/include/sass/version.h'
        assert generated.read_bytes()==original.read_bytes().replace(b'"[NA]"',b'"3.6.6"',1)
    if name=='appstream':
        work=Path('/mnt/lfs/sources/phase2/work/appstream-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/AppStream-1.1.6')
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/appstream-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['gi_exit']==0
        rows=[json.loads(l) for l in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()]
        assert len(rows)==8 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
        if qualifier=='appstream-probe-4':
            assert (log/'appstream-configure-3.exit').read_text().strip()=='1'
            command=json.loads((log/'appstream-configure-3.job.json').read_text())['command']
            assert hashlib.sha256(command[-1].encode()).hexdigest()=='252782d8a01dfa8ffe0043ad9f84f9e87db3245b1c5d8adcfcd20f5a6ffb2852'
            assert json.loads((log/'appstream-probe-4.job.json').read_text())['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/appstream_finish.py').read_text()]
            for relative,digest in json.loads((work/'probe-4/binaries-before.json').read_text()).items():
                with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
            expected=json.loads((work/'probe-4/stage-before.json').read_text());actual=inspect_stage(work/'stage')['entries']
            assert set(actual)==set(expected)
            for relative,row in expected.items():
                path=work/'stage'/relative;st=path.lstat()
                assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid'])
                if 'link' in row:assert str(path.readlink())==row['link']
                if 'sha256' in row:assert actual[relative]['sha256']==row['sha256']
        else:assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/appstream-build.sh').read_bytes()
    if name=='libfyaml':
        import xml.etree.ElementTree as ET
        work=Path('/mnt/lfs/sources/phase2/work/libfyaml-1')
        original=json.loads((log/'libfyaml-1.job.json').read_text())['command']
        if qualifier=='libfyaml-finish-2':
            assert (log/'libfyaml-1.exit').read_text().strip()=='2'
            assert hashlib.sha256(original[-1].encode()).hexdigest()=='7484f54ca53df4029de7ee890cad19ab7e1d49649a6efc5a834ddd8fa1bbd9c0'
            assert json.loads((log/'libfyaml-finish-2.job.json').read_text())['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/libfyaml_finish.py').read_text()]
        else:
            canonical=(ROOT/'scripts/build/phase2/libfyaml-build.sh').read_text()
            if original[-2:]==['bash','/src/toddy-build.sh']:
                assert Path('/mnt/lfs/sources/phase2/inputs/libfyaml-0.9.6/toddy-build.sh').read_text()==canonical
            else:assert original[-3:]==['bash','-c',canonical]
        source=Path('/mnt/lfs/sources/phase2/inputs/libfyaml-0.9.6')
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libfyaml-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        tests=ET.parse(work/'check-ctest.xml').getroot().findall('.//testcase');assert tests and len(tests)==proof['check_sdk_ctest_cases']
        assert all(not any(t.find(k) is not None for k in ['failure','error','skipped']) for t in tests)
        if qualifier=='libfyaml-finish-2':
            assert proof['original_summary']=={'TOTAL':537,'PASS':535,'SKIP':0,'XFAIL':0,'FAIL':0,'XPASS':0,'ERROR':2}
            for relative,digest in json.loads((work/'finish-2/binaries-before.json').read_text()).items():
                with (work/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
            summary=proof['affected_unit_summary']
        else:summary=proof['upstream_summary']
        assert summary['TOTAL']>0 and summary['TOTAL']==summary['PASS']
        assert all(summary.get(k,0)==0 for k in ['SKIP','XFAIL','FAIL','XPASS','ERROR'])
        assert '#define HAVE_COMPATIBLE_CHECK 1' in (work/'compile/config.h').read_text()
    if name=='libxmlb':
        work=Path('/mnt/lfs/sources/phase2/work/libxmlb-1');source=Path('/mnt/lfs/sources/phase2/inputs/libxmlb-0.3.29')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libxmlb-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libxmlb-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['gi_exit']==0
        rows=[json.loads(l) for l in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()]
        assert len(rows)==2 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
        assert sum(r['passed_tap_cases'] for r in proof['upstream_drivers'])==56
    if name=='itstool':
        work=Path('/mnt/lfs/sources/phase2/work/itstool-1');source=Path('/mnt/lfs/sources/phase2/inputs/itstool-2.0.7')
        proof=json.loads((work/'test-results.json').read_text());assert proof['upstream_python_tests']==64 and proof['staged_consumer_exit']==0
        if qualifier=='itstool-dtd-finish-3':
            assert (log/'itstool-recovery-2.exit').read_text().strip()=='1'
            assert json.loads((log/'itstool-dtd-finish-3.job.json').read_text())['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/itstool_finish.py').read_text()]
            assert proof['original_passed']==62 and proof['affected_native_exit']==0
            assert proof['original_failed']==proof['affected_retested']==['test_IT_keep_entities_1','test_IT_translate_with_external_dtds']
            old=(work/'upstream-tests.log').read_text();assert 'Ran 64 tests' in old and old.rstrip().endswith('FAILED (failures=2)')
            new=(work/'dtd-affected-tests.log').read_text();assert 'Ran 2 tests' in new and new.rstrip().endswith('OK')
        else:
            assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/itstool-build.sh').read_bytes()
            assert proof['upstream_exit']==0
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/itstool-probe.py').read_bytes()
        assert all(proof['consumer'][k] is True for k in ['xml_extraction','compiled_gettext_catalog','portuguese_merge'])
    if name=='libxml2-python':
        work=Path('/mnt/lfs/sources/phase2/work/libxml2-1');output=work/'python-binding-1'
        proof=json.loads((output/'qualified-5.json').read_text())
        rows=proof['upstream_python_scripts'];assert len(rows)==48 and len({r['name'] for r in rows})==48
        assert all(r['exit']==0 for r in rows) and proof['staged_consumer_exit']==0
        assert (log/'libxml2-python-target-3.exit').read_text().strip()=='0'
        assert json.loads((log/'libxml2-python-target-3.job.json').read_text())['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/xml_python_build.py').read_text()]
        assert json.loads((log/'libxml2-python-probe-5.job.json').read_text())['command'][-4:]==['python3','-c',(ROOT/'scripts/build/phase2/xml_python_qualify.py').read_text(),(ROOT/'scripts/build/phase2/xml_python_probe.py').read_text()]
        for relative,digest in json.loads((output/'core-before.json').read_text()).items():
            with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
        files={str(p.relative_to(output/'stage')) for p in (output/'stage').rglob('*') if p.is_file()}
        assert files==set(proof['payload']) and len(files)==3
        assert all('/site-packages/' in p and Path(p).suffix in ('.py','.so') for p in files)
        core=json.loads((log.parent/'packages/libxml2_2.15.3-1+toddy1_amd64.json').read_text());assert core['installed']
    if name=='doxygen':
        import xml.etree.ElementTree as ET
        work=Path('/mnt/lfs/sources/phase2/work/doxygen-1');source=Path('/mnt/lfs/sources/phase2/inputs/doxygen-1.18.0')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/doxygen-build.sh').read_bytes()
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/doxygen-probe.py').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        tests=ET.parse(work/'ctest.xml').getroot().findall('.//testcase');assert len(tests)==122
        failed=[r for r in tests if r.find('failure') is not None or r.find('error') is not None]
        if doxygen_finish:
            assert (log/'doxygen-1.exit').read_text().strip()=='8'
            assert len(failed)==1 and failed[0].get('name')=='012_cite'
            assert proof['original_passed']==121 and proof['original_failed'][0]['passed'] is False
            assert json.loads((log/'doxygen-finish-2.job.json').read_text())['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/doxygen_finish.py').read_text()]
            for relative,digest in json.loads((work/'finish-2/binaries-before.json').read_text()).items():
                with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
        else:assert not failed and proof['upstream_exit']==0
        assert not any(r.find('skipped') is not None for r in tests)
        assert proof['consumer']['generator_exit']==proof['consumer']['schema_exit']==0
    if name=='gtk':
        import re
        work=Path('/mnt/lfs/sources/phase2/work/gtk-1');source=Path('/mnt/lfs/sources/phase2/inputs/gtk-4.22.4')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/gtk-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/gtk-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['gi_exit']==0
        tests=proof['upstream_selected'];assert len(tests)==3 and {r['name'] for r in tests}=={'bitset','stringlist','rgba'}
        for r in tests:
            assert r['native_exit']==0 and (work/('upstream-'+r['name']+'.exit')).read_text().strip()=='0'
            text=(work/('upstream-'+r['name']+'.log')).read_text()
            assert len(re.findall(r'^ok\s+\d+',text,re.M))==r['passed_cases'] and r['passed_cases']>0
            assert not re.search(r'^not ok|#\s*SKIP',text,re.M)
        assert hashlib.sha256((work/'stage/usr/share/glib-2.0/schemas/gschemas.compiled').read_bytes()).hexdigest()==proof['schema_cache_sha256']
        volume=json.loads((log/'gtk-build-volume.json').read_text());assert volume['state']=='mounted'
        assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(work)],text=True).strip()==volume['filesystem_uuid']
    if name=='iso-codes':
        work=Path('/mnt/lfs/sources/phase2/work/iso-codes-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/iso-codes-v4.20.1')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/iso-codes-build.sh').read_bytes()
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/iso-codes-probe.py').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==0 and proof['registered_drivers']==8
        results=proof['actual_source_utf8'];assert len(results)==8
        assert all(r['native_exit']==0 and r['actual_po_files']>0 for r in results)
        for row in results:
            assert len(list((source/row['domain']).glob('*.po')))==row['actual_po_files']
            assert (work/('utf8-'+row['domain']+'.exit')).read_text().strip()=='0'
    if name=='tiff':
        import xml.etree.ElementTree as ET
        work=Path('/mnt/lfs/sources/phase2/work/tiff-1')
        source=Path('/mnt/lfs/sources/phase2/inputs/tiff-4.7.2')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/tiff-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/tiff-probe.c').read_bytes()
        report=ET.parse(work/'ctest.xml').getroot();cases=report.findall('.//testcase')
        assert cases and all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases)
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['registered_tests']==len(cases) and proof['upstream_exit']==proof['staged_consumer_exit']==0
    if name=='cbindgen':
        work=Path('/mnt/lfs/sources/phase2/work/cbindgen-1');source=Path('/mnt/lfs/sources/phase2/inputs/cbindgen-tool-0.29.4')
        for prepared,canonical in [('toddy-build.py','cbindgen_build.py'),('toddy-probe.py','cbindgen_probe.py')]:
            assert (source/prepared).read_bytes()==(ROOT/'scripts/build/phase2'/canonical).read_bytes()
        config=json.loads((source/'toddy-crates.json').read_text());assert config==json.loads((ROOT/'config/phase2/cbindgen-crates.lock.json').read_text()) and len(config['packages'])==72
        assert hashlib.sha256((source/'project/Cargo.lock').read_bytes()).hexdigest()==config['cargo_lock_sha256']
        proof=json.loads((work/'test-results.json').read_text());assert proof['upstream_selected_exit']==proof['consumer_exit']==0 and proof['original_inputs_unchanged'] is True
        assert proof['upstream_summaries']==[['ok','2','0','0'],['ok','3','0','0']]
        assert proof['consumer']['malformed_exit']==1
        assert [r['language'] for r in proof['consumer']['outcomes']]==['c','c++']
        assert all(r['generate_exit']==r['compile_exit']==r['native_abi_exit']==0 for r in proof['consumer']['outcomes'])
        assert hashlib.sha256((work/'compile/release/cbindgen').read_bytes()).hexdigest()==proof['binary_sha256']
        assert (work/'compile/release/cbindgen').read_bytes()==(work/'stage/usr/bin/cbindgen').read_bytes()
    if name=='icu':
        work=Path('/mnt/lfs/sources/phase2/work/icu-1');source=Path('/mnt/lfs/sources/phase2/inputs/icu')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/icu-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/icu-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['version']=='78.3'
        assert proof['upstream_exit']==proof['staged_consumer_exit']==proof['staged_cli_exit']==0 and proof['converted_bytes']==8
        assert (work/'upstream-check.exit').read_text().strip()=='0'
        text=(work/'upstream-check.log').read_text()
        assert 'All tests OK:  testdata intltest iotest cintltst' in text and 'PASS: config selfcheck OK' in text
        assert (work/'stage/usr/lib/libicuuc.so.78.3').is_file() and (work/'stage/usr/lib/libicudata.so.78.3').is_file()
    if name=='libadwaita':
        work=Path('/mnt/lfs/sources/phase2/work/libadwaita-1');source=Path('/mnt/lfs/sources/phase2/inputs/libadwaita-1.9.3')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libadwaita-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libadwaita-probe.c').read_bytes()
        stage=json.loads((work/'stage-results.json').read_text());assert stage['native_build_exit']==stage['stage_exit']==stage['c_version_exit']==stage['gi_version_exit']==0
        raw=(log/'native-mutter-1-report.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='18108d6681186c55dd19f1be9256f37ae569cdffbd5dc167b6224298a2117d65'
        report=json.loads(raw);assert report['kernel']=='7.1.8-toddy' and report['all_selected_exits_zero'] is True
        assert report['suite']['widget_drivers_exit_zero']==67 and report['suite']['passed_case_executions']==408 and report['suite']['skipped_case_executions']==0
        manifest=Path('/mnt/lfs/sources/phase2/native-fixtures/mutter-1/accepted.json');assert hashlib.sha256(manifest.read_bytes()).hexdigest()==report['manifest_sha256']
        accepted=json.loads(manifest.read_text());registered=json.loads((work/'compile/meson-info/intro-tests.json').read_text());assert len(registered)==67
        runs={r['name']:r for r in report['runs'] if r['name']!='native-gtk-window'}
        assert set(runs)=={r['name'] for r in registered} and all(r['exit']==0 for r in runs.values())
        for p,digest in accepted['artifacts'].items():assert hashlib.sha256((Path('/mnt/lfs')/p.lstrip('/')).read_bytes()).hexdigest()==digest
        before={str(p.relative_to(source/'tests')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source/'tests').rglob('*') if p.is_file() and not p.is_symlink()}
        assert hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()==accepted['source_test_assets_sha256']
        assert (work/'compile/src/libadwaita-1.so.0').read_bytes()==(work/'stage/usr/lib/libadwaita-1.so.0').read_bytes()
    if name=='docutils':
        work=Path('/mnt/lfs/sources/phase2/work/docutils-1');source=Path('/mnt/lfs/sources/phase2/inputs/docutils-0.23')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/docutils-build.sh').read_bytes()
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/docutils-probe.py').read_bytes()
        prepared=json.loads((source/'toddy-prepared.json').read_text());assert prepared['extra_source']['name']=='docutils-flit-backend' and prepared['extra_source']['version']=='3.12.0'
        proof=json.loads((work/'test-results.json').read_text());assert proof['upstream_exit']==proof['staged_cli_exit']==proof['staged_consumer']['native_consumer_exit']==0 and proof['upstream_manpage_cases']==4
        wheels=list((work/'wheels').glob('*.whl'));assert len(wheels)==1 and hashlib.sha256(wheels[0].read_bytes()).hexdigest()==proof['wheel_sha256']
    if name=='colord':
        work=Path('/mnt/lfs/sources/phase2/work/colord-1');source=Path('/mnt/lfs/sources/phase2/inputs/colord-1.4.8')
        recipe=(ROOT/'scripts/build/phase2/colord-build.sh').read_text()
        assert (source/'toddy-build.sh').read_text()==recipe
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/colord-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0 and proof['distinct_original_cases_qualified']==38
        edid=hashlib.sha256((log/'hwdb-colord-edid-2.log').read_bytes()).hexdigest();assert edid==proof['native_edid_case_recovered']['log_sha256']
        native=json.loads((log.parent/'build/b02-hwdb-cache-edid-postcheck.success.json').read_text());assert native['recipe_exit']==native['postcheck_exit']==0
        code=(ROOT/'scripts/build/phase2/colord_complete.py').read_text()+'\nmain('+repr(recipe)+','+repr(edid)+')\n'
        assert json.loads((log/'colord-finish-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
        assert len(proof['original_cases_reused'])==4 and len(proof['pending_case_results'])==33
        for row in proof['pending_case_results']:
            p=Path(str(row['log']).replace('/build/',str(work)+'/',1));assert row['native_exit']==0 and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
            assert 'ok 1 '+row['name'] in p.read_text() and '# SKIP' not in p.read_text()
    if name=='libgusb':
        work=Path('/mnt/lfs/sources/phase2/work/libgusb-1');source=Path('/mnt/lfs/sources/phase2/inputs/libgusb-0.4.9')
        recipe=(ROOT/'scripts/build/phase2/libgusb-build.sh').read_text();probe=(ROOT/'scripts/build/phase2/libgusb-probe.c').read_text()
        assert (source/'toddy-build.sh').read_text()==recipe.replace('ninja -C /build/compile gusb/libgusb.ver > /build/api-map.log 2>&1\n','')
        original_probe=probe.replace('GMainContext *main_context=g_main_context_new();g_usb_context_set_main_context(context,main_context);assert(g_usb_context_get_main_context(context)==main_context);g_main_context_unref(main_context);','g_usb_context_set_hotplug_poll_interval(context,5000);assert(g_usb_context_get_hotplug_poll_interval(context)==5000);')
        assert (source/'toddy-probe.c').read_text()==original_probe
        finish=(ROOT/'scripts/build/phase2/gusb_finish.py').read_text()+'\nmain('+repr(recipe)+')\n'
        assert json.loads((log/'libgusb-finish-2.job.json').read_text())['command'][-3:]==['python3','-c',finish]
        code=(ROOT/'scripts/build/phase2/gusb_probe_qualify.py').read_text()+'\nmain('+repr(probe)+','+repr(recipe)+')\n'
        assert json.loads((log/'libgusb-probe-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
        assert (work/'probe-3/consumer.exit').read_text().strip()=='0'
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['exported_api_exit']==0 and proof['original_portable_cases']==2
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0
    if name=='libusb':
        work=Path('/mnt/lfs/sources/phase2/work/libusb-1');source=Path('/mnt/lfs/sources/phase2/inputs/libusb-1.0.30')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libusb-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libusb-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        for name2 in ['set_option','init_context']:
            assert ':test-result: PASS' in (work/('compile/tests/'+name2+'.trs')).read_text()
    if name=='libcanberra':
        work=Path('/mnt/lfs/sources/phase2/work/libcanberra-1');source=Path('/mnt/lfs/sources/phase2/inputs/libcanberra-0.30')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libcanberra-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libcanberra-probe.c').read_bytes()
        prepared=json.loads((source/'toddy-prepared.json').read_text());assert prepared['extra_source']['name']=='libcanberra-wayland-patch' and len(prepared['source_patches'])==2
        proof=json.loads((work/'test-results.json').read_text());assert proof['registered_upstream_suites']==0 and proof['staged_consumer_exit']==0
    if name=='pulseaudio':
        work=Path('/mnt/lfs/sources/phase2/work/pulseaudio-1');source=Path('/mnt/lfs/sources/phase2/inputs/pulseaudio-17.0')
        recipe=(ROOT/'scripts/build/phase2/pulseaudio-build.sh').read_text()
        assert (source/'toddy-build.sh').read_text()==recipe.replace('LD_LIBRARY_PATH=/stage/usr/lib:/stage/usr/lib/pulseaudio /build/consumer >','/build/consumer >')
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/pulseaudio-probe.c').read_bytes()
        code=(ROOT/'scripts/build/phase2/pulse_probe_qualify.py').read_text()+'\nmain('+repr(recipe)+')\n'
        assert json.loads((log/'pulseaudio-probe-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
        assert (work/'consumer-2.exit').read_text().strip()=='0'
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0 and len(proof['upstream_drivers'])==12
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==12 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    if name=='libsndfile':
        work=Path('/mnt/lfs/sources/phase2/work/libsndfile-1');source=Path('/mnt/lfs/sources/phase2/inputs/libsndfile-1.2.2')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libsndfile-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libsndfile-probe.c').read_bytes()
        code=(ROOT/'scripts/build/phase2/sndfile_qualify.py').read_text()+'\nmain()\n'
        assert json.loads((log/'libsndfile-qualify-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
        proof=json.loads((work/'test-results.json').read_text());assert proof['upstream_make_check_exit']==proof['staged_consumer_exit']==0
        assert hashlib.sha256((work/'upstream-tests.log').read_bytes()).hexdigest()==proof['log_sha256']
    if name=='libvorbis':
        work=Path('/mnt/lfs/sources/phase2/work/libvorbis-1');source=Path('/mnt/lfs/sources/phase2/inputs/libvorbis-1.3.7')
        recipe=(ROOT/'scripts/build/phase2/libvorbis-build.sh').read_text();probe=(ROOT/'scripts/build/phase2/libvorbis-probe.c').read_text()
        assert (source/'toddy-build.sh').read_text()==recipe
        assert (source/'toddy-probe.c').read_text()==probe.replace('#define OV_EXCLUDE_STATIC_CALLBACKS\n','')
        code=(ROOT/'scripts/build/phase2/vorbis_probe_qualify.py').read_text()+'\nmain('+repr(probe)+','+repr(recipe)+')\n'
        assert json.loads((log/'libvorbis-probe-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
        assert (work/'probe-2/consumer.exit').read_text().strip()=='0'
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['upstream_exit']==0 and proof['upstream_codec_roundtrips']==528
    if name=='libogg':
        work=Path('/mnt/lfs/sources/phase2/work/libogg-1');source=Path('/mnt/lfs/sources/phase2/inputs/libogg-1.3.6')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libogg-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libogg-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        assert [r['name'] for r in proof['upstream_drivers']]==['test_bitwise','test_framing']
        for row in proof['upstream_drivers']:
            assert row['result']=='PASS' and row['exit']==0
            assert ':test-result: PASS' in (work/('compile/src/'+row['name']+'.trs')).read_text()
    if name=='json-glib':
        work=Path('/mnt/lfs/sources/phase2/work/json-glib-1');source=Path('/mnt/lfs/sources/phase2/inputs/json-glib-1.10.8')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/json-glib-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/json-glib-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['gi_exit']==0
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==17 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    if name=='gnome-desktop':
        work=Path('/mnt/lfs/sources/phase2/work/gnome-desktop-1');source=Path('/mnt/lfs/sources/phase2/inputs/gnome-desktop-44.5')
        recipe=(ROOT/'scripts/build/phase2/gnome-desktop-build.sh').read_text()
        original=recipe.replace("cc -DG_LOG_DOMAIN='\"GnomeDesktop\"' -I/build/compile/libgnome-desktop",'cc -DGNOME_DESKTOP_USE_UNSTABLE_API').replace('gnome-desktop-4 gio-2.0','gnome-desktop-4')
        assert (source/'toddy-build.sh').read_text()==original
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/gnome-desktop-probe.c').read_bytes()
        code=(ROOT/'scripts/build/phase2/gnome_desktop_finish.py').read_text()+'\nmain('+repr(recipe)+",'finish-3')\n"
        assert json.loads((log/'gnome-desktop-finish-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0 and proof['original_languages_cases']==1
        assert 'ok 1 /languages/using-null-locale' in (work/'original-languages.log').read_text()
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==1 and rows[0]['name'].endswith('bg-slide-show') and rows[0]['result']=='OK' and rows[0]['returncode']==0
    if name=='libwacom':
        work=Path('/mnt/lfs/sources/phase2/work/libwacom-1');source=Path('/mnt/lfs/sources/phase2/inputs/libwacom-2.19.1')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libwacom-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libwacom-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==9
        for r in rows:
            assert (r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77 and r['name'].endswith('files-in-git'))
        assert len(proof['original_c_drivers'])==4 and sum(r['passed_cases'] for r in proof['original_c_drivers'])==8725
        for r in proof['original_c_drivers']:
            assert (work/(r['name']+'.exit')).read_text().strip()=='0' and r['skipped_cases']==0
    if name=='libgudev':
        work=Path('/mnt/lfs/sources/phase2/work/libgudev-1');source=Path('/mnt/lfs/sources/phase2/inputs/libgudev-238')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libgudev-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libgudev-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['gi_exit']==0 and proof['upstream_tag_cases']==1
        assert 'ok 1 /gudev/tags' in (work/'upstream-tags.log').read_text()
        assert json.loads((work/'compile/meson-info/intro-tests.json').read_text())==[]
    if name=='libnotify':
        work=Path('/mnt/lfs/sources/phase2/work/libnotify-1');source=Path('/mnt/lfs/sources/phase2/inputs/libnotify-0.8.8')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libnotify-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libnotify-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['gi_exit']==0
        assert proof['registered_upstream_tests']==0 and json.loads((work/'compile/meson-info/intro-tests.json').read_text())==[]
        assert 'org.freedesktop.DBus.Error.ServiceUnknown' in (work/'consumer.log').read_text()
    if name=='wireplumber':
        work=Path('/mnt/lfs/sources/phase2/work/wireplumber-1');source=Path('/mnt/lfs/sources/phase2/inputs/wireplumber-0.5.15')
        recipe=(ROOT/'scripts/build/phase2/wireplumber-build.sh').read_text()
        assert (source/'toddy-build.sh').read_text()==recipe.replace('-Dintrospection=disabled','-Dintrospection=enabled')
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/wireplumber-probe.c').read_bytes()
        code=(ROOT/'scripts/build/phase2/wireplumber_pot_recover.py').read_text()+'\nmain('+repr(recipe)+')\n'
        assert json.loads((log/'wireplumber-pot-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
        rows=[json.loads(s) for s in (work/'compile-2/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==53 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==proof['cli_version_exit']==0
        routing=json.loads((work/'pot-3/routing.json').read_text());assert routing['preserved_elfs']
        assert all(hashlib.sha256((work/n).read_bytes()).hexdigest()==h for n,h in routing['preserved_elfs'].items())
        assert hashlib.sha256((work/'compile-2/build.ninja').read_bytes()).hexdigest()==routing['after_sha256']
        assert ' -o ../../src/po/conf.pot ' not in (work/'compile-2/build.ninja').read_text()
        assert 'msgid' in (work/'compile-2/po/conf.pot').read_text()
    if name=='lua':
        work=Path('/mnt/lfs/sources/phase2/work/lua-1');source=Path('/mnt/lfs/sources/phase2/inputs/lua-5.4.8')
        recipe=(ROOT/'scripts/build/phase2/lua-build.sh').read_text()
        probe=(ROOT/'scripts/build/phase2/lua-probe.c').read_text()
        assert (source/'toddy-build.sh').read_text()==recipe
        code=(ROOT/'scripts/build/phase2/lua_probe_qualify.py').read_text()+'\nmain('+repr(probe)+','+repr(recipe)+')\n'
        assert json.loads((log/'lua-probe-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
        context=(ROOT/'scripts/build/phase2/lua_patch_recover.py').read_text()+'\nmain('+repr(recipe)+')\n'
        assert json.loads((log/'lua-context-2.job.json').read_text())['command'][-3:]==['python3','-c',context]
        assert (work/'probe-3/consumer.c').read_text()==probe and (work/'probe-3/consumer.exit').read_text().strip()=='0'
        assert 'final OK' in (work/'upstream-tests.log').read_text()
        assert (work/'project-2/src/liblua.so.5.4.8').read_bytes()==(work/'stage/usr/lib/liblua.so.5.4.8').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['upstream_basic_suite_exit']==proof['staged_consumer_exit']==0
        patch=json.loads((work/'patch-context-2.json').read_text());assert patch['original_sha256']=='44324a802822f0a35d095aaad2f5f58fa7b1821ae87ae44dbcfc8a23fcd2e67e'
    if name=='pipewire':
        work=Path('/mnt/lfs/sources/phase2/work/pipewire-1');source=Path('/mnt/lfs/sources/phase2/inputs/pipewire-1.6.8')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/pipewire-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/pipewire-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_daemon_client_exit']==0 and proof['daemon_stopped']
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==50 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
        assert any(r['type']=='PipeWire:Interface:Core' for r in json.loads((work/'core-dump.json').read_text()))
        options={r['name']:r['value'] for r in json.loads((work/'compile/meson-info/intro-buildoptions.json').read_text())}
        assert options['alsa']=='enabled' and options['udev']=='enabled' and options['session-managers']==[]
        assert not options['pam-defaults-install'] and not options['rlimits-install']
    if name=='alsa-lib':
        work=Path('/mnt/lfs/sources/phase2/work/alsa-lib-1');source=Path('/mnt/lfs/sources/phase2/inputs/alsa-lib-1.2.16.1')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/alsa-lib-build.sh').read_bytes()
        code=(ROOT/'scripts/build/phase2/alsa_lib_qualify.py').read_text()+'\nmain('+repr((ROOT/'scripts/build/phase2/alsa-lib-probe.c').read_text())+')\n'
        assert json.loads((log/'alsa-lib-probe-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
        assert (work/'probe-2/consumer.c').read_bytes()==(ROOT/'scripts/build/phase2/alsa-lib-probe.c').read_bytes()
        assert (work/'probe-2/consumer.exit').read_text().strip()=='0'
        for test in ['config','midi_event']:
            assert ':test-result: PASS' in (work/('compile/test/lsb/'+test+'.trs')).read_text()
        proof=json.loads((work/'test-results.json').read_text());assert proof['upstream_check_exit']==proof['staged_consumer_exit']==0
    if name=='libinput':
        work=Path('/mnt/lfs/sources/phase2/work/libinput-1');source=Path('/mnt/lfs/sources/phase2/inputs/libinput-1.31.3')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libinput-build.sh').read_bytes()
        prepared=json.loads((source/'toddy-prepared.json').read_text())
        assert inspect_stage(source/'toddy-test-sdk')==prepared['private_test_sdk']['manifest']
        assert prepared['private_test_sdk']['upstream_sdk_cases_reused']==9
        code=(ROOT/'scripts/build/phase2/libinput_qualify.py').read_text()+'\nmain('+repr((ROOT/'scripts/build/phase2/libinput-probe.c').read_text())+')\n'
        assert json.loads((log/'libinput-probe-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
        assert (work/'probe-2/consumer.c').read_bytes()==(ROOT/'scripts/build/phase2/libinput-probe.c').read_bytes()
        assert (work/'probe-2/consumer.exit').read_text().strip()=='0'
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==10 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        assert proof['profile']=={'mtdev':True,'libwacom':False,'lua_plugins':False,'internal_event_debugging':False,'debug_gui':False}
    if name=='libei':
        work=Path('/mnt/lfs/sources/phase2/work/libei-1');source=Path('/mnt/lfs/sources/phase2/inputs/libei-1.6.0')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libei-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libei-probe.c').read_bytes()
        prepared=json.loads((source/'toddy-prepared.json').read_text())
        assert prepared['extra_source']['name']=='munit-test-dependency'
        assert 'revision='+prepared['extra_source']['commit'] in (source/'subprojects/munit.wrap').read_text()
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0 and not proof['test_dependency_installed']
        assert (log/'libei-1.exit').read_text().strip()=='0'
        assert json.loads((log/'libei-dtd-2.job.json').read_text())['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/libei_schema_qualify.py').read_text()]
        assert proof['source_schema_validation']['name']=='dtdcheck' and proof['source_schema_validation']['native_exit']==0
        assert (work/'schema-2/dtd.exit').read_text().strip()=='0'
        assert hashlib.sha256((work/'schema-2/dtd.log').read_bytes()).hexdigest()==proof['source_schema_validation']['log_sha256']
        assert len(proof['upstream_selected'])==6 and sum(r['case_executions'] for r in proof['upstream_selected'])>0
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==6 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
        assert not any('munit' in str(p.relative_to(work/'stage')) for p in (work/'stage').rglob('*'))
    if name=='libxcvt':
        work=Path('/mnt/lfs/sources/phase2/work/libxcvt-1');source=Path('/mnt/lfs/sources/phase2/inputs/libxcvt-0.1.3')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libxcvt-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libxcvt-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['registered_upstream_tests']==0 and proof['staged_consumer_exit']==proof['cli_exit']==0
        assert json.loads((work/'compile/meson-info/intro-tests.json').read_text())==[]
    if name=='libevdev':
        import re
        work=Path('/mnt/lfs/sources/phase2/work/libevdev-1');source=Path('/mnt/lfs/sources/phase2/inputs/libevdev-1.13.6')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/libevdev-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/libevdev-probe.c').read_bytes()
        prepared=json.loads((source/'toddy-prepared.json').read_text())
        assert inspect_stage(source/'toddy-test-sdk')==prepared['private_test_sdk']['manifest']
        assert prepared['private_test_sdk']['upstream_sdk_cases_reused']==9
        proof=json.loads((work/'test-results.json').read_text());assert proof['staged_consumer_exit']==0
        rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
        assert len(rows)==len(proof['upstream_drivers'])==6 and proof['native_check_cases']>0
        count=0
        for row in rows:
            text=row.get('stdout','')+row.get('stderr','')
            if row['result']=='SKIP':
                assert row['returncode']==77 and 'needs to run as root' in text
            else:
                assert row['result']=='OK' and row['returncode']==0
                summaries=re.findall(r'Checks:\s*(\d+), Failures:\s*(\d+), Errors:\s*(\d+)',text)
                assert all(int(f)==int(e)==0 for _,f,e in summaries)
                count+=sum(int(n) for n,_,_ in summaries)
        assert count==proof['native_check_cases']
    if name=='mtdev':
        work=Path('/mnt/lfs/sources/phase2/work/mtdev-1');source=Path('/mnt/lfs/sources/phase2/inputs/mtdev-1.1.7')
        assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/mtdev-build.sh').read_bytes()
        assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/mtdev-probe.c').read_bytes()
        proof=json.loads((work/'test-results.json').read_text())
        assert proof['staged_consumer_exit']==proof['upstream_diagnostic_exit']==0 and proof['matching_cases']==2
        assert len(proof['matching_oracle'])==2 and all(r['matching_cost']==r['independent_exhaustive_optimum'] for r in proof['matching_oracle'])
    if name=='dbus-python':
        from qualify_dbus_python import qualify as qualify_dbus_python
        qualify_dbus_python(ROOT,log)
    if name=='json-c':
        from qualify_json_c import qualify as qualify_json_c
        qualify_json_c(ROOT)
    if name=='polkit':
        from qualify_polkit import qualify as qualify_polkit
        qualify_polkit(ROOT)
    if name=='gnome-keyring':
        from qualify_gnome_keyring import qualify as qualify_gnome_keyring
        qualify_gnome_keyring(ROOT)
    if name=='libical':
        from qualify_libical import qualify as qualify_libical
        qualify_libical(ROOT)
    if name=='nspr':
        from qualify_nspr import qualify as qualify_nspr
        qualify_nspr(ROOT)
    if name=='nss':
        from qualify_nss import qualify as qualify_nss
        qualify_nss(ROOT)
    if name=='libpsl':
        from qualify_libpsl import qualify as qualify_libpsl
        qualify_libpsl(ROOT)
    if name=='nettle':
        from qualify_nettle import qualify as qualify_nettle
        qualify_nettle(ROOT)
    if name=='libunistring':
        from qualify_libunistring import qualify as qualify_libunistring
        qualify_libunistring(ROOT)
    if name=='libidn2':
        from qualify_libidn2 import qualify as qualify_libidn2
        qualify_libidn2(ROOT)
    if name=='gnutls':
        from qualify_gnutls import qualify as qualify_gnutls
        qualify_gnutls(ROOT)
    if name=='libproxy':
        from qualify_libproxy import qualify as qualify_libproxy
        qualify_libproxy(ROOT)
    if name=='libsoup':
        from qualify_libsoup import qualify as qualify_libsoup
        qualify_libsoup(ROOT)
    if name=='evolution-data-server':
        from qualify_eds import qualify as qualify_eds
        qualify_eds(ROOT)
    if name=='gnome-text-editor':
        from qualify_gnome_text_editor import qualify as qualify_gnome_text_editor
        qualify_gnome_text_editor(ROOT)
    if name=='cups':
        from qualify_cups import qualify as qualify_cups
        qualify_cups(ROOT)
    if name=='mitkrb':
        from qualify_mitkrb import qualify as qualify_mitkrb
        qualify_mitkrb(ROOT)
    if name=='libgtop':
        from qualify_libgtop import qualify as qualify_libgtop
        qualify_libgtop(ROOT)
    if name=='colord-gtk':
        from qualify_colord_gtk import qualify as qualify_colord_gtk
        qualify_colord_gtk(ROOT)
    if name=='modemmanager':
        from qualify_modemmanager import qualify as qualify_modemmanager
        qualify_modemmanager(ROOT)
    if name=='libqmi':
        from qualify_libqmi import qualify as qualify_libqmi
        qualify_libqmi(ROOT)
    if name=='libmbim':
        from qualify_libmbim import qualify as qualify_libmbim
        qualify_libmbim(ROOT)
    if name=='gnome-bluetooth':
        from qualify_gnome_bluetooth import qualify as qualify_gnome_bluetooth
        qualify_gnome_bluetooth(ROOT)
    if name=='gsound':
        from qualify_gsound import qualify as qualify_gsound
        qualify_gsound(ROOT)
    if name=='libpwquality':
        from qualify_libpwquality import qualify as qualify_libpwquality
        qualify_libpwquality(ROOT)
    if name=='cracklib':
        from qualify_cracklib import qualify as qualify_cracklib
        qualify_cracklib(ROOT)
    if name=='gnome-online-accounts':
        from qualify_goa import qualify as qualify_goa
        qualify_goa(ROOT)
    if name=='librest':
        from qualify_librest import qualify as qualify_librest
        qualify_librest(ROOT)
    if name=='tecla':
        from qualify_tecla import qualify as qualify_tecla
        qualify_tecla(ROOT)
    if name=='editorconfig':
        from qualify_editorconfig import qualify as qualify_editorconfig
        qualify_editorconfig(ROOT)
    if name=='libspelling':
        from qualify_libspelling import qualify as qualify_libspelling
        qualify_libspelling(ROOT)
    if name=='enchant':
        from qualify_enchant import qualify as qualify_enchant
        qualify_enchant(ROOT)
    if name=='aspell':
        from qualify_aspell import qualify as qualify_aspell
        qualify_aspell(ROOT)
    if name=='gexiv2':
        from qualify_gexiv2 import qualify as qualify_gexiv2
        qualify_gexiv2(ROOT)
    if name=='exiv2':
        from qualify_exiv2 import qualify as qualify_exiv2
        qualify_exiv2(ROOT)
    if name in ('brotli','inih'):
        from qualify_metadata_prerequisites import qualify as qualify_metadata
        qualify_metadata(ROOT,name)
    if name=='blueprint-compiler':
        from qualify_blueprint_compiler import qualify as qualify_blueprint_compiler
        qualify_blueprint_compiler(ROOT)
    if name=='glycin-gtk4':
        from qualify_glycin_gtk4 import qualify as qualify_glycin_gtk4
        qualify_glycin_gtk4(ROOT)
    if name=='tinysparql':
        from qualify_tinysparql import qualify as qualify_tinysparql
        qualify_tinysparql(ROOT)
    if name=='gnome-autoar':
        from qualify_gnome_autoar import qualify as qualify_gnome_autoar
        qualify_gnome_autoar(ROOT)
    if name=='libportal':
        from qualify_libportal import qualify as qualify_libportal
        qualify_libportal(ROOT)
    if name=='gnome-terminal':
        from qualify_gnome_terminal import qualify as qualify_gnome_terminal
        qualify_gnome_terminal(ROOT)
    if name=='libxslt':
        from qualify_libxslt import qualify as qualify_libxslt
        qualify_libxslt(ROOT)
    if name=='libhandy':
        from qualify_libhandy import qualify as qualify_libhandy
        qualify_libhandy(ROOT)
    if name=='vte':
        from qualify_vte import qualify as qualify_vte
        qualify_vte(ROOT)
    if name=='simdutf':
        from qualify_simdutf import qualify as qualify_simdutf
        qualify_simdutf(ROOT)
    if name=='fmt':
        from qualify_fmt import qualify as qualify_fmt
        qualify_fmt(ROOT)
    if name=='fast-float':
        from qualify_fast_float import qualify as qualify_fast_float
        qualify_fast_float(ROOT)
    if name=='gst-plugins-base':
        from qualify_gst_plugins_base import qualify as qualify_gst_plugins_base
        qualify_gst_plugins_base(ROOT)
    if name=='gstreamer':
        from qualify_gstreamer import qualify as qualify_gstreamer
        qualify_gstreamer(ROOT)
    if name=='gnome-shell':
        from qualify_gnome_shell import qualify as qualify_gnome_shell
        qualify_gnome_shell(ROOT)
    if name=='gnome-settings-daemon':
        from qualify_gnome_settings_daemon import qualify as qualify_gnome_settings_daemon
        qualify_gnome_settings_daemon(ROOT)
    if name=='gdm':
        from qualify_gdm import qualify as qualify_gdm
        qualify_gdm(ROOT)
    if name=='libnma':
        from qualify_libnma import qualify as qualify_libnma
        qualify_libnma(ROOT)
    if name=='networkmanager':
        from qualify_networkmanager import qualify as qualify_networkmanager
        qualify_networkmanager(ROOT)
    if name=='libndp':
        from qualify_libndp import qualify as qualify_libndp
        qualify_libndp(ROOT)
    if name=='geoclue':
        from qualify_geoclue import qualify as qualify_geoclue
        qualify_geoclue(ROOT)
    if name=='libgweather':
        from qualify_libgweather import qualify as qualify_libgweather
        qualify_libgweather(ROOT)
    if name=='gweather-locations':
        from qualify_gweather_locations import qualify as qualify_gweather_locations
        qualify_gweather_locations(ROOT)
    if name=='geocode-glib':
        from qualify_geocode_glib import qualify as qualify_geocode_glib
        qualify_geocode_glib(ROOT)
    if name=='ibus':
        from qualify_ibus import qualify as qualify_ibus
        qualify_ibus(ROOT)
    if name=='vala':
        from qualify_vala import qualify as qualify_vala
        qualify_vala(ROOT)
    if name=='unicode-ucd':
        from qualify_unicode_ucd import qualify as qualify_unicode_ucd
        qualify_unicode_ucd(ROOT)
    if name=='glib-networking':
        from qualify_glib_networking import qualify as qualify_glib_networking
        qualify_glib_networking(ROOT)
        from gio_network_resources import prepare as prepare_gio_network
        prepare_gio_network()
    if name=='gcr3':
        from qualify_gcr3 import qualify as qualify_gcr3
        qualify_gcr3(ROOT)
    if name=='libsecret':
        from qualify_libsecret import qualify as qualify_libsecret
        qualify_libsecret(ROOT)
    if name=='gcr':
        from qualify_gcr import qualify as qualify_gcr
        qualify_gcr(ROOT)
    if name=='p11-kit':
        from qualify_p11_kit import qualify as qualify_p11_kit
        qualify_p11_kit(ROOT)
    if name=='libtasn1':
        from qualify_libtasn1 import qualify as qualify_libtasn1
        qualify_libtasn1(ROOT)
    if name=='gnome-session':
        from qualify_gnome_session import qualify as qualify_gnome_session
        qualify_gnome_session(ROOT)
    if name=='upower':
        from prepare_upower_native import qualify as qualify_upower
        from accept_upower_native import validate as validate_upower_native
        qualify_upower()
        acceptance=json.loads((log/'upower-native-acceptance-1.json').read_text())
        assert acceptance['state']=='native-linux-service-qualified' and validate_upower_native(acceptance['proof'])==acceptance['summary']
    if name=='accountsservice':
        from qualify_accountsservice_stage import qualify as qualify_accountsservice
        from accept_accountsservice_native import validate as validate_accountsservice_native
        qualify_accountsservice(ROOT)
        acceptance=json.loads((log/'accountsservice-native-acceptance-1.json').read_text())
        assert acceptance['state']=='native-real-accounts-qualified'
        assert validate_accountsservice_native(acceptance['proof'])==acceptance['summary']
    if name=='dconf':
        from qualify_dconf import qualify as qualify_dconf
        qualify_dconf(ROOT)
    if name=='python-dbusmock':
        from qualify_dbusmock import qualify as qualify_dbusmock
        qualify_dbusmock(ROOT)
    if name=='duktape':
        from qualify_duktape import qualify as qualify_duktape
        qualify_duktape(ROOT)
    if name=='linux-pam':
        from qualify_pam import qualify as qualify_pam
        qualify_pam(ROOT,log)
    if name=='gjs':
        from qualify_gjs import qualify as qualify_gjs
        qualify_gjs(ROOT,log)
    if name=='mozjs':
        from qualify_mozjs_security import qualify as qualify_mozjs
        qualify_mozjs(ROOT)
    if name=='gtksourceview':
        from qualify_gtksource_patch import qualify
        qualify(ROOT,log)
    assert name==sys.argv[1], 'Package identity changed during qualification'
    source = Path('/mnt/lfs/sources/phase2/work') / (name+'-1') / 'stage'
    if name=='cups':source=Path('/mnt/lfs/sources/phase2/work/cups-layout-1/stage')
    if name=='gcr3':source=Path('/mnt/lfs/sources/phase2/work/gcr3-patched-1/stage')
    if name=='polkit':source=Path('/mnt/lfs/sources/phase2/work/polkit-full-1/stage')
    if name=='dconf':source=Path('/mnt/lfs/sources/phase2/work/dconf-vendored-1/stage')
    if name=='mozjs':source=Path('/mnt/lfs/sources/phase2/work/mozjs-security-1/stage')
    if name=='linux-pam':source=Path('/mnt/lfs/sources/phase2/work/pam-1/stage')
    if name=='gtksourceview':source=Path('/mnt/lfs/sources/phase2/work/gtksourceview-patched-1/stage')
    if name=='libxml2-python':source=Path('/mnt/lfs/sources/phase2/work/libxml2-1/python-binding-1/stage')
    assert not (source/'.toddy-retired.json').exists(),'Stage retired under verified archive custody; reuse the native package, no promotion replay'
    before = inspect_stage(source)
    assert required in before['entries'], 'Missing declared payload'
    destination = Path('/mnt/lfs/sources/stage') / ('phase2-'+name)
    if name in ('mitkrb','libqmi','modemmanager'):
        from native_scratch_staging import destination as scratch_destination
        destination=scratch_destination(name)
    if name=='libxslt' and destination.exists():
        prior=json.loads((log.parent/'build/b02-libxslt-install.failed.json').read_text())
        assert prior['recipe_exit']==1 and prior['postcheck_exit'] is None and prior['changed_paths']==0
        assert "NameError: name 'work' is not defined" in (log.parent/'build/b02-libxslt-install.log').read_text()
        assert not Path('/var/cache/toddy/packages/libxslt_1.1.45-1+toddy1_amd64.deb').exists()
        absent=subprocess.run(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status}','libxslt'],capture_output=True,text=True)
        assert absent.returncode==1
        current=inspect_stage(destination)['entries']
        assert all(current[k]==v for k,v in before['entries'].items())
        assert set(current)-set(before['entries'])=={'usr/share/doc/libxslt'}
        assert (destination/'usr/share/doc/libxslt').is_dir() and not list((destination/'usr/share/doc/libxslt').iterdir())
    elif name in ('lua','libcanberra') and destination.exists():
        # The first transaction stopped while collecting embedded legal notices,
        # before archive creation/dpkg. Resume that proven staging state only.
        prior=json.loads((log.parent/('build/b02-'+name+'-install.failed.json')).read_text())
        assert prior['recipe_exit']==1 and prior['postcheck_exit'] is None
        assert 'No upstream notice found; review before packaging' in (log.parent/('build/b02-'+name+'-install.log')).read_text()
        assert not (Path('/var/cache/toddy/packages')/(name+'_'+version+'-1+toddy1_amd64.deb')).exists()
        assert not (Path('/var/log/toddy/packages')/(name+'_'+version+'-1+toddy1_amd64.json')).exists()
        state=subprocess.run(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status}',name],capture_output=True,text=True)
        assert state.returncode in (0,1) and state.stdout.strip()!='install ok installed'
        current=inspect_stage(destination)['entries']
        assert all(current[k]==v for k,v in before['entries'].items())
        allowed={'usr/share/doc','usr/share/doc/'+name,'usr/share/doc/'+name+'/source-notices','usr/share/doc/'+name+'/source-notices/index.json'}
        assert set(current)-set(before['entries'])<=allowed
        notice=json.loads((destination/('usr/share/doc/'+name+'/source-notices/index.json')).read_text())
        assert all(not r['notices'] for r in notice['sources'])
    else:
        if name in ('mitkrb','libqmi','modemmanager'):
            assert destination.is_dir() and not list(destination.iterdir())
        else:
            assert not destination.exists(), 'Reconcile existing stage; no replay'
        shutil.copytree(source, destination, symlinks=True,dirs_exist_ok=name in ('mitkrb','libqmi','modemmanager'))
        assert inspect_stage(destination) == before
    (log / (name+'-stage.json')).write_text(json.dumps(before, indent=2)+'\n')
    if name=='cups':
        from cups_native import promote
        promote(destination)
    if name=='gnome-terminal':
        addon=destination/'usr/share/metainfo/org.gnome.Terminal.Nautilus.metainfo.xml'
        assert addon.is_file();addon.unlink()
    if name=='gnome-shell':
        # Upstream installs this launcher even with extensions_app=false.
        launcher=destination/'usr/share/applications/org.gnome.Shell.Extensions.desktop'
        assert launcher.is_file();excluded=hashlib.sha256(launcher.read_bytes()).hexdigest();launcher.unlink()
        (log/'gnome-shell-production-selection.json').write_text(json.dumps({'scope':'Minimal Shell, no dead launcher for optional unbuilt Extensions app; no owner preferences changed. Network portal sign-in follows upstream browser fallback.','excluded_disabled_app_launcher_sha256':excluded},indent=2)+'\n')
    if name=='gdm':
        import configparser
        config=destination/'etc/gdm/custom.conf';before_config=hashlib.sha256(config.read_bytes()).hexdigest()
        conf=configparser.ConfigParser();conf.optionxform=str;conf.read(config)
        for key in ['AutomaticLoginEnable','TimedLoginEnable','InitialSetupEnable']:conf.set('daemon',key,'false')
        with config.open('w') as f:conf.write(f)
        group=destination/'usr/lib/sysusers.d/gdm.conf';group.parent.mkdir(parents=True,exist_ok=True);assert not group.exists();group.write_text('g gdm 21\n')
        temp=destination/'usr/lib/tmpfiles.d/gdm.conf';temp.parent.mkdir(parents=True,exist_ok=True);assert not temp.exists();temp.write_text('d /var/lib/gdm 0755 root root -\n')
        state=destination/'var/lib/gdm';state.mkdir(parents=True,exist_ok=True);state.chmod(0o755)
        (log/'gdm-production-selection.json').write_text(json.dumps({'scope':'Current GDM50 dynamic userdb greeters; group21 only, no obsolete static UID/home. Root0755 persistent base, volatile per-greeter homes remain upstream managed. Factory automatic/timed/optional GNOME initial setup disabled; native installer creates owner. No daemon activation or global NSS/PAM edits.','custom_conf_before_sha256':before_config,'custom_conf_after_sha256':hashlib.sha256(config.read_bytes()).hexdigest()},indent=2)+'\n')
    if name=='geoclue':
        import re
        config=destination/'etc/geoclue/geoclue.conf';before_config=config.read_bytes()
        after_config=re.sub(rb'(?m)^(#url=[^\n]*[?&]key=)[^\s]+$',lambda m:m[1]+b'YOUR_KEY',before_config);config.write_bytes(after_config)
        sysusers=destination/'usr/lib/sysusers.d/geoclue-sysusers.conf';assert sysusers.read_text()=='u geoclue - - /var/lib/geoclue\n'
        sysusers.write_text('u geoclue 30 - /var/lib/geoclue /bin/false\n')
        excluded={}
        for rel in ['usr/share/applications/geoclue-where-am-i.desktop','usr/libexec/geoclue-2.0/demos/where-am-i']:
            path=destination/rel;excluded[rel]=hashlib.sha256(path.read_bytes()).hexdigest();path.unlink()
        (log/'geoclue-production-selection.json').write_text(json.dumps({'scope':'Keep full service/library; omit upstream demonstration application, fixed locked service ID30 and remove bundled public provider-key examples from comments only. No actual owner config or provider endpoint edited.','excluded_demo':excluded,'config_before_sha256':hashlib.sha256(before_config).hexdigest(),'config_after_sha256':hashlib.sha256(after_config).hexdigest()},indent=2)+'\n')
    if name=='glib-networking':
        # Compiler-local discovery contains only network modules, while the
        # installed resource also serves DConf. Never package/overwrite it.
        (destination/'usr/lib/gio/modules/giomodule.cache').unlink()
    if name=='nss':
        # Original test modules stay in immutable qualification evidence only.
        # The book's glob also matches them after gtests are enabled.
        removed={}
        for filename in ['libpkcs11testmodule.so','libnssckbi-testlib.so']:
            path=destination/'usr/lib'/filename;assert path.is_file() and not path.is_symlink()
            removed['usr/lib/'+filename]=hashlib.sha256(path.read_bytes()).hexdigest();path.unlink()
        doc=destination/'usr/share/doc/nss';(doc/'patches').mkdir(parents=True)
        patch=json.loads((ROOT/'config/phase2/nss-patches.lock.json').read_text())
        shutil.copy2(ROOT/patch['patch_file'],doc/'patches'/Path(patch['patch_file']).name)
        shutil.copy2('/mnt/lfs/sources/nss-standalone-1.patch',doc/'patches/nss-standalone-1.patch')
        (doc/'source-patch.json').write_text(json.dumps(patch,indent=2)+'\n')
        (doc/'README.Toddy').write_text('Frozen NSS3.126/shared dynamic SDK and certutil/nss-config/pk12util. Required book standalone patch only updates final manifest context for this source; same five build/install changes, no runtime code patch. Five selected original crypto/DER/API programs2271passes/three upstream disabled cases, not full potentially hanging network suite. Actual SHA256/random/AES-GCM/tamper/refusal/recovery qualified. Two test modules excluded after immutable stage validation; private test databases are never shipped. Upstream bundled roots retained until separately qualified p11-kit/make-ca integration; TLS/trust-store/native GNOME remain separate gates.\n')
        (log/'nss-production-selection.json').write_text(json.dumps({'excluded_test_modules':removed,'unchanged_qualification_stage':True,'root_provider':'Upstream bundled roots; qualified p11-kit/make-ca integration pending'},indent=2)+'\n')
    if name=='polkit':
        acceptance=json.loads((log/'polkit-standard-native-acceptance-1.json').read_text())
        import os
        for virtual,sha in acceptance['summary']['helpers'].items():
            helper=destination/virtual.lstrip('/');assert hashlib.sha256(helper.read_bytes()).hexdigest()==sha and helper.stat().st_mode&0o7777==0o755
            os.chown(helper,0,0);helper.chmod(0o4755)
        rules=destination/'etc/polkit-1/rules.d';assert rules.is_dir() and not list(rules.iterdir());os.chown(rules,0,27);rules.chmod(0o750)
        policy=destination/'etc/pam.d';policy.mkdir(parents=True,exist_ok=True);assert not (policy/'polkit-auth').exists()
        (policy/'polkit-auth').write_text('auth required pam_unix.so\naccount required pam_unix.so\npassword required pam_deny.so\nsession required pam_unix.so\n')
        doc=destination/'usr/share/doc/polkit';(doc/'patches').mkdir(parents=True)
        patch=json.loads((ROOT/'config/phase2/polkit-patches.lock.json').read_text());shutil.copy2(ROOT/patch['patch_file'],doc/'patches'/Path(patch['patch_file']).name)
        (doc/'source-patch.json').write_text(json.dumps(patch,indent=2)+'\n')
        (doc/'README.Toddy').write_text('Frozen127 plus exact ADR0151 typed-subject decoder correction. Five original native programs/59TAP cases and11actual standard-helper expected outcomes qualified. Two exact root:root4755 binaries only; service root:polkitd0750 rules, locked UID/GID27 account. Required pam_unix auth/account/session, password changes denied; no owner test rules are shipped. Optional helper.socket remains unqualified/unstarted because SUID embedded-agent cookie/UID behavior failed. GNOME permission UI is a separate gate. See ADR0153/0155 and source-patch.json.\n')
    if name=='libxml2':
        wrapper=destination/'usr/bin/xml2-config'
        wrapper.write_text(wrapper.read_text().replace('--static','--shared'))
    if name=='freetype':
        doc=destination/'usr/share/doc/freetype';doc.mkdir(parents=True,exist_ok=True)
        (doc/'README.Toddy').write_text('This software is based in part on the work of the FreeType Team.\nPortions copyright 1996-2026 The FreeType Project (https://freetype.org). All rights reserved.\nFTL license option selected; exact upstream terms in copyright/source-notices.\nSource modifications: enabled gxvalid/otvalid modules and FT_CONFIG_OPTION_SUBPIXEL_RENDERING per BLFS13.1.\nDynamic HarfBuzz loading; optional reference manual not included.\n')
    if name=='libwacom':
        omitted={}
        for relative in ['usr/bin/libwacom-show-stylus','usr/share/man/man1/libwacom-show-stylus.1']:
            path=destination/relative
            assert path.is_file() and not path.is_symlink()
            assert path.read_bytes()==(work/'compile'/Path(relative).name).read_bytes()
            omitted[relative]=hashlib.sha256(path.read_bytes()).hexdigest();path.unlink()
        (log/'libwacom-runtime-partition.json').write_text(json.dumps({
            'scope':'Omit only optional Python show-stylus CLI/man whose libevdev/pyudev bindings are unavailable. Original source/test stage retained; native C library/tools/database/udev inputs unchanged.',
            'omitted':omitted},indent=2)+'\n')
    if name=='linux-pam':
        # The compiler stage stays unprivileged. Only this authenticated helper
        # in the copied root-owned promotion stage receives its exact policy.
        helper=destination/'usr/sbin/unix_chkpwd'
        assert hashlib.sha256(helper.read_bytes()).hexdigest()=='2176a32b57f8c0ec676503cec517534695e96689f5d29c16e81ff264de600e29'
        assert helper.stat().st_mode & 0o7777 == 0o755
        import os
        os.chown(helper,0,0);helper.chmod(0o4755)
        policy=destination/'etc/pam.d';assert not policy.exists();policy.mkdir(parents=True)
        (policy/'other').write_text(''.join(f'{kind} required pam_deny.so\n' for kind in ['auth','account','password','session']))
        doc=destination/'usr/share/doc/linux-pam';doc.mkdir(parents=True,exist_ok=True)
        patches=json.loads((ROOT/'config/phase2/pam-patches.lock.json').read_text())
        (doc/'patches').mkdir()
        for patch in patches['patches']:shutil.copy2(ROOT/patch['file'],doc/'patches'/Path(patch['file']).name)
        (doc/'security-backports.json').write_text(json.dumps(patches,indent=2)+'\n')
        (doc/'README.Toddy').write_text('Frozen Linux-PAM1.7.2 with nine ordered ADR0126 upstream security backports. Original77unit drivers and native7.1.8 real yescrypt/helper/refusal/lock/recovery7cases passed. Generic other policy denies all four management groups. Optional userdb/NIS/SELinux/audit/libeconf disabled. Shadow, pam_systemd, authenticated session boot and GDM integration remain separate gates. No existing account or password is changed.\n')
    if name=='gcr3':
        doc=destination/'usr/share/doc/gcr3';(doc/'patches').mkdir(parents=True)
        patch=json.loads((ROOT/'config/phase2/gcr3-patches.lock.json').read_text());shutil.copy2(ROOT/patch['patch_file'],doc/'patches'/Path(patch['patch_file']).name)
        (doc/'source-patch.json').write_text(json.dumps(patch,indent=2)+'\n')
        (doc/'README.Toddy').write_text('Frozen3.41.2 C/GTK3 compatibility ABI for GNOME Keyring50, alongside unchanged Gcr4/Gck2. One build-only Meson guard honors disabled SSH agent; no C/crypto changes.43original core programs/native transport/refusal/recovery qualified. Legacy GIR/Vala/docs/SSH-agent omitted. GTK3 native graphical prompt/viewer and shared PGP schema union remain separate gates. Private keygen test SDK never shipped. See source-patch.json and ADR0159.\n')
    if name=='gnome-keyring':
        doc=destination/'usr/share/doc/gnome-keyring';doc.mkdir(parents=True,exist_ok=True)
        (doc/'README.Toddy').write_text('Frozen50.0 production debug-mode=false: test-only service/login/prompter hooks disabled.57original production programs and five original private debug-only fixture programs qualified separately; fixture daemon never shipped. Actual production Secret Service store/read/lock/wrong-master/Stop/restart persistence qualified with ephemeral synthetic data. PAM module loads, but no PAM login policy is enabled by this package. Actual native PAM/GNOME/graphical and shared schema integration remain separate gates. Optional SSH agent/libcap-ng/SELinux omitted via supported options. Book schema path correction preserved in source preparation receipt.\n')
    if name=='ibus':
        doc=destination/'usr/share/doc/ibus';doc.mkdir(parents=True,exist_ok=True)
        (doc/'README.Toddy').write_text('Frozen official tag1.5.34 embeds1.5.34-rc2; native1.5.34~rc2-1+toddy1 preserves and discloses source version. Minimal GTK3/4+Wayland/GI/Unicode/setup/UI profile; XIM/X11 agent, GTK2, Python2, appindicator and optional emoji dict omitted. Seven portable original programs and UTF8/key parser refusal/recovery qualified; actual service, graphical keyboard and shared IM/schema caches remain separate pending gates. Full source/UCD/Unicode3 notices retained. ADR0169 records backend guard and original Xlib fixture link correction.\n')
    if name=='gexiv2':
        doc=destination/'usr/share/doc/gexiv2';doc.mkdir(parents=True,exist_ok=True)
        (doc/'README.Toddy').write_text('Frozen GExiv2 0.16.2 shared GObject/GI/Vala/Python/tools with owned Exiv2 0.28.8. All3 original C/Python programs0 and own real PNG UTF8 metadata/edit/reset/pixel retention/malformed refusal/recovery. XMP title readback includes language marker. No LocalSearch/Nautilus/desktop acceptance.\n')
    if name=='exiv2':
        doc=destination/'usr/share/doc/exiv2';doc.mkdir(parents=True,exist_ok=True)
        from qualify_exiv2 import qualify as qualify_exiv2
        review=qualify_exiv2(ROOT);review.pop('stage')
        (doc/'original-test-review.json').write_text(json.dumps(review,indent=2)+'\n')
        (doc/'README.Toddy').write_text('Frozen0.28.8 local metadata profile with owned Brotli/INI, PNG/JPEG/TIFF/BMFF/video/XMP; network transports/samples/Python bindings unselected. Four original test programs1169nested cases,1159non-skipped/10explicit skips; fifth registered version driver dumps metadata with zero cases; initial disabled-feature/private-fixture failures retained. Own UTF8 PNG EXIF edit/read/reset/pixel retention/corrupt refusal and valid XMP/external entity201 rejection/canary not read/recovery passed, all92ELFs/55stage files unchanged after probe correction. Current src/xmp.cpp XMLValidator rejects DOCTYPE before Adobe SDK; no global Expat-vulnerability fix, GExiv2/LocalSearch/GUI or remote-transport acceptance. Source/XMP SDK full notices retained. ADR0203.\n')
    if name in ('brotli','inih'):
        doc=destination/'usr/share/doc'/name;doc.mkdir(parents=True,exist_ok=True)
        (doc/'README.Toddy').write_text('Frozen BLFS13.1 prerequisite, isolated source build and all selected tarball original cases; actual installed local UTF8/refusal/recovery tests. No Exiv2/full desktop acceptance. Brotli external downloaded corpus/Python bindings omitted; inih C+INIReader default bounded stack parser selected. ADR0202.\n')
    if name=='blueprint-compiler':
        doc=destination/'usr/share/doc/blueprint-compiler';doc.mkdir(parents=True,exist_ok=True)
        from qualify_blueprint_compiler import qualify as qualify_blueprint_compiler
        review=qualify_blueprint_compiler(ROOT);review.pop('stage_sha256')
        (doc/'original-test-review.json').write_text(json.dumps(review,indent=2)+'\n')
        (doc/'README.Toddy').write_text('Frozen0.22.2 build-only GTK UI compiler SDK, Python bytecompilation/docs omitted. Four original tokenizer/formatter cases and original linter method/15fixtures passed; first linter r+ source PermissionError preserved, identical private test copy used with source/private bytes unchanged. Generated build outputs retained, no Ninja/approved-test replay. Actual CLI UTF8 GTK XML/invalid property refusal/two recovery cycles passed. Full Gtk.Builder/deprecation display suite deferred; no widget/native GNOME acceptance. Build SDK excluded from final runtime image unless a separately selected consumer needs it. ADR0200.\n')
    if name=='glycin-gtk4':
        doc=destination/'usr/share/doc/glycin-gtk4';doc.mkdir(parents=True,exist_ok=True)
        from qualify_glycin_gtk4 import qualify as qualify_glycin_gtk4
        (doc/'native-conversion-proof.json').write_text(json.dumps(qualify_glycin_gtk4(ROOT),indent=2)+'\n')
        (doc/'README.Toddy').write_text('GTK4 companion API2.1.0 from frozen Glycin2.1.5 bundle, linked against existing owned core/loaders. Separate offline locked release/ltofalse build, no core/loaders rebuild. Native7.1.8/Systemd/UID101/BWRAP/default installed loader paths: four PNG-SVG-to-GDK-texture pixel-preserving PNG roundtrips, two malformed refusals/two recoveries passed. All five stage files/core hashes unchanged. Original broad Python suite unexecuted, no display/widget/GNOME/full desktop acceptance. Full frozen source/vendor/toolchain notices retained. ADR0199.\n')
    if name=='tinysparql':
        doc=destination/'usr/share/doc/tinysparql';doc.mkdir(parents=True,exist_ok=True)
        from qualify_tinysparql import qualify as qualify_tinysparql
        (doc/'original-test-review.json').write_text(json.dumps(qualify_tinysparql(ROOT),indent=2)+'\n')
        (doc/'README.Toddy').write_text('Frozen3.11.1 ICU/GI/Vala/Soup3 production debugfalse/testsfalse; unsafe SQLite guard retained, foundation SQLite3.53.4 unchanged. Separate debug original tests:29programs and487core cases passed, four exact SQLite17digit-vs15digit lexical goldens remain failed/reviewed; independent production typed arithmetic/lossless roundtrip four cases passed. Original source/goldens unchanged.17functional graphical-session programs compiled/deferred, no desktop/indexer/portal/permission/cancellation acceptance. Optional docs/man/stemmer/Avahi/completion omitted; no endpoint/service started during package installation. ADR0198.\n')
    if name=='libxslt':
        doc=destination/'usr/share/doc/libxslt';doc.mkdir(parents=True,exist_ok=True)
        from qualify_libxslt import review
        (doc/'original-test-review.json').write_text(json.dumps(review(source.parent/'original-tests.log',Path('/mnt/lfs/sources/phase2/inputs/libxslt-1.1.45')),indent=2)+'\n')
        (doc/'README.Toddy').write_text('Build-only xsltproc SDK for authenticated source UI transformations; not a GNOME Terminal runtime dependency. Core driver reports748cases/noerrors; four original DocBook golden whitespace differences remain unaccepted. No complete original-suite/general CLI parser sandbox or DocBook rendering qualification. Use bounded explicit nonet/nowrite/nomkdir/maxdepth/maxvars for selected fixtures. See original-test-review.json.\n')
    archives=[archive]
    if name=='mitkrb':
        archives += [row['filename'] for row in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if row['name'] in ('mitkrb-upstream-fix','mitkrb-security-fix','mitkrb-openssl4-fixes')]
    if name=='cracklib':archives.append('cracklib-words-2.10.3.xz')
    if name=='editorconfig':archives.append('editorconfig-core-test-d91029bdf1e3e0307714afe0d2cde7ba6fd208ab.tar.gz')
    if name=='aspell':archives.append('aspell6-en-2020.12.07-0.tar.bz2')
    if name=='glycin-gtk4':archives+=['glycin-2.1.5-vendor.tar.gz','rustc-1.97.1-src.tar.xz']
    if name=='vte':archives+=['fmt-12.2.0.tar.gz','fast_float-8.2.10.tar.gz']
    if name=='ibus':archives+=['UCD-17.0.0.zip','Unicode-License-3.0.txt']
    if name=='unicode-ucd':archives.append('Unicode-License-3.0.txt')
    if name=='nss':archives.append('nss-standalone-1.patch')
    if name=='dconf':archives.append('gvdb-4758f6fb7f889e074e13df3f914328f3eecb1fd3.tar.gz')
    if name=='mozjs':archives.append('spidermonkey-140.14.0-python_3.14_fixes-1.patch')
    if name=='gtksourceview':archives.append('gtksourceview-5.20.0-duplicate-capture-1.patch')
    if name=='docutils':archives.append('flit_core-3.12.0.tar.gz')
    if name=='cbindgen':archives.append('cbindgen-0.29.4-vendor.tar.gz')
    if name=='libcanberra':archives.append('libcanberra-0.30-wayland-1.patch')
    if name in ('shared-mime-info','llvm'):
        extra_name='xdgmime-tests' if name=='shared-mime-info' else 'llvm-upstream-fix'
        row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==extra_name)
        archives.append(row['filename'])
    if name=='libdisplay-info':
        extra=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='hwdata')
        archives.append(extra['filename'])
    if name=='libei':
        extra=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='munit-test-dependency')
        archives.append(extra['filename'])
    if name=='lua':
        archives += [r['filename'] for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name'] in ('lua-shared-library-patch','lua-test-suite')]
    write_copyright(destination, name, archives)
    if name=='gnome-terminal':
        doc=destination/'usr/share/doc/gnome-terminal';common=ROOT/'LICENSES/third-party/LGPL-2.1.txt'
        shutil.copyfile(common,doc/'LGPL-2.1.txt')
        with (doc/'copyright').open('ab') as f:f.write(b'\nBundled per-file LGPL2.1 terms; complete text:\n'+common.read_bytes())
    if name=='gdm':
        doc=destination/'usr/share/doc/gdm';license_text=ROOT/'LICENSES/GFDL-1.3.txt'
        assert hashlib.sha256(license_text.read_bytes()).hexdigest()=='110535522396708cea37c72a802c5e7e81391139f5f7985631c93ef242b206a4'
        shutil.copyfile(license_text,doc/'GFDL-1.3.txt')
        with (doc/'copyright').open('ab') as f:f.write(b'\nDocumentation permits GFDL1.1 or later without invariant/cover texts; full selected GFDL1.3 text:\n'+license_text.read_bytes())
    if name=='libgweather':
        doc=destination/'usr/share/doc/libgweather';common=ROOT/'LICENSES/third-party/LGPL-2.1.txt'
        shutil.copyfile(common,doc/'LGPL-2.1.txt')
        with (doc/'copyright').open('ab') as notice:notice.write(b'\nCommon GNU LGPL2.1 full text retained from repository LICENSES/third-party/LGPL-2.1.txt:\n'+common.read_bytes())
    if name=='gtksourceview':
        document=destination/'usr/share/doc/gtksourceview'
        shutil.copyfile('/mnt/lfs/sources/gtksourceview-5.20.0-duplicate-capture-1.patch',document/'duplicate-capture.patch')
        (document/'README.Toddy').write_text('Source-backed private duplicate-capture fix: ADR0146. Original6case consumer reproduced5failures; corrected6cases and5original syntax cases passed. Original regex3cases passed under native7.1.8/Mutter. Full editor/GNOME integration is a separate B02 gate. Original invalidUTF8 file.cir and known GDB grammar remain unqualified. Upstream full legal notices retained; downstream derivative patch follows upstream LGPL terms.\n')
    if name=='mozjs':
        (destination/'usr/share/doc/mozjs/README.Toddy').write_text('Explicit same-family security overlay140.17.0, ADR0147. Original API/JIT and real dynamic consumer qualified; detached SIGINT case reconciled by one unchanged foreground-disposition test, with original aggregate failure preserved. Main-suite retained baseline diagnostics are NOT passing tests or full Intl qualification. Baseline bundles ICU77.1; system ICU78.3 differs from Unicode16/generated locale/calendar/timezone fixtures, and four compound-unit tests report functional errors. Exact diagnostics/case counts retained in release evidence. Original source-archive VCS-dependent message checker remains unavailable; strict ASCII property verified separately. No browser/full GNOME/hardware acceptance. Full source legal notices retained.\n')
    if name=='gjs':
        (destination/'usr/share/doc/gjs/README.Toddy').write_text('Pinned GJS1.88.1: original two C drivers202cases passed; actual native7.1.8/Mutter remaining78original programs OK/2741passed cases/147upstream pending skips. Skips remain unqualified, not passes. Native C/CLI/GI/event/refusal/recovery qualified; full GNOME session and product interaction remain separate B02 gates. Profiler/installed test payload omitted for minimal runtime; full exact source legal notices retained.\n')
    if name=='duktape':
        (destination/'usr/share/doc/duktape/README.Toddy').write_text('Frozen2.7.0 normal/debug shared policy-engine profile. Both bytecode load/dump APIs disabled using supported DUK_USE_BYTECODE_DUMP_SUPPORT option; fail unsupported. Book O2 and explicit self-contained libm link. Original hello and15own native checks per library passed. Full generic ECMAScript conformance and Polkit authorization remain separate qualifications. See ADR0150.\n')
    source_args=[arg for item in archives for arg in ['--source',item]]
    if name=='llvm':
        runtime=destination.with_name('phase2-llvm-runtime')
        partition=split_runtime(destination,runtime)
        write_copyright(runtime,'llvm-runtime',archives)
        (log/'llvm-runtime-partition.json').write_text(json.dumps(partition,indent=2)+'\n')
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'llvm-runtime',
                        version+'-1+toddy1',str(runtime),*source_args,
                        '--recipe','scripts/build/phase2/llvm-install.sh',
                        '--depends','glibc (>= 2.44-1), gcc (>= 16.2.0-1), libffi (>= 3.8.0-1), zlib (>= 1.3.2-1), zstd (>= 1.5.7-1)',
                        '--install'],cwd=ROOT,check=True)
    conffiles=[]
    if name=='cups':conffiles=[arg for file in sorted((destination/'etc/cups').iterdir()) if file.is_file() for arg in ['--conffile','/'+str(file.relative_to(destination))]]
    if name=='libpwquality':conffiles=['--conffile','/etc/security/pwquality.conf']
    if name=='vte':conffiles=['--conffile','/etc/profile.d/vte.sh','--conffile','/etc/profile.d/vte.csh']
    if name=='gdm':conffiles=[v for n in ['custom.conf'] for v in ['--conffile','/etc/gdm/'+n]]+[v for n in ['gdm-autologin','gdm-launch-environment','gdm-fingerprint','gdm-smartcard','gdm-password'] for v in ['--conffile','/etc/pam.d/'+n]]
    if name=='geoclue':conffiles=['--conffile','/etc/geoclue/geoclue.conf']
    if name=='ibus':conffiles=['--conffile','/etc/dconf/profile/ibus','--conffile','/etc/dconf/db/ibus.d/00-upstream-settings']
    if name=='polkit':conffiles=['--conffile','/etc/pam.d/polkit-auth']
    if name=='linux-pam':conffiles=['--conffile','/etc/pam.d/other']
    if name in ('fontconfig','llvm','rustc','at-spi2-core','modemmanager'):
        for relative,row in before['entries'].items():
            if relative.startswith('etc/') and 'sha256' in row: conffiles+=['--conffile','/'+relative]
    subprocess.run([sys.executable, str(ROOT/'scripts/build/stage_package.py'), name,
                    version+('-1+toddy2' if name in ('linux-pam','gnome-settings-daemon','gnome-terminal','gsound','colord-gtk') else '-1+toddy1'), str(destination), *source_args,
                    '--recipe', 'scripts/build/phase2/'+name+'-install.sh',
                    '--depends', depends, '--install', *conffiles,
                    *(['--architecture','all'] if name in ('unicode-ucd','fast-float','blueprint-compiler') else [])], cwd=ROOT, check=True)
    if name=='glib-networking':
        from gio_network_resources import finish as finish_gio_network
        finish_gio_network()
