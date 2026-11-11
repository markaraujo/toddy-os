#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 ]]
[[ $# == 0 && ! -e /build/mozconfig && ! -e /build/obj ]]
[[ $(cat /src/browser/config/version.txt) == 153.7.0 ]]
attempt=1
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
export PATH=/tools/nasm/usr/bin:/usr/bin:/usr/sbin
export CC=clang CXX=clang++
export WASM_CC=/tools/wasi-sdk/bin/clang WASM_CXX=/tools/wasi-sdk/bin/clang++
export MOZCONFIG=/build/mozconfig MOZBUILD_STATE_PATH=/build/mozbuild
export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE=none
export CARGO_HOME=/build/cargo-home
unset MOZ_TELEMETRY_REPORTING
mkdir -p "$CARGO_HOME"
cat > "$MOZCONFIG" <<'CONFIG'
# BLFS13.1-systemd Firefox profile with ADR0225 source153.7.0esr security candidate.
# Exact source supports Wayland-only GTK; retain upstream WASM/content sandbox.
ac_add_options --prefix=/usr
ac_add_options --enable-application=browser
ac_add_options --enable-default-toolkit=cairo-gtk3-wayland-only
ac_add_options --disable-bootstrap
ac_add_options --enable-linker=bfd
ac_add_options --with-wasi-sysroot=/tools/wasi-sdk/share/wasi-sysroot
ac_add_options --disable-necko-wifi
ac_add_options --disable-crashreporter
ac_add_options --disable-updater
ac_add_options --disable-debug-symbols
ac_add_options --disable-tests
ac_add_options --enable-rust-simd
ac_add_options --enable-system-ffi
ac_add_options --enable-system-pixman
ac_add_options --with-system-jpeg
# The qualified system PNG lacks APNG. Use this exact Firefox archive's PNG;
# retain its notices/version for browser security review, no foundation upgrade.
ac_add_options --with-system-zlib
ac_add_options --with-system-icu
ac_add_options --with-system-nspr
ac_add_options --with-system-nss
mk_add_options MOZ_OBJDIR=/build/obj
mk_add_options MOZ_MAKE_FLAGS=-j6
MOZ_APP_REMOTINGNAME=firefox
CONFIG
# No official branding/API key, native-only CPU flags, automatic downloads,
# source mutation, sandbox disabling or installation in this configure slice.
cd /build
/src/mach configure > /build/firefox-configure-$attempt.log 2>&1
