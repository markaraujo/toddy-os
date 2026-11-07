#!/usr/bin/env python3
"""Adapt only GI 1.86's compiler/preprocessor mocks to Setuptools 84 dispatch."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

assert os.getuid() == 101
source = Path('/src/tests/scanner/test_ccompiler.py')
original = source.read_bytes()
assert hashlib.sha256(original).hexdigest() == 'ae0d323b8b59d3fb8d4e950b8d14be110fd2f01dc39c517150144e7125d2cfaa'
work = Path('/build/validation')
assert not work.exists(), 'Preserve prior qualification; do not replay'
work.mkdir()
logs = Path('/build/compile/meson-logs')
raw = (logs/'testlog.json').read_bytes()
rows = [json.loads(line) for line in raw.splitlines()]
assert len(rows) == 12
failed = [r for r in rows if r['result'] != 'OK' or r['returncode'] != 0 or r['is_fail']]
assert len(failed) == 1 and failed[0]['name'].endswith(':test_ccompiler.py')
assert 'self.call(pp_args)' in failed[0]['stdout'] or 'self.call(pp_args)' in failed[0].get('stderr', '')
for name in ['testlog.json', 'testlog.txt', 'testlog.junit.xml']:
    if (logs/name).exists():
        shutil.copyfile(logs/name, work/('original-'+name))
text = original.decode()
needle = "patch.object(distutils.ccompiler.CCompiler, 'spawn')"
assert text.count(needle) == 2
patched = text.replace(needle, "patch.object(distutils.ccompiler.CCompiler, 'call')").encode()
test = work/'test_ccompiler.py'
test.write_bytes(patched)
environment = dict(os.environ, PYTHONPATH='/build/compile', LD_LIBRARY_PATH='/build/compile/giscanner')
version = subprocess.check_output([sys.executable, '-c', 'import setuptools; print(setuptools.__version__)'],
                                  env=environment, text=True).strip()
assert version == '84.0.0'
result = subprocess.run([sys.executable, str(test)], env=environment, capture_output=True, timeout=60)
output = result.stdout + result.stderr
(work/'ccompiler-corrected.log').write_bytes(output)
sys.stdout.buffer.write(output); sys.stdout.flush()
assert result.returncode == 0
assert source.read_bytes() == original
# Exercise the real production preprocessor as well as the unchanged mock assertions.
(work/'live.c').write_text('#define TODDY_VALUE 42\n/* toddy-preserved-comment */\nint toddy_native = TODDY_VALUE;\n')
live = """from giscanner.ccompiler import CCompiler
from pathlib import Path
c=CCompiler();c.preprocess('/build/validation/live.c','/build/validation/live.i',[])
s=Path('/build/validation/live.i').read_text()
assert 'toddy_native = 42' in s and 'toddy-preserved-comment' in s
"""
actual = subprocess.run([sys.executable, '-c', live], env=environment, capture_output=True, timeout=60)
(work/'live-preprocessor.log').write_bytes(actual.stdout+actual.stderr)
assert actual.returncode == 0, actual.stderr.decode(errors='replace')
qualification = {
    'scope': 'GI 1.86.0 compiler/preprocessor test mock dispatch only; production source unchanged',
    'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'setuptools': version, 'original_groups': len(rows), 'unchanged_passing_groups': 11,
    'original_log_sha256': hashlib.sha256(raw).hexdigest(),
    'original_test_sha256': hashlib.sha256(original).hexdigest(),
    'corrected_test_sha256': hashlib.sha256(patched).hexdigest(),
    'corrected_test_exit': result.returncode, 'live_preprocessor_exit': actual.returncode,
    'corrected_log_sha256': hashlib.sha256(output).hexdigest(),
    'change': 'Only compile_args/preprocess_args mocks: CCompiler.spawn -> CCompiler.call; assertions/skips/expected failures unchanged',
}
(work/'qualification.json').write_text(json.dumps(qualification, indent=2)+'\n')
print(json.dumps(qualification, indent=2))
