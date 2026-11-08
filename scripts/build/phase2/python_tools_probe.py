"""Actual native Pytest pass/fail, metadata/dependency, TOML and lexer consumers."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from packaging.requirements import Requirement
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import CLexer
import tomlkit

config=json.loads(Path(sys.argv[1]).read_text())
work=Path(sys.argv[2]);assert work.is_absolute() and not work.exists()
assert work.is_relative_to('/build') or work.is_relative_to('/tmp')
work.mkdir();versions={};dependencies=[]
for row in config['packages']:
    name=row['name'];version=importlib.metadata.version(name)
    assert version==row['version'], (name,version)
    versions[name]=version
    for text in importlib.metadata.requires(name) or []:
        requirement=Requirement(text)
        if requirement.marker and not requirement.marker.evaluate({'extra':''}):continue
        actual=importlib.metadata.version(requirement.name)
        assert actual in requirement.specifier, (name,text,actual)
        dependencies.append({'consumer':name,'requirement':text,'actual_version':actual})
document=tomlkit.parse('# retain comment\n[tool]\nvalue = 20\n')
document['tool']['value']=42
assert tomlkit.parse(tomlkit.dumps(document))['tool']['value']==42
assert '# retain comment' in tomlkit.dumps(document)
rendered=highlight('int main(void) { return 42; }',CLexer(),HtmlFormatter())
assert '<span' in rendered and 'main' in rendered and '42' in rendered
positive=work/'positive';negative=work/'negative';positive.mkdir();negative.mkdir()
(positive/'pytest.ini').write_text('[pytest]\naddopts = -ra\n')
(positive/'test_native.py').write_text('import pytest\n@pytest.fixture\ndef value(): return 42\n@pytest.mark.parametrize("offset", [0, 1])\ndef test_native(value, offset): assert value + offset == 42 + offset\n')
(negative/'test_native_failure.py').write_text('def test_expected_failure(): assert 41 == 42\n')
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1')
rows=[]
for label,directory,expected,passed,failed in [('positive',positive,0,2,0),('negative',negative,1,0,1)]:
    report=directory/'result.xml'
    result=subprocess.run([sys.executable,'-m','pytest','-q','--color=no','--junitxml',str(report),
                           str(directory)],cwd=directory,env=env,capture_output=True,text=True,timeout=30)
    (work/(label+'.log')).write_text(result.stdout+result.stderr)
    (work/(label+'.exit')).write_text(str(result.returncode)+'\n')
    assert result.returncode==expected
    xml=ET.fromstring(report.read_bytes())
    assert xml.tag in {'testsuite','testsuites'}
    suites=[xml] if xml.tag=='testsuite' else xml.findall('testsuite')
    assert suites and sum(int(s.get('tests','0')) for s in suites)==passed+failed
    assert sum(int(s.get('failures','0')) for s in suites)==failed
    assert all(int(s.get('errors','0'))==int(s.get('skipped','0'))==0 for s in suites)
    rows.append({'name':'pytest-'+label,'native_exit':result.returncode,'expected_exit':expected,
                 'passed':passed,'expected_failures':failed,'errors':0,'skipped':0})
proof={'scope':'Actual native frozen wheel versions/dependency closure, TOML comment-preserving edit, C lexer HTML, Pytest fixture/param pass2 and deliberate fail1; not full upstream suites',
       'uid':os.getuid(),'versions':versions,'dependencies':dependencies,'pytest':rows,
       'toml_roundtrip':True,'lexer_html':True}
(work/'results.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof),flush=True)
