#!/bin/bash
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py adwaita-fonts
# Generate native caches after the final font files have their actual inodes.
chroot /mnt/lfs /usr/bin/fc-cache -f /usr/share/fonts/Adwaita
python3 - <<'PY'
import hashlib,json
from pathlib import Path
cache=Path('/mnt/lfs/var/cache/fontconfig')
rows=[{'path':str(p.relative_to('/mnt/lfs')),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size}
      for p in sorted(cache.glob('*')) if p.is_file() and not p.is_symlink()]
assert any(r['path'].endswith('.cache-9') or '.cache-' in r['path'] for r in rows)
Path('/var/log/toddy/phase2/adwaita-fonts-generated-cache.json').write_text(json.dumps({'generator':'native fc-cache -f /usr/share/fonts/Adwaita','scope':'generated runtime cache, not portable package payload; regenerate in final image','files':rows},indent=2)+'\n')
PY
