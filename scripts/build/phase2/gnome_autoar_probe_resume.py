"""Correct own C locale initialization; keep all original extraction evidence."""
from pathlib import Path
import hashlib,json,os,re,subprocess,zipfile

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main(probe):
 w=Path('/build');assert not (w/'stage-results.json').exists()
 assert (w/'original-tests.exit').read_text().strip()=='0'
 verified=json.loads((w/'original-fixtures-verified.json').read_text());assert verified['source_unchanged'] and verified['private_input_reference_unchanged'] and verified['original_binary_unmodified'] and verified['tmp_symlink_escape_not_created']
 before={'artifacts':hashes(w/'compile',True),'stage_sha256':hashes(w/'stage')}
 p=w/'probe-3';p.mkdir();(p/'probe.c').write_text(probe);(p/'before.json').write_text(json.dumps(before,indent=2)+'\n')
 subprocess.run(['bash','-c','cc /build/probe-3/probe.c -I/stage/usr/include/gnome-autoar-0 -L/stage/usr/lib $(pkg-config --cflags --libs gio-2.0) -lgnome-autoar-0 -Wl,-rpath,/stage/usr/lib -o /build/probe-3/native-probe'],check=True)
 c=p/'consumer';c.mkdir()
 with zipfile.ZipFile(c/'payload.zip','w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('documento-ã.txt','Olá Toddy\n')
 (c/'empty.zip').write_bytes(b'');original={n:hashlib.sha256((c/n).read_bytes()).hexdigest() for n in ['payload.zip','empty.zip']}
 with (p/'consumer.json').open('x') as out:r=subprocess.run([str(p/'native-probe'),str(c)],stdout=out,timeout=30)
 (p/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 assert original=={n:hashlib.sha256((c/n).read_bytes()).hexdigest() for n in original}
 code="import gi,json;gi.require_version('GnomeAutoar','0.1');gi.require_version('GnomeAutoarGtk','0.1');from gi.repository import GnomeAutoar,GnomeAutoarGtk;assert GnomeAutoar.Extractor.__gtype__.name=='AutoarExtractor';print(json.dumps({'namespace':'GnomeAutoar0.1/GnomeAutoarGtk0.1','GI_type':'AutoarExtractor','widget_tested':False}))"
 env=dict(os.environ,GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0',LD_LIBRARY_PATH='/stage/usr/lib');gi=json.loads(subprocess.check_output(['python3','-c',code],env=env,text=True,timeout=15))
 assert hashes(w/'compile',True)==before['artifacts'] and hashes(w/'stage')==before['stage_sha256']
 text=(w/'original-tests.log').read_text();cases=re.findall(r'^ok\s+\d+[^\n]*',text,re.M);assert cases and not re.search(r'^not ok',text,re.M)
 result={'scope':'Frozen gnome-autoar0.4.5 core/GTK3/GI/Vala using unchanged owned libarchive3.8.11. Original extraction unit/private identical fixture source-input-reference checks retained; manual programs compile only. Own C locale omission corrected consumer-only, actual ZIP UTF8/empty refusal/precancel no-effect/recovery/source retention/GI only, no GUI or mid-extraction Stop acceptance.','compile_exit':0,'stage_exit':0,'original_registered_programs':1,'original_unit_cases':cases,'original_fixture_verification':verified,'reused_libarchive_version':'3.8.11','consumer':json.loads((p/'consumer.json').read_text()),'GI_consumer':gi,'probe_only_recovery':{'compile_and_stage_unchanged':True,'original_failure_retained':True,'corrected_probe_sha256':hashlib.sha256(probe.encode()).hexdigest()},**before}
 (w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
