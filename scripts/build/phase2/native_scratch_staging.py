"""Location-aware native staging; installed payload stays on the target filesystem.

Called only inside the existing exclusive full-root run_step transaction.
"""
from pathlib import Path
import json,os,stat,subprocess
from shared_source_inputs import UUID,volume,save

BASE=Path('/mnt/lfs/sources/phase2/work/doxygen-1')
LOG=Path('/var/log/toddy/phase2')
TARGET=Path('/mnt/lfs')
ALLOWED={'mitkrb':'1.22.2','libqmi':'1.38.0','modemmanager':'1.24.2','gnome-control-center':'50.4'}

def allocation(stage):
    # Count every entry as a newly allocated target block, even existing parents.
    total=0
    for p in stage.rglob('*'):
        entry=p.lstat()
        assert stat.S_ISREG(entry.st_mode) or stat.S_ISDIR(entry.st_mode) or stat.S_ISLNK(entry.st_mode),'Special stage entry refused'
        total+=max(4096,((entry.st_size+4095)//4096)*4096) if stat.S_ISREG(entry.st_mode) else 4096
    return total

def workspace_paths(r):
    source=Path(r['source']);target=Path(r['target'])
    assert source==BASE/'toddy-editor-workers/native-transactions-1/output'
    assert target==TARGET/'sources/native-package-output'
    return source,target

def check_workspace(r):
    source,target=workspace_paths(r)
    assert source.resolve()==source and target.resolve()==target
    assert source.stat().st_ino==r['inode']==target.stat().st_ino and source.stat().st_dev==target.stat().st_dev==BASE.stat().st_dev
    assert target.stat().st_uid==0 and target.stat().st_mode&0o777==0o700
    flags=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(target)],text=True).strip().split(','))
    assert {'rw','nodev','nosuid'}<=flags

def mount_workspace(source,target):
    assert source.resolve()==source and target.resolve()==target
    assert not list(source.iterdir()) and not list(target.iterdir())
    assert subprocess.run(['mountpoint','-q',str(target)]).returncode==32
    subprocess.run(['mount','--bind',str(source),str(target)],check=True)
    subprocess.run(['mount','-o','remount,bind,rw,nosuid,nodev',str(target)],check=True)

def bind_stage(name,physical):
    assert name in ALLOWED and physical==BASE/'toddy-editor-workers/native-transactions-1'/(name+'-promotion-1')
    assert physical.resolve()==physical and physical.is_dir() and physical.stat().st_dev==BASE.stat().st_dev!=TARGET.stat().st_dev
    target=TARGET/'sources/stage'/('phase2-'+name)
    receipt=LOG/(name+'-promotion-alias-1.json');assert not receipt.exists() and not target.exists()
    r={'state':'bind-intended','physical':str(physical),'target':str(target),'inode':physical.stat().st_ino,'filesystem_uuid':UUID}
    save(receipt,r);target.mkdir(mode=0o755)
    subprocess.run(['mount','--bind',str(physical),str(target)],check=True)
    subprocess.run(['mount','-o','remount,bind,rw,nosuid,nodev',str(target)],check=True)
    assert target.resolve()==target and target.stat().st_ino==r['inode'] and target.stat().st_dev==BASE.stat().st_dev
    r['state']='complete';save(receipt,r);return target

def prepare(name):
    assert os.geteuid()==0 and name in ALLOWED
    volume(BASE)
    assert os.statvfs(TARGET).f_frsize==4096
    stage=TARGET/'sources/phase2/work'/(name+'-1')/'stage'
    assert stage.resolve()==stage and stage.is_dir() and stage.stat().st_dev==BASE.stat().st_dev!=TARGET.stat().st_dev
    required=16*1024**3+allocation(stage)+8*1024**2
    v=os.statvfs(TARGET);assert v.f_bavail*v.f_frsize>=required,'Keep installed payload plus metadata above fixed target reserve'
    v=os.statvfs(BASE);assert v.f_bavail*v.f_frsize>=512*1024**2+3*allocation(stage)+8*1024**2
    cache=Path('/var/cache/toddy/packages');assert cache.stat().st_dev!=TARGET.stat().st_dev
    v=os.statvfs(cache);assert v.f_bavail*v.f_frsize>=2*allocation(stage)+8*1024**2
    parent=BASE/'toddy-editor-workers/native-transactions-1'
    receipt=LOG/'native-output-scratch-1.json'
    if receipt.exists():
        workspace=json.loads(receipt.read_text());assert workspace['state']=='complete';check_workspace(workspace)
    else:
        assert not parent.exists();workspace={'state':'creation-intended','source':str(parent/'output'),
            'target':str(TARGET/'sources/native-package-output'),'filesystem_uuid':UUID}
        save(receipt,workspace);parent.mkdir(mode=0o700);(parent/'output').mkdir(mode=0o700)
        target=Path(workspace['target']);assert target.is_dir() and target.stat().st_uid==0 and target.stat().st_mode&0o777==0o700
        workspace.update(state='bind-intended',inode=(parent/'output').stat().st_ino);save(receipt,workspace)
        mount_workspace(parent/'output',target);check_workspace(workspace);workspace['state']='complete';save(receipt,workspace)
    assert not list(Path(workspace['source']).iterdir()),'Pending native archive output must be reconciled'
    assert parent.stat().st_uid==0 and parent.stat().st_mode&0o777==0o700
    p=LOG/(name+'-native-scratch-stage-1.json');destination=parent/(name+'-promotion-1')
    assert not p.exists() and not destination.exists(),'Inspect existing transaction; never replay'
    r={'state':'prepared','name':name,'version':ALLOWED[name],'destination':str(destination),
       'filesystem_uuid':UUID,'target_required_bytes':required,'payload_allocation_bound':allocation(stage),
       'scope':'Source stage/promotion/native archive workspace on qualified scratch; installed files remain on target, full-root verification retained'}
    save(p,r);destination.mkdir(mode=0o755)
    alias=bind_stage(name,destination);r['physical_destination']=str(destination);r['destination']=str(alias);save(p,r);return r

def destination(name):
    assert name in ALLOWED;volume(BASE)
    r=json.loads((LOG/(name+'-native-scratch-stage-1.json')).read_text());assert r['state']=='prepared' and r['version']==ALLOWED[name]
    physical=BASE/'toddy-editor-workers/native-transactions-1'/(name+'-promotion-1')
    expected=TARGET/'sources/stage'/('phase2-'+name)
    assert r['destination']==str(expected) and r['physical_destination']==str(physical)
    assert expected.resolve()==expected and expected.stat().st_ino==physical.stat().st_ino and expected.stat().st_dev==BASE.stat().st_dev!=TARGET.stat().st_dev
    assert not list(expected.iterdir()),'Only a freshly prepared empty promotion alias may be populated'
    workspace=json.loads((LOG/'native-output-scratch-1.json').read_text());assert workspace['state']=='complete';check_workspace(workspace)
    v=os.statvfs(TARGET);assert v.f_bavail*v.f_frsize>=r['target_required_bytes']
    stage=TARGET/'sources/phase2/work'/(name+'-1')/'stage'
    assert r['payload_allocation_bound']==allocation(stage) and r['target_required_bytes']==16*1024**3+allocation(stage)+8*1024**2
    return expected

def restore_workspace(base,log,name):
    p=log/'native-output-scratch-1.json'
    if not p.exists():return None
    assert base==BASE;volume(base)
    r=json.loads(p.read_text());assert r['state']=='complete' and r['filesystem_uuid']==UUID
    source,target=workspace_paths(r)
    assert target.resolve()==target and target.stat().st_uid==0 and target.stat().st_mode&0o777==0o700
    assert source.stat().st_ino==r['inode'] and source.stat().st_uid==0 and source.stat().st_mode&0o777==0o700
    receipt=log/(name+'-native-output.json');assert not receipt.exists()
    state={'state':'bind-intended','source':str(source),'target':str(target),'inode':r['inode']};save(receipt,state)
    mount_workspace(source,target);check_workspace(r);state['state']='complete';save(receipt,state);return state
