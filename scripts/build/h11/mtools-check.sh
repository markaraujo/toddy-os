#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h10/require_media_tools.py
cat /opt/toddy-build/scripts/build/h11/mtools-image-check-inner.sh \
 /opt/toddy-build/scripts/build/h11/mtools-image-roundtrip.sh | chroot_run
