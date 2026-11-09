#!/bin/bash
set -euo pipefail
bash /opt/toddy-build/scripts/build/phase2/pulseaudio-check.sh
bash /opt/toddy-build/scripts/build/phase2/libcanberra-check.sh
