#!/bin/bash
# Guest-only preparation into a separately identified disposable scratch disk.
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/qtbase_wayland_native.py prepare
