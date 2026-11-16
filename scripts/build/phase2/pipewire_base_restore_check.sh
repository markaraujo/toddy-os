#!/bin/bash
# Exact archived-base recovery only under a NEW full-root run_step transaction.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/pipewire_base_restore.py postcheck
