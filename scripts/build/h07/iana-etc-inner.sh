#!/bin/bash
# LFS 13.1-systemd 8.4, staged before native package installation.
set -euo pipefail
cd /sources/iana-etc-20260805
mkdir -p /sources/stage/iana-etc/etc
cp -v services protocols /sources/stage/iana-etc/etc
