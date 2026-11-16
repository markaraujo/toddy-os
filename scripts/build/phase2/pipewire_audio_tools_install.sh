#!/bin/bash
# Standalone tool package only under a NEW full-root native transaction.
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/pipewire_audio_tools.py install
