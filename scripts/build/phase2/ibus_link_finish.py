"""Link unchanged upstream Xlib stress fixture without enabling GTK X11/XIM."""
from pathlib import Path
import subprocess
p=Path('/build');assert not (p/'original-tests.log').exists() and not (p/'stage.log').exists()
assert 'Build XIM agent server        no' in (p/'configure-3.log').read_text()
recipe=Path('/src/toddy-build.sh').read_text();marker='make -j4 > /build/compile.log 2>&1\n';assert recipe.count(marker)==1
script='set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\ncd /build/source\n'+"make -j4 'test_stress_LDADD=$(AM_LDADD) -lX11' > /build/compile-4.log 2>&1\n"+recipe.split(marker)[1]
subprocess.run(['bash','-c',script],check=True)
