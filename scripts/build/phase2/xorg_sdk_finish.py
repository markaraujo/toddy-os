"""Resume only the failed compiler fixture; preserve original C/API and stage proof."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entries(root):
    result={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():result[str(p.relative_to(root))]={'symlink':os.readlink(p)}
        elif p.is_file():result[str(p.relative_to(root))]={'sha256':digest(p),'size':p.stat().st_size}
    return result


def main():
    assert os.getuid()==101
    root=Path('/build/xorg-sdk'); proof=root/'qualified.json'
    destination=Path('/build/xorg-sdk-consumer-recovery-2')
    assert not proof.exists() and not destination.exists(), 'Reconcile prior finish; no replay'
    old=(root/'probe.log').read_text()
    assert old.startswith('keysym resource synthetic-auth allocation display-parser: OK\n')
    assert 'compatibility map not defined in XkbWriteXKBCompatMap' in old
    assert (root/'probe.exit').read_text().strip()=='1'
    rows=json.loads((root/'results.partial.json').read_text())
    config=json.loads(Path('/src/toddy-sdk.json').read_text())
    assert len(rows)==10 and [r['name'] for r in rows]==[p['name'] for p in config['packages']]
    for row,package in zip(rows,config['packages']):
        assert row['source_sha256']==package['source_sha256'] and row['version']==package['version']
        assert entries(Path('/stage')/row['name'])==row['entries']
        assert row['log_sha256']==digest(root/'logs'/(row['name']+'.log'))
    prefix='/build/xorg-sdk/bootstrap/usr'
    with (root/'compiler-recovery-2.log').open('xb') as output:
        result=subprocess.run(['python3','/src/toddy-probe.py',prefix,str(destination),'--compiler-only'],
                              stdout=output,stderr=subprocess.STDOUT)
    (root/'compiler-recovery-2.exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0, 'Corrected compiler fixture failed'
    consumer=json.loads((destination/'results.json').read_text())
    assert consumer['c_api_exit'] is None
    consumer['c_api_exit']=0
    consumer['c_api_evidence']='Reused original native C exit0: exact original probe prints sentinel only after check=True consumer succeeds; original subsequent compiler-fixture failure preserved.'
    assert all(entries(Path('/stage')/r['name'])==r['entries'] for r in rows)
    proof.write_text(json.dumps({'scope':'Headless Xorg SDK stages with explicit compiler-fixture-only recovery, no session/physical claim',
        'packages':rows,'config_sha256':digest(Path('/src/toddy-sdk.json')),
        'probe_exit':0,'probe_log_sha256':digest(root/'compiler-recovery-2.log'),
        'original_probe_log_sha256':digest(root/'probe.log'),'consumer':consumer,
        'recovery':'Original SDK job1 exit1 retained after all10 build/check/stage0 and C consumer0; only corrected compiler cases rerun in job2.'},indent=2)+'\n')


if __name__=='__main__':main()
