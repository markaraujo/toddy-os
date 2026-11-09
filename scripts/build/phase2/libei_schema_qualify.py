"""Run only the remaining registered protocol-schema check, preserving C evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    assert os.getuid()==101
    work=Path('/build');out=work/'schema-2';out.mkdir()
    proof=json.loads((work/'test-results.json').read_text())
    assert len(proof['upstream_selected'])==6 and all(r['exit']==0 for r in proof['upstream_selected'])
    registered=json.loads((work/'compile/meson-info/intro-tests.json').read_text())
    rows=[r for r in registered if r['name']=='dtdcheck'];assert len(rows)==1
    row=rows[0];before={str(p.relative_to(work/'stage')):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (work/'stage').rglob('*') if p.is_file() and not p.is_symlink()}
    with (out/'dtd.log').open('xb') as log:
        result=subprocess.run(row['cmd'],env=dict(os.environ,**row['env']),cwd=row.get('workdir') or work/'compile',
                              stdout=log,stderr=subprocess.STDOUT,timeout=60)
    (out/'dtd.exit').write_text(str(result.returncode)+'\n');assert result.returncode==0
    assert before=={str(p.relative_to(work/'stage')):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (work/'stage').rglob('*') if p.is_file() and not p.is_symlink()}
    proof['source_schema_validation']={'name':'dtdcheck','native_exit':0,'command':row['cmd'],
                                       'stage_files_unchanged':len(before),'log_sha256':hashlib.sha256((out/'dtd.log').read_bytes()).hexdigest()}
    proof['registered_not_selected']=[n for n in proof['registered_not_selected'] if n!='dtdcheck']
    (work/'test-results.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
