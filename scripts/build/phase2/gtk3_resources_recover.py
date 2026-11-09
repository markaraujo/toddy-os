"""Finish resource validation after a fixed/relocatable counting correction."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(code):
    assert os.getuid()==101
    src=Path('/src');work=Path('/build');union=work/'schema-union'
    (work/'recovery-2').mkdir()
    original_cache=sha(union/'gschemas.compiled')
    assert original_cache=='310d5f4f97596655f5b75d917b4e208a6b05212aa842be90dcb3bce1e856f6aa'
    assert not (work/'test-results.json').exists()
    assert not (work/'immodules-original.cache').exists()
    recipe=json.loads((src/'toddy-resources.json').read_text())
    module=ast.parse(code)
    function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    start=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Import) and any(a.name=='gi' for a in n.names))
    tail=ast.Module(body=function.body[start:],type_ignores=[])
    # Only the remaining validation/query statements run: no mkdir/copy/schema
    # generation or prior library/upstream test commands are replayed.
    context=dict(globals(),src=src,work=work,union=union,recipe=recipe)
    exec(compile(ast.fix_missing_locations(tail),'<gtk3-resource-finish>','exec'),context)
    assert sha(union/'gschemas.compiled')==original_cache
    path=work/'test-results.json';proof=json.loads(path.read_text())
    proof['recovery']='Original count mixed52fixed+6relocatable. Corrected separate counts; verified existing private cache reused unchanged, no schema/library/upstream replay.'
    path.write_text(json.dumps(proof,indent=2)+'\n')
