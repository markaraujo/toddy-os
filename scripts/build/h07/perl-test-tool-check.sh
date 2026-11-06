#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $# == 1 ]]
module=$(python3 - "$1" <<'PY'
import json,sys
r=next(r for r in json.load(open('/opt/toddy-build/config/native-perl-test-tools.lock.json'))['components'] if r['package']==sys.argv[1]);print(r['probe_module'])
PY
)
chroot "$LFS" /usr/bin/env -i HOME=/root PATH=/usr/bin:/usr/sbin LC_ALL=C \
 /usr/bin/perl -M"$module" -e 'print "Native Perl module loaded successfully\n"'
