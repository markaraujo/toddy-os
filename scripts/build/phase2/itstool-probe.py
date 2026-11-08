"""Exercise actual XML extraction and UTF-8 gettext translation merge."""
import json
from pathlib import Path
import subprocess
import sys
import libxml2


def main():
    root=Path(sys.argv[1]);root.mkdir()
    source=root/'fixture.xml'
    source.write_text('<root xmlns:its="http://www.w3.org/2005/11/its" its:version="2.0" its:translate="no"><p its:translate="yes">Hello Toddy</p></root>\n')
    commands=[['itstool','-o',str(root/'fixture.pot'),str(source)]]
    def run(args):
        r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        assert r.returncode==0,(args,r.returncode,r.stderr);return r
    run(commands[0]);assert 'msgid "Hello Toddy"' in (root/'fixture.pot').read_text()
    (root/'pt.po').write_text('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Language: pt_BR\\n"\n\nmsgid "Hello Toddy"\nmsgstr "Olá Toddy"\n')
    commands.append(['msgfmt','-o',str(root/'pt.mo'),str(root/'pt.po')]);run(commands[-1])
    commands.append(['itstool','-m',str(root/'pt.mo'),'-o',str(root/'translated.xml'),str(source)]);run(commands[-1])
    doc=libxml2.parseFile(str(root/'translated.xml'));assert doc.xpathEval('string(/root/p)')=='Olá Toddy';doc.freeDoc()
    print(json.dumps({'scope':'Actual native ITS extraction and UTF-8 gettext merge; no GUI acceptance','xml_extraction':True,'compiled_gettext_catalog':True,'portuguese_merge':True,'commands':commands}))


if __name__=='__main__':main()
