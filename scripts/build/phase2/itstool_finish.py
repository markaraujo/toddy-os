"""Retest only the two DTD-affected cases, then stage the existing tool."""
import json
import os
from pathlib import Path
import subprocess


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir())
    root=Path('/build');old=(root/'upstream-tests.log').read_text()
    assert 'Ran 64 tests' in old and old.rstrip().endswith('FAILED (failures=2)')
    names=['test_IT_keep_entities_1','test_IT_translate_with_external_dtds']
    assert all('FAIL: '+n+' ' in old for n in names)
    catalog=root/'docbook-catalog.xml';assert not catalog.exists()
    catalog.write_text('<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"><rewriteSystem systemIdStartString="http://www.oasis-open.org/docbook/xml/4.5/" rewritePrefix="file:///src/docbook/"/></catalog>\n')
    env=dict(os.environ,XML_CATALOG_FILES=str(catalog))
    with (root/'dtd-affected-tests.log').open('xb') as log:
        r=subprocess.run(['python3','tests/run_tests.py',*['ItstoolTests.'+n for n in names]],cwd=root/'source',env=env,stdout=log,stderr=subprocess.STDOUT)
    (root/'dtd-affected-tests.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    text=(root/'dtd-affected-tests.log').read_text();assert 'Ran 2 tests' in text and text.rstrip().endswith('OK')
    with (root/'stage.log').open('xb') as log:r=subprocess.run(['make','DESTDIR=/stage','install'],cwd=root/'compile',stdout=log,stderr=subprocess.STDOUT)
    (root/'stage.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    with (root/'consumer.log').open('xb') as log:
        r=subprocess.run(['python3','/src/toddy-probe.py','/build/consumer'],env=dict(os.environ,PATH='/stage/usr/bin:'+os.environ['PATH'],XDG_DATA_DIRS='/stage/usr/share:/usr/share'),stdout=log,stderr=subprocess.STDOUT)
    (root/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    result={'scope':'Native ITS XML/gettext tool; original full-suite failures retained',
        'upstream_python_tests':64,'original_passed':62,'original_failed':names,'affected_retested':names,'affected_native_exit':0,
        'staged_consumer_exit':0,'consumer':json.loads((root/'consumer.log').read_text()),
        'source_supplement':json.loads(Path('/src/toddy-dtd-prepared.json').read_text())}
    (root/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
