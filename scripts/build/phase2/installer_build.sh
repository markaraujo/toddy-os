#!/bin/bash
# Compiler-side only, invoked by qualified isolated.sh as UID101.
set -euo pipefail
[[ $(id -u) == 101 && -r /src/installer_build.py ]]
exec /usr/bin/python3 -I /src/installer_build.py
