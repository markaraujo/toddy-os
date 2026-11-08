#!/bin/bash
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py freetype
chroot /mnt/lfs /usr/sbin/ldconfig
