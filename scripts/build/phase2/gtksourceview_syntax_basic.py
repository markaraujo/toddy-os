"""Original pure text syntax cases; persist every child output before qualification."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

CASES = ['/syntax-highlighting/file.py','/syntax-highlighting/file.py3','/syntax-highlighting/file.sh','/syntax-highlighting/file.json','/syntax-highlighting/file.xml']
EXPECTED = None


def main():
    assert os.getuid()==101 and isinstance(CASES,list) and len(CASES)==5
    root=Path('/build/syntax-basic-6');root.mkdir()
    source=Path('/src');binary=Path('/build/compile/testsuite/test-syntax')
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==EXPECTED
    original_artifacts=json.loads(Path('/build/stage-results.json').read_text())['compiled_elf_sha256']
    for name,digest in original_artifacts.items():assert hashlib.sha256((Path('/build')/name).read_bytes()).hexdigest()==digest
    text=(source/'testsuite/test-syntax.c').read_text()
    assert 'g_test_init (&argc, &argv, NULL)' in text and 'gtk_init' not in text and 'gtk_test_init' not in text
    fixture=root/'layout/testsuite';fixture.mkdir(parents=True)
    (fixture/'data').symlink_to(source/'data',target_is_directory=True)
    (fixture.parent/'tests').symlink_to(source/'tests',target_is_directory=True)
    intro=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
    original=next(t for t in intro if t['name']=='test-syntax');assert original['cmd']==[str(binary)]
    env={**os.environ,**original['env'],'G_TEST_SRCDIR':str(fixture),'LD_LIBRARY_PATH':'/build/compile/gtksourceview:/stage/usr/lib'}
    outcomes=[];proof={'scope':'Actual unchanged original pure text GtkSourceView syntax driver selected cases in qualified UID101/no-network read-only-input sandbox; no display/product UI acceptance','original_binary_sha256':EXPECTED,'outcomes':outcomes,'all_selected_passed':False}
    destination=root/'result.json'
    def save():destination.write_text(json.dumps(proof,indent=2)+'\n')
    for i,case in enumerate(CASES):
        assert re.fullmatch(r'/syntax-highlighting/file[.][a-zA-Z0-9.+-]+',case)
        output=root/(str(i)+'.stdout');error=root/(str(i)+'.stderr')
        with output.open('xb') as out,error.open('xb') as err:
            try:r=subprocess.run([str(binary),'-p',case],cwd='/build/compile',env=env,stdout=out,stderr=err,timeout=30);exit_code=r.returncode
            except subprocess.TimeoutExpired:exit_code=None
        stdout=output.read_text();stderr=error.read_text();lines=re.findall(r'^ok\s+[0-9]+(?:\s+.*)?$',stdout,re.M)
        row={'case':case,'exit':exit_code,'tap_ok':lines,'stdout_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256(error.read_bytes()).hexdigest()};outcomes.append(row);save()
        if exit_code!=0 or len(lines)!=1 or case not in lines[0] or '# SKIP' in lines[0]:
            print(json.dumps(row),flush=True);print(stdout[-3000:],flush=True);print(stderr[-2000:],flush=True)
            raise AssertionError('Selected case did not pass; actual output preserved before assertion')
    for name,digest in original_artifacts.items():assert hashlib.sha256((Path('/build')/name).read_bytes()).hexdigest()==digest
    proof['compiled_elf_files_unchanged']=len(original_artifacts)
    proof['all_selected_passed']=True;proof['passed_cases']=len(outcomes);save()

if __name__=='__main__':main()
