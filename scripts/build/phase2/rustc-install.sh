#!/bin/bash
# Build SDK only; no automatic inclusion in the offline/live image.
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py rustc
