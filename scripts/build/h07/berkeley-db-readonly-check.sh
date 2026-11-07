#!/bin/bash
# stdin must survive the namespace wrapper as used by the real handoff recipe.
set -euo pipefail
python3 - <<'PY'
import errno,json,os
from pathlib import Path
source=Path('/mnt/lfs/sources/db-5.3.28')
assert os.statvfs(source).f_flag&os.ST_RDONLY
try:
 descriptor=os.open(source/'LICENSE',os.O_WRONLY)
except OSError as error:
 assert error.errno==errno.EROFS,error
else:
 os.close(descriptor)
 raise AssertionError('Preserved source unexpectedly writable')
work=source/'build-production'
marker=work/'.toddy-production-write-probe'
with marker.open('x') as stream:
 stream.write('private build output only\n');stream.flush();os.fsync(stream.fileno())
assert marker.read_text()=='private build output only\n'
marker.unlink()
print(json.dumps({'source_write_errno':'EROFS','production_output_writable':True,'caller_stdin_preserved':True}))
PY
