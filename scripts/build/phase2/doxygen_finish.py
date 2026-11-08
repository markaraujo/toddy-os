"""Stage preserved XML generator with the unmet optional BibTeX case retained."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir())
    rows=ET.parse('/build/ctest.xml').getroot().findall('.//testcase')
    failures=[r for r in rows if r.find('failure') is not None or r.find('error') is not None]
    assert len(rows)==122 and len(failures)==1 and failures[0].get('name')=='012_cite'
    assert not any(r.find('skipped') is not None for r in rows)
    assert shutil.which('bibtex') is None and shutil.which('perl')
    log=Path('/build/compile/Testing/Temporary/LastTest.log').read_text()
    assert 'Problems running bibtex' in log
    output=Path('/build/finish-2');output.mkdir()
    binaries={}
    for p in Path('/build/compile').rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        with p.open('rb') as f:
            if f.read(4)!=b'\x7fELF':continue
            f.seek(0);binaries[str(p.relative_to('/build/compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
    assert binaries;(output/'binaries-before.json').write_text(json.dumps(binaries,indent=2)+'\n')
    with (output/'stage.log').open('xb') as out:
        r=subprocess.run(['cmake','--install','/build/compile'],env=dict(os.environ,DESTDIR='/stage'),stdout=out,stderr=subprocess.STDOUT)
    (output/'stage.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    with (output/'consumer.log').open('xb') as out:
        r=subprocess.run(['python3','/src/toddy-probe.py',str(output/'consumer')],env=dict(os.environ,PATH='/stage/usr/bin:'+os.environ['PATH']),stdout=out,stderr=subprocess.STDOUT)
    (output/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    for relative,digest in binaries.items():
        with (Path('/build/compile')/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    result={'scope':'Build-only C/API XML generator qualified; optional bibliography unavailable, original012_cite failure retained',
       'upstream_total':122,'original_passed':121,'original_failed':[{'name':'012_cite','reason':'External optional BibTeX absent; Perl5.44 available','passed':False}],
       'existing_compiled_elf_files_unchanged':len(binaries),'staged_consumer_exit':0,
       'consumer':json.loads((output/'consumer/results.json').read_text()),
       'limitations':'Bibliography/citation integration requires optional BibTeX. No full-suite success, GUI, desktop/catalog availability claim.'}
    Path('/build/test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
