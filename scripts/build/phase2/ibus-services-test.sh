#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
unshare --mount --net --propagation private python3 /opt/toddy-build/scripts/build/phase2/ibus_native_services.py
