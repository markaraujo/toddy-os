"""Resume only the diagnosed IBus GTK4 backend guard failure; never install."""
from pathlib import Path
import hashlib,json,subprocess
p=Path('/build');s=p/'source/client/gtk2/ibusimcontext.c'
assert (p/'configure.log').is_file() and not (p/'original-tests.log').exists() and not (p/'stage.log').exists()
before=s.read_bytes();old=b'#ifdef HAVE_XIM\n    display = gtk_widget_get_display (ibusimcontext->client_window);\n'
assert before.count(old)==1 and b'GDK_WINDOWING_X11' in before
s.write_bytes(before.replace(old,b'    display = gtk_widget_get_display (ibusimcontext->client_window);\n#if defined(HAVE_XIM) && defined(GDK_WINDOWING_X11)\n'))
r=json.loads((p/'source-corrections.json').read_text());r.append({'path':str(s.relative_to(p/'source')),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'reason':'Shared GTK2/3/4 source needs actual GDK X11 backend as well as IBus XIM server; Wayland display lookup remains unconditional'})
(p/'source-corrections.json').write_text(json.dumps(r,indent=2)+'\n')
recipe=Path('/src/toddy-build.sh').read_text();marker='make -j4 > /build/compile.log 2>&1\n'
assert recipe.count(marker)==1
script='set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\ncd /build/source\nmake -j4 > /build/compile-2.log 2>&1\n'+recipe.split(marker)[1]
subprocess.run(['bash','-c',script],check=True)
