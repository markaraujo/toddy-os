#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h11/require_gate.py
chroot_run < /opt/toddy-build/scripts/build/h11/mtools-image-check-inner.sh
