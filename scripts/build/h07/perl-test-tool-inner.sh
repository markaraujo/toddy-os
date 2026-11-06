#!/bin/bash
set -euo pipefail
package=$1
source_directory=$2
cd "/sources/$source_directory"
test ! -e "/sources/stage/$package"
mkdir -p "/sources/evidence/h07-$package"
perl Makefile.PL INSTALLDIRS=vendor </dev/null
make
chown -R tester:tester .
su tester -c 'make test' 2>&1 | tee "/sources/evidence/h07-$package/check.log"
make DESTDIR="/sources/stage/$package" install
mkdir -p "/sources/stage/$package/usr/share/doc/$package"
# Retain original distribution notices, including module-embedded license POD.
for file in LICENSE LICENSE.md LICENCE COPYING README README.md META.json; do
 if [[ -f $file ]]; then cat "$file" >> "/sources/stage/$package/usr/share/doc/$package/copyright"; fi
done
cat /usr/share/doc/perl/copyright >> "/sources/stage/$package/usr/share/doc/$package/copyright"
