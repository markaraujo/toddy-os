#!/bin/bash
# Invoke only under run_step.py; retains full-root native transaction evidence.
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/qtbase_wayland_native.py install
