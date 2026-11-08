"""Real native XML API generation and schema validation for the build tool."""
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

destination=Path(sys.argv[1]);destination.mkdir()
version=subprocess.check_output(['doxygen','--version'],text=True).strip();assert version.startswith('1.18.0')
(destination/'fixture.h').write_text('/** Return an answer. */\nint toddy_answer(int value);\n')
(destination/'Doxyfile').write_text('PROJECT_NAME=ToddyFixture\nINPUT=fixture.h\nOUTPUT_DIRECTORY=out\nGENERATE_XML=YES\nGENERATE_HTML=NO\nGENERATE_LATEX=NO\nEXTRACT_ALL=YES\nQUIET=YES\nHAVE_DOT=NO\nWARN_AS_ERROR=YES\n')
with (destination/'generate.log').open('xb') as log:
    r=subprocess.run(['doxygen','Doxyfile'],cwd=destination,stdout=log,stderr=subprocess.STDOUT)
(destination/'generate.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
xml=destination/'out/xml';index=ET.parse(xml/'index.xml').getroot();assert index.tag=='doxygenindex'
found=[]
for p in xml.glob('*.xml'):
    for member in ET.parse(p).getroot().findall('.//memberdef'):
        if member.get('kind')=='function' and member.findtext('name')=='toddy_answer':
            assert member.findtext('type')=='int' and member.findtext('param/declname')=='value'
            found.append(p.name)
assert found
r=subprocess.run(['xmllint','--noout','--schema',str(xml/'index.xsd'),str(xml/'index.xml')],capture_output=True,text=True)
(destination/'schema.log').write_text(r.stdout+r.stderr);(destination/'schema.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
result={'scope':'Native build-tool version, real C function/parameter XML generation and XSD validation; no desktop application qualification',
        'version':version,'generator_exit':0,'schema_exit':0,'function':'toddy_answer','xml_files_with_function':found}
(destination/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
