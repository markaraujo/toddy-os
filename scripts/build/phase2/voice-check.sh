#!/bin/bash
# Dedicated native builder only; this entry point never downloads or opens audio.
set -euo pipefail
[[ $# == 2 ]] || exit 64
exec python3 /opt/toddy-build/scripts/build/phase2/voice_native.py check "$1" "$2"
