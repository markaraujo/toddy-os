#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/password-change ]]
cc -O2 -Wall -Wextra /src/login-password-change.c -lpam -o /build/password-change
set +e
/build/password-change > /build/unprivileged-guard.stdout 2> /build/unprivileged-guard.stderr
result=$?
set -e
[[ $result == 64 && ! -s /build/unprivileged-guard.stdout && ! -s /build/unprivileged-guard.stderr ]]
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');(p/'compile-results.json').write_text(json.dumps({'scope':'Root-only native test client compile and unprivileged/missing-argument refusal only; no password operation performed in compiler sandbox.','source_sha256':hashlib.sha256(Path('/src/login-password-change.c').read_bytes()).hexdigest(),'client_sha256':hashlib.sha256((p/'password-change').read_bytes()).hexdigest(),'compile_exit':0,'unprivileged_guard_exit':64},indent=2)+'\n')
PY
