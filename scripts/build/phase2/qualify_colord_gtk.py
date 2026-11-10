"""Bind both colord GTK ABIs and distinguish pending original display tests."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/colord-gtk-0.3.1');w=Path('/mnt/lfs/sources/phase2/work/colord-gtk-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());locked=next(x for x in json.loads((root/'config/phase2/sources.lock.json').read_text())['components'] if x['name']=='colord-gtk')
 assert p['source_sha256']==locked['sha256'] and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']
 canonical=(root/'scripts/build/phase2/colord-gtk-build.sh').read_text()
 original=(s/'toddy-build.sh').read_text()
 if (l/'colord-gtk-finish-2.exit').exists():
  assert original.count('-Dvapi=true')==1 and original.replace('-Dvapi=true','-Dvapi=false').replace("['gtk3','gtk4','introspection','vapi','tests']","['gtk3','gtk4','introspection','tests']").replace("and not options['gtk2']","and not options['gtk2'] and not options['vapi']").replace('GTK3 GI/Vala','GTK3 GI; optional Vala omitted because owned Colord has no VAPI')==canonical
  assert (l/'colord-gtk-1.exit').read_text().strip()=='1' and (l/'colord-gtk-finish-2.exit').read_text().strip()=='1'
  assert (l/'colord-gtk-collect-3.exit').read_text().strip()=='0'
  assert 'Package `colord' in (w/'original-build.log').read_text() and 'not found' in (w/'original-build.log').read_text()
  command=(root/'scripts/build/phase2/colord_gtk_finish.py').read_text()+'\nmain('+repr(canonical)+')\n'
  assert json.loads((l/'colord-gtk-finish-2.job.json').read_text())['command'][-1]==command
  original_probe=(s/'toddy-probe.c').read_text()
  removed=''.join(line+'\n' for line in original_probe.splitlines() if 'g_assert_cmpint(CD_GTK_' in line)
  assert len(removed.splitlines())==3 and original_probe.replace(removed,'')==(root/'scripts/build/phase2/colord-gtk-probe.c').read_text()
  command=(root/'scripts/build/phase2/colord_gtk_collect.py').read_text()+'\nmain('+repr(canonical)+','+repr((root/'scripts/build/phase2/colord-gtk-probe.c').read_text())+')\n'
  assert json.loads((l/'colord-gtk-collect-3.job.json').read_text())['command'][-1]==command
 else:
  assert original==canonical and (l/'colord-gtk-1.exit').read_text().strip()=='0'
 assert digest(s/'toddy-probe.c')==p['probe_sha256']
 if not (l/'colord-gtk-finish-2.exit').exists():assert digest(s/'toddy-probe.c')==digest(root/'scripts/build/phase2/colord-gtk-probe.c')
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_tests_executed']==[] and r['original_display_suite_pending']
 assert {t['name'] for t in r['original_tests_registered']}=={'colord-test-private','colord-gtk4-test-private'}
 assert set(r['consumer'])=={'colord-gtk','colord-gtk4'} and all(v=='Colord GTK local GObject/profile-empty state/two fresh cycles; no widget/display/service access\n' for v in r['consumer'].values())
 options={o['name']:o['value'] for o in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())}
 assert all(options[n] for n in ['gtk3','gtk4','introspection','tests']) and not options['gtk2'] and not options['vapi']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 if (l/'colord-gtk-finish-2.exit').exists():
  assert r['artifacts']==json.loads((w/'before-finish-2.json').read_text())
  assert r['stage_sha256']==json.loads((w/'before-collect-3-stage.json').read_text())
 return r
