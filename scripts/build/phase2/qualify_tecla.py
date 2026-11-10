"""Bind Tecla's staged bytes and separate display-dependent native CLI evidence."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify_stage(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/tecla-50.0');w=Path('/mnt/lfs/sources/phase2/work/tecla-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='2542acb24850082e0ccf6aa17af9651db71d22f0e233fdbf5ed0cffe2e45bc06' and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']=='a0dbd6f7744e0d167a6125e5bd0f9b79bbcf3d42d3322ea19f0a1bff21b04f05'
 assert (l/'tecla-1.exit').read_text().strip()=='1' and (l/'tecla-collect-2.exit').read_text().strip()=='0'
 assert json.loads((l/'tecla-collect-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/tecla_collect_stage.py').read_text()
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_tests']['registered']==r['original_tests']['results']==[] and r['original_tests']['no_registered_tests_not_a_pass']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 assert digest(w/'compile/src/tecla')==digest(w/'stage/usr/bin/tecla')
 assert 'Version: 50.0' in (w/'stage/usr/share/pkgconfig/tecla.pc').read_text()
 return r

def qualify(root):
 r=qualify_stage(root);report=Path('/var/log/toddy/phase2/native-tecla-cli-report-1.json')
 proof=json.loads(report.read_text())
 assert hashlib.sha256(json.dumps(proof,sort_keys=True).encode()).hexdigest()=='7a0e45a402f7735e384ce8bfa85cbf848cc0b5d01536634dd5510acc29aa6aad'
 assert proof['kernel']=='7.1.8-toddy' and proof['compositor_exit']==0 and proof['all_selected_exits_zero'] is True
 rows=proof['runs'];assert len(rows)==2 and all(x['exit']==0 for x in rows)
 assert rows[0]['name']=='tecla --version' and rows[0]['stdout'].strip()=='tecla 50.0'
 assert rows[1]['name']=='tecla --help' and '--version' in rows[1]['stdout']
 assert proof['details']['graphical_preview_tested'] is False
 return r
