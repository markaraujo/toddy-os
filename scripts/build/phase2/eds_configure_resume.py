"""Resume proven configure-only EDS failure with supported optional sound switch."""
from pathlib import Path
import hashlib,subprocess,sys
p=Path('/build');source=Path('/src/toddy-build.sh')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='4d8c38a0b048c3071cbfa1965bdc8249770d4ecb1daeffe30f64895eb82616f4'
assert (p/'compile/CMakeCache.txt').is_file()
assert 'ENABLE_CANBERRA:BOOL=ON' in (p/'compile/CMakeCache.txt').read_text()
assert not (p/'compile/build.ninja').exists() and not (p/'compile/.ninja_log').exists()
assert not (p/'original-tests.log').exists() and not list(Path('/stage').iterdir())
original=source.read_text();fresh=original.replace('-DENABLE_CANBERRA=ON','-DENABLE_CANBERRA=OFF')
assert fresh==sys.argv[1]
script=fresh.replace(' && ! -e /build/compile','')
assert script!=fresh
raise SystemExit(subprocess.run(['bash','-c',script]).returncode)
