"""Require original EDS service/storage tests and unchanged-stage C correction."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/evolution-data-server-3.60.2');work=Path('/mnt/lfs/sources/phase2/work/evolution-data-server-1');log=Path('/var/log/toddy/phase2')
    assert digest(source/'toddy-build.sh')=='4d8c38a0b048c3071cbfa1965bdc8249770d4ecb1daeffe30f64895eb82616f4'
    assert digest(source/'toddy-probe.c')=='e435a41a331a145878c3f878bbdc0ec30d9dc996c6e178c49638535cea816954'
    old=(source/'toddy-build.sh').read_text();configured=old.replace('-DENABLE_CANBERRA=ON','-DENABLE_CANBERRA=OFF')
    fresh=configured.replace('-Wl,-rpath,/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib \\', '-Wl,-rpath,/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib \\\n    -Wl,-rpath-link,/stage/usr/lib/evolution-data-server \\').replace('LD_LIBRARY_PATH=/stage/usr/lib timeout','LD_LIBRARY_PATH=/stage/usr/lib:/stage/usr/lib/evolution-data-server timeout')
    assert fresh==(root/'scripts/build/phase2/evolution-data-server-build.sh').read_text()
    probe=(root/'scripts/build/phase2/evolution-data-server-probe.c').read_text()
    assert probe==(source/'toddy-probe.c').read_text().replace('eds_major_version()','eds_major_version').replace('eds_minor_version()','eds_minor_version').replace('eds_micro_version()','eds_micro_version')
    prefix=['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(source),str(work)]
    jobs=[('evolution-data-server-1',['bash','/src/toddy-build.sh'],'1'),
          ('evolution-data-server-canberra-2',['python3','-c',(root/'scripts/build/phase2/eds_configure_resume.py').read_text(),configured],'1'),
          ('evolution-data-server-consumer-3',['python3','-c',(root/'scripts/build/phase2/eds_consumer_finish.py').read_text(),probe],'1'),
          ('evolution-data-server-private-4',['python3','-c',(root/'scripts/build/phase2/eds_private_consumer.py').read_text(),probe],'0')]
    for name,command,exitcode in jobs:
        assert (log/(name+'.exit')).read_text().strip()==exitcode
        assert json.loads((log/(name+'.job.json')).read_text())['command']==prefix+command
    tests=[]
    for c in ET.parse(work/'original-tests.xml').findall('.//testcase'):
        assert c.find('failure') is None and c.find('error') is None and c.find('skipped') is None
        tests.append({'name':c.get('name'),'result':'PASS'})
    assert len(tests)==len({t['name'] for t in tests})==101
    for name in ['test-cal-client-create-object','test-cal-client-modify-object','test-cal-client-remove-object','test-cal-cache-offline','e-source-registry-test','libedataserver-test']:
        assert {'name':name,'result':'PASS'} in tests,name
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    assert result['original_tests']==tests
    assert result['prior_ELFs_unchanged_by_consumer_correction'] and result['stage_unchanged_by_consumer_correction']
    assert result['consumer']=={'UTF8_calendar_roundtrip':True,'malformed_calendar_refused':True,'prior_event_preserved':True,'local_source_identity':True,'recovery_cycles':2,'real_accounts_used':False}
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        for name,sha in result[key].items():assert digest(work/base/name)==sha
    assert 'usr/share/glib-2.0/schemas/gschemas.compiled' not in result['stage_sha256']
    return result
