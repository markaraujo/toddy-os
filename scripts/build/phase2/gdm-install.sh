#!/bin/bash
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py gdm
python3 /opt/toddy-build/scripts/build/phase2/initialize_gdm_group.py
