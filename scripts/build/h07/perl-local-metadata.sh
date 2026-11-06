#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-perl-html-tagset.success.json ]]
python3 /opt/toddy-build/scripts/build/upgrade_native_metadata.py --only perl-html-tagset
