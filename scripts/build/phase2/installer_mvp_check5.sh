#!/bin/bash
# Fixed installer5 revision3; retain actual installer4 and compile3 unchanged.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/installer_mvp_native.py postcheck5
