#!/bin/bash
# Only under run_step.py: native package intent/journal and real postcheck.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/installer_native.py install
