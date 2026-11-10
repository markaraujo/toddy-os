#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py libatasmart
