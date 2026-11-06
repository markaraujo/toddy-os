#!/bin/bash
set -euo pipefail
test "$(cat /mnt/lfs/var/toddy-runner-probe)" = 'runner probe'
