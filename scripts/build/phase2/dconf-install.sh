#!/bin/bash
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py dconf
python3 /opt/toddy-build/scripts/build/phase2/dconf_native_resources.py
