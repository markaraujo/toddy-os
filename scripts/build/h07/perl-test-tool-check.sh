#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $# == 1 ]]
module=$(python3 - "$1" <<'PY'
import json,sys
r=next(r for r in json.load(open('/opt/toddy-build/config/native-perl-test-tools.lock.json'))['components'] if r['package']==sys.argv[1]);print(r['probe_module'])
PY
)
chroot "$LFS" /usr/bin/env -i HOME=/root PATH=/usr/bin:/usr/sbin LC_ALL=C \
 /bin/bash -s -- "$module" "$1" <<'INNER'
set -euo pipefail
fixture=$(mktemp -d /tmp/toddy-perl-module.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cd "$fixture"
# require loads the real module/XS without enabling Devel::Cover instrumentation
# for the probe itself. The unchanged upstream suites exercise normal imports.
loaded=$(perl -e '
 my $module=shift;
 die "Invalid module name" unless $module =~ /\A[A-Za-z_]\w*(?:::\w+)*\z/;
 $module =~ s!::!/!g; $module .= ".pm";
 require $module;
 print $INC{$module}, "\n";
' "$1")
[[ $loaded == /* ]]
owner=$(dpkg-query -S "$loaded")
if [[ $owner != "$2: $loaded" ]]; then
 printf 'Native Perl provider mismatch; expected %s, observed %s\n' "$2" "$owner" >&2
 exit 1
fi
printf 'Native Perl module loaded from installed package %s: %s\n' "$2" "$loaded"
INNER
