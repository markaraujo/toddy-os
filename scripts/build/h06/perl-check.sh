#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
perl -e 'die "wrong version" unless $^V eq v5.44.0; print "Native Perl 5.44.0 works\n";'
INNER
