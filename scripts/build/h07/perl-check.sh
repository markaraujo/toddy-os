#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' perl) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
perl -Mthreads -MCompress::Raw::Zlib -MCompress::Raw::Bzip2 -MGDBM_File -e 'print "PERL_NATIVE_OK\n"'
perl -MConfig -e 'die "no shared libperl" unless $Config{useshrplib} eq "true"; die "no threads" unless $Config{usethreads} eq "define";'

INNER
