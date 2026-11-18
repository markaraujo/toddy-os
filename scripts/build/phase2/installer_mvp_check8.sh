#!/bin/bash
# Fixed installer8/version6 for exact selected package cache custody.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/installer_mvp_native.py postcheck8
