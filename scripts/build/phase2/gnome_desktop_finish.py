"""Finish only GNOME Desktop's direct language target and native data consumer."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(recipe,output='finish-2'):
    assert os.getuid()==101
    assert output in ('finish-2','finish-3')
    work=Path('/build');out=work/output;out.mkdir()
    rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
    assert len(rows)==1 and rows[0]['name'].endswith('bg-slide-show')
    assert rows[0]['result']=='OK' and rows[0]['returncode']==0
    stage=work/'stage'
    before={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    assert before and (work/'compile/libgnome-desktop/config.h').is_file()
    # The first direct target failed before either consumer ran. Continue only
    # those commands, not configure/build/upstream tests or staging.
    marker='cc -DG_LOG_DOMAIN'
    assert recipe.count(marker)==1
    tail=marker+recipe.split(marker,1)[1]
    (out/'finish.sh').write_text('set -euo pipefail\nexport GSETTINGS_BACKEND=memory\nexport PYTHONDONTWRITEBYTECODE=1\n'+tail)
    subprocess.run(['bash',str(out/'finish.sh')],check=True)
    assert before=={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
    path=work/'test-results.json';proof=json.loads(path.read_text())
    proof['consumer_recovery']='Only missing generated-config include corrected for direct original target; accepted library/stage/bg tests retained.'
    proof['stage_files_unchanged']=len(before)
    proof['introspection_warning']='Original GnomeBG load_async has no corresponding load_finish annotation; build succeeds, async GI/display behavior not qualified.'
    path.write_text(json.dumps(proof,indent=2)+'\n')
