#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/upgrade_native_metadata.py
python3 /opt/toddy-build/scripts/build/finalize_directory_ownership.py --apply
