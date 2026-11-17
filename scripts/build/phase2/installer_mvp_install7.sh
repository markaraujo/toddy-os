#!/bin/bash
# Fixed installer7/version5: declared generated-directory ownership correction.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/installer_mvp_native.py install7
