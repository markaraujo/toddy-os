#!/bin/bash
# Fixed installer6/version4 after controlled runtime source hash reconciliation.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/installer_mvp_native.py postcheck6
