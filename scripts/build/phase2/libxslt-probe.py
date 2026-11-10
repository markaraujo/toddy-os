"""Bounded real xsltproc transformation, malformed refusal and no-write recovery."""
from pathlib import Path
import json,os,subprocess,sys
prefix=Path(sys.argv[1]);work=Path(sys.argv[2]);assert not work.exists();work.mkdir(mode=0o700)
exe=str(prefix/'usr/bin/xsltproc');env=dict(os.environ,LD_LIBRARY_PATH=str(prefix/'usr/lib'))
r=subprocess.run([exe,'--version'],env=env,capture_output=True,text=True,timeout=10);assert r.returncode==0 and 'libxslt 10145' in r.stdout+r.stderr
xml=work/'input.xml';xml.write_text('<root>Toddy ã</root>')
xsl=work/'style.xsl';xsl.write_text('''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"><xsl:output method="text" encoding="UTF-8"/><xsl:template match="/"><xsl:value-of select="root"/></xsl:template></xsl:stylesheet>''')
base=[exe,'--nonet','--nowrite','--nomkdir','--maxdepth','128','--maxvars','4096']
for i in range(2):
 r=subprocess.run(base+[str(xsl),str(xml)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode==0 and r.stdout=='Toddy ã'
 bad=work/'malformed.xml';bad.write_text('<root>');r=subprocess.run(base+[str(xsl),str(bad)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode!=0
 forbidden=work/'must-not-exist.txt';write=work/'write.xsl';write.write_text('''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:exsl="http://exslt.org/common" extension-element-prefixes="exsl"><xsl:template match="/"><exsl:document href="'''+forbidden.as_uri()+'''" method="text">forbidden</exsl:document></xsl:template></xsl:stylesheet>''')
 r=subprocess.run(base+[str(write),str(xml)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode!=0 and not forbidden.exists() and 'write' in r.stderr.lower()
 r=subprocess.run(base+[str(xsl),str(xml)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode==0 and r.stdout=='Toddy ã'
print(json.dumps({'xsltproc_version':'1.1.45','UTF8_transform':True,'malformed_XML_refused':True,'EXSLT_write_refused_no_effect':True,'reset_recovery_cycles':2,'selected_flags':['nonet','nowrite','nomkdir','maxdepth128','maxvars4096'],'GUI_or_general_CLI_default_sandbox_claim':False}))
