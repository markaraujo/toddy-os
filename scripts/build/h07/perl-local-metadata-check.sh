#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ ! -e $LFS/usr/lib/perl5/5.44/core_perl/perllocal.pod ]]
chroot "$LFS" /usr/bin/dpkg-query -W -f='${Version}\n' perl-html-tagset | grep -Fx '3.24-1+toddy1'
bash /opt/toddy-build/scripts/build/h07/perl-test-tool-check.sh perl-html-tagset
