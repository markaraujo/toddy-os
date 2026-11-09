"""Finish only Lua's shared-library C consumer; reuse actual basic-suite result."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(probe, recipe):
    assert os.getuid()==101
    work=Path('/build');out=work/'probe-3';out.mkdir()
    assert 'final OK' in (work/'upstream-tests.log').read_text()
    assert (work/'project-2/src/liblua.so.5.4.8').is_file()
    stage=work/'stage'
    before={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    (out/'consumer.c').write_text(probe)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(out/'consumer.c'),
                    '-I/stage/usr/include','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',
                    '-llua','-lm','-ldl','-o',str(out/'consumer')],check=True)
    with (out/'consumer.log').open('xb') as log:
        result=subprocess.run([str(out/'consumer')],stdout=log,stderr=subprocess.STDOUT)
    (out/'consumer.exit').write_text(str(result.returncode)+'\n');assert result.returncode==0
    assert before=={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    summary=recipe.split("python3 - <<'PY'\n",1)[1].rsplit('\nPY',1)[0]
    subprocess.run(['python3','-c',summary],check=True)
    path=work/'test-results.json';proof=json.loads(path.read_text())
    proof['consumer_recovery']='luaL_dostring is a boolean macro; use loadstring then pcall for exact LUA_ERRRUN, preserving error-text/stack assertions. No library or basic-suite replay.'
    proof['stage_files_unchanged']=len(before)
    proof['patch_context']=json.loads((work/'patch-context-2.json').read_text())
    path.write_text(json.dumps(proof,indent=2)+'\n')
