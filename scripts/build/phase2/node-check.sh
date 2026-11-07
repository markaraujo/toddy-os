#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(node --version) == v24.19.0 ]]
[[ $(dpkg-query -W -f='${Status}' nodejs) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
node - <<'JS'
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const { createHash } = require('node:crypto');
assert.equal(process.execPath, '/usr/bin/node');
assert.equal(createHash('sha256').update('toddy').digest('hex'),
  'ca974e2787c3c8689c56a30365e2bdc274ce9ee1096abacf2060b7bfa6a683e0');
const result = spawnSync(process.execPath, ['-e', 'process.stdout.write("native-child")'], {encoding:'utf8'});
assert.equal(result.status, 0);
assert.equal(result.stdout, 'native-child');
JS
NATIVE
