#!/bin/bash
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/cups_isolation.py "$@"
