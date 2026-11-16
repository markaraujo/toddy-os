#!/bin/bash
set -euo pipefail
exec python3 /opt/toddy-build/scripts/build/phase2/voice_process_reconcile.py install-catalog
