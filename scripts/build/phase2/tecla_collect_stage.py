from pathlib import Path
import hashlib,json,os
w=Path('/build');assert Path('/stage/usr/bin/tecla').is_file()
assert 'Version: 50.0' in Path('/stage/usr/share/pkgconfig/tecla.pc').read_text()
r={'scope':'Tecla50.0 keyboard previewer pinned to frozen BLFS source instead of moving control-center wrap HEAD. Compile/stage/data-only pkgconfig only; CLI initializes Adwaita before options and requires a separate native display test; no graphical keyboard preview/focus/input acceptance. Existing GTK/Adwaita/XKB evidence reused.','compile_exit':0,'stage_exit':0,'original_tests':json.loads((w/'original-test-results.json').read_text()),'consumer':{'pkgconfig_version':'50.0','CLI_requires_display':True,'CLI_tested':False,'graphical_viewer_tested':False},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to(w/'stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
