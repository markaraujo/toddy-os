#!/bin/bash
# Test-only endpoint override. Preserve the original daemon config and policy.
set -euo pipefail
[[ $(id -u) == 101 && ${XDG_RUNTIME_DIR:-} == /var/tmp/toddy-localsearch-* ]]
case "$XDG_RUNTIME_DIR" in *[!a-zA-Z0-9_./-]*) exit 64 ;; esac
[[ -d $XDG_RUNTIME_DIR && ! -L $XDG_RUNTIME_DIR ]]
[[ $(realpath -e -- "$XDG_RUNTIME_DIR") == "$XDG_RUNTIME_DIR" && $(stat -c %u -- "$XDG_RUNTIME_DIR") == 101 ]]
exec /usr/bin/dbus-daemon "$@" "--address=unix:tmpdir=$XDG_RUNTIME_DIR"
