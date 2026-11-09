"""Select supported no-XIM profile for owned Wayland-only GTK; no installation."""
from pathlib import Path
import subprocess
p=Path('/build');assert not (p/'original-tests.log').exists() and not (p/'stage.log').exists()
s=(p/'source/client/gtk2/ibusimcontext.c').read_text()
assert '#if defined(HAVE_XIM) && defined(GDK_WINDOWING_X11)' in s
recipe=Path('/src/toddy-build.sh').read_text();start="CFLAGS='-O2 -std=gnu17' ./configure"
assert recipe.count(start)==1
script='set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\ncd /build/source\n'+start+recipe.split(start)[1]
assert script.count('--disable-static --disable-python2')==1
script=script.replace('--disable-static --disable-python2','--disable-xim --disable-static --disable-python2',1).replace('/build/configure.log','/build/configure-3.log').replace('/build/compile.log','/build/compile-3.log')
subprocess.run(['bash','-c',script],check=True)
