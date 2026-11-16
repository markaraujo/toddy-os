#!/bin/bash
# First package only, invoked by run_step's native full-root transaction.
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/calamares_native.py install
