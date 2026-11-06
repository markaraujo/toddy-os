#!/bin/bash
# Preserve archive bytes while checking ordinary printf/trap behavior separately.
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-bash-recovery.success.json ]]
[[ -z $(dpkg --root="$LFS" --verify bash) ]]
