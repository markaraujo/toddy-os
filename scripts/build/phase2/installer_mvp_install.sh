#!/bin/bash
# Revision4 external producer; frozen compile3/helper remain unchanged.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/installer_mvp_native.py install
