#!/bin/bash
# Frozen BLFS13.1 itstool2.0.7; native Python binding is required.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/configure.ac && -d /stage ]]
cp -a /src /build/source
chmod -R u+w /build/source
cd /build/source
autoreconf --force --install --verbose
mkdir /build/compile
cd /build/compile
PYTHON=/usr/bin/python3 /build/source/configure --prefix=/usr
make -j4
make check > /build/upstream-check.log 2>&1
python3 - <<'CATALOG'
from pathlib import Path
assert Path('/src/docbook/docbookx.dtd').is_file()
Path('/build/docbook-catalog.xml').write_text('<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"><rewriteSystem systemIdStartString="http://www.oasis-open.org/docbook/xml/4.5/" rewritePrefix="file:///src/docbook/"/></catalog>\n')
CATALOG
(cd /build/source && XML_CATALOG_FILES=/build/docbook-catalog.xml python3 tests/run_tests.py > /build/upstream-tests.log 2>&1)
make DESTDIR=/stage install
XDG_DATA_DIRS=/stage/usr/share:/usr/share PATH=/stage/usr/bin:$PATH python3 /src/toddy-probe.py /build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
text=Path('/build/upstream-tests.log').read_text();assert 'Ran 64 tests' in text and text.rstrip().endswith('OK')
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native build-only ITS/gettext XML translation tool', 'upstream_python_tests':64,'upstream_exit':0,'upstream_note':'Original tests/run_tests.py executed in private source copy; make check alone registers no cases','staged_consumer_exit':0,'consumer':json.loads(Path('/build/consumer.log').read_text())},indent=2)+'\n')
PY
