#!/bin/bash
set -euo pipefail
# Reversible test payload for runner semantics, never a release component.
printf 'runner probe\n' > /mnt/lfs/var/toddy-runner-probe
