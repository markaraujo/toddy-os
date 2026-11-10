#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --sysconfdir=/etc --with-python3 --enable-introspection \
    --without-escrow --without-gtk-doc --without-lvm --without-lvm_dbus \
    --without-nvdimm --without-tools --without-smartmontools > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
(
    export GI_TYPELIB_PATH=/build/compile/src/lib
    export LD_LIBRARY_PATH=/build/compile/src/utils/.libs:/build/compile/src/lib/.libs
    export PYTHONPATH=/src/tests:/src/src/python
    export LIBBLOCKDEV_CONFIG_DIR=/src/tests/test_configs/default_config
    timeout 40 python3 -m unittest -v \
        utils_test.UtilsExecProgressTest.test_initialization \
        utils_test.UtilsExecLoggingTest.test_version_cmp \
        utils_test.UtilsExecLoggingTest.test_exec_locale > /build/original-core-tests.log 2>&1
)
make DESTDIR=/stage install > /build/original-stage.log 2>&1
export GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0
export LD_LIBRARY_PATH=/stage/usr/lib
export LIBBLOCKDEV_CONFIG_DIR=/stage/etc/libblockdev/3/conf.d
export PYTHONPATH=/stage/usr/lib/python3.14/site-packages
python3 - <<'PROBE' > /build/local-probe.log 2>&1
from importlib import import_module
import gi
gi.require_version('BlockDev', '3.0')
from gi.repository import BlockDev
assert gi.Repository.get_default().get_typelib_path('BlockDev') == '/stage/usr/lib/girepository-1.0/BlockDev-3.0.typelib'
assert import_module('gi.overrides.BlockDev').__file__.startswith('/stage/')
crypto = BlockDev.PluginSpec(name=BlockDev.Plugin.CRYPTO, so_name=None)
for cycle in range(2):
    assert BlockDev.reinit([crypto], True, None)
    assert BlockDev.get_available_plugin_names() == ['crypto']
    assert BlockDev.crypto_is_tech_avail(BlockDev.CryptoTech.LUKS, BlockDev.CryptoTechMode.QUERY)
    assert BlockDev.reinit([], True, None)
    assert BlockDev.get_available_plugin_names() == []
print('BlockDev 3 GI and two local crypto plugin load/query/unload cycles passed')
PROBE
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path

work = Path('/build')
stage = Path('/stage')
tests = (work / 'original-core-tests.log').read_text()
assert 'Ran 3 tests' in tests and '\nOK\n' in tests and 'skipped' not in tests
consumer = (work / 'local-probe.log').read_text()
assert 'BlockDev 3 GI and two local crypto plugin load/query/unload cycles passed\n' in consumer
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
required = {'usr/lib/girepository-1.0/BlockDev-3.0.typelib', 'usr/share/gir-1.0/BlockDev-3.0.gir',
            'usr/lib/python3.14/site-packages/gi/overrides/BlockDev.py'}
assert artifacts and required <= payload.keys()
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '3.5.0', 'compile_exit': 0, 'stage_exit': 0, 'selected_original_core_cases': 3,
          'consumer': consumer, 'artifacts': artifacts, 'stage_sha256': payload,
          'device_tests_pending': True}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
