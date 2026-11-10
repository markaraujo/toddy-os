"""Bind real Aspell dictionary/API tests to unchanged compiled and staged bytes."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/aspell-0.60.8.2');w=Path('/mnt/lfs/sources/phase2/work/aspell-1');l=Path('/var/log/toddy/phase2')
 prepared=json.loads((s/'toddy-prepared.json').read_text())
 assert prepared['source_sha256']=='57fe4863eae6048f72245a8575b44b718fb85ca14b9f8c0afc41b254dfd76919'
 assert prepared['extra_source']['sha256']=='4c8f734a28a088b88bb6481fcf972d0b2c3dc8da944f7673283ce487eac49fb3'
 assert not prepared['source_patches']
 original=(s/'toddy-build.sh').read_text();current=(root/'scripts/build/phase2/aspell-build.sh').read_text()
 if (l/'aspell-dictionary-2.exit').exists():
  assert (l/'aspell-1.exit').read_text().strip()=='2' and (l/'aspell-dictionary-2.exit').read_text().strip()=='0'
  assert hashlib.sha256(original.encode()).hexdigest()=='cdfdf53b1490540a9291eecf697fd7489315eadfa781a5ecdaec02345db10d35'
  corrected=original.replace('make DESTDIR=/stage install\nln -s','make DESTDIR=/stage install\n# Global Info index is generated shared state, not an Aspell-owned payload.\nmv /stage/usr/share/info/dir /build/aspell-generated-info-dir\nln -s').replace('exec /build/compile/aspell --data-dir=/build/dictionary-source','exec /build/compile/aspell --data-dir=/stage/usr/lib/aspell-0.60').replace('cd /build/dictionary-source\nASPELL=','cp /src/toddy-dictionary-source/{en.dat,en_phonet.dat,en_affix.dat} /stage/usr/lib/aspell-0.60/\ncd /build/dictionary-source\nASPELL=')
  assert corrected==current
  assert json.loads((l/'aspell-dictionary-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/aspell-resume-dictionary.sh').read_text()
 else:assert (l/'aspell-1.exit').read_text().strip()=='0' and original==current
 assert (s/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/aspell-probe.py').read_bytes()
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 resource=r['resource'];assert resource['exit']==0 and not resource['interrupted'] and resource['minimum_free']>=16*1024**3
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 if (w/'aspell-resume-2-before.json').exists():assert json.loads((w/'aspell-resume-2-before.json').read_text())==r['artifacts']
 assert len(list((w/'stage/usr/lib/aspell-0.60').glob('*.rws')))==22
 assert not (w/'stage/usr/share/info/dir').exists()
 assert r['consumer']=={'dictionary':'en_US official SCOWL2020.12.07','API_known_words':2,'misspelling_and_hello_suggestion':True,'UTF8_personal_word_persistence':True,'session_add_clear_cycles':2,'invalid_language_dictionary_option_refusals':3,'malformed_dictionary_unchanged':True,'personal_file_unchanged_on_refusal':True,'recovery_cycles':2,'CLI_pipe_and_unknown_option':True,'graphical_or_Portuguese_dictionary_tested':False}
 return r
