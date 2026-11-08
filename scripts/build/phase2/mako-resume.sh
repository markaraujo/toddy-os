#!/bin/bash
# Original job stopped before wheel execution; retain its partial source copy.
set -euo pipefail
[[ $(id -u) == 101 && -d /build/source && ! -e /build/source-permission-failed-1 ]]
[[ ! -e /build/wheels && ! -e /stage/usr ]]
[[ -r /src/doc/build/changelog.rst ]]
mv /build/source /build/source-permission-failed-1
exec bash /src/toddy-build.sh
