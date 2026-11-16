#!/bin/bash
# Guest coordinator only; install/check use the owned run_step full-root transaction.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/pipewire_tools_native.py prepare
