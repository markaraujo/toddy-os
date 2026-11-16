#!/bin/bash
# Native byte/ownership/dependency and offscreen consumer checks, no GUI claim.
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/calamares_native.py postcheck
