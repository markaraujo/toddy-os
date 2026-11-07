#!/bin/bash
# Recovery of existing directory metadata after accepted native repackaging.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/finalize_directory_ownership.py --apply
