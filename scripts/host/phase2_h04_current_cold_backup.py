#!/usr/bin/env python3
"""Exactly one inactive H04 project backup; current-byte custody, no history claim."""
import hashlib,json,os,stat,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import phase2_compress_cold_checkpoints as cold
import phase2_mvp_cold_builders as graph_guard
ROOT=cold.ROOT
PROFILES={'h04-target.qcow2':{'device':66306,'inode':11810807,'bytes':8805875712,'allocated':8784470016,
    'mtime_ns':1793929443958529671,'ctime_ns':1793929443958529671,'backing':None}}

def image_identity(path):
    path=Path(path)
    if path!=ROOT/'.local/vm/checkpoints/h04-target.qcow2' or path.resolve()!=path:raise ValueError('Only exact current H04 project backup')
    expected=PROFILES[path.name];info=path.lstat()
    if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode)!=0o644 or info.st_uid!=os.getuid() or info.st_gid!=os.getgid() or info.st_nlink!=1 or
        (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)!=(expected['device'],expected['inode'],expected['bytes'],expected['mtime_ns'],expected['ctime_ns'])):
        raise ValueError('Current H04 backup inode/metadata changed')
    return expected

def graph():
    original=graph_guard.PROFILES
    graph_guard.PROFILES=PROFILES
    try:return graph_guard.graph()
    finally:graph_guard.PROFILES=original

def current_sha(fd,original):
    """Complete fresh readonly hash under exclusive OFD custody, before compression."""
    os.lseek(fd,0,os.SEEK_SET);digest=hashlib.sha256();count=0
    while block:=os.read(fd,8*1024**2):digest.update(block);count+=len(block)
    if count!=original.st_size or cold.identity(os.fstat(fd))!=cold.identity(original):raise ValueError('Current backup changed during fresh readonly SHA')
    os.lseek(fd,0,os.SEEK_SET)
    return {'sha256':digest.hexdigest(),'bytes':count,'identity':cold.identity(original),'historical_integrity_claimed':False}

def inspect():
    _,rows=graph();facts=image_identity(ROOT/'.local/vm/checkpoints/h04-target.qcow2')
    return {'scope':'readonly current project backup eligibility only','source':'.local/vm/checkpoints/h04-target.qcow2','metadata':facts,
        'absolute_graph_images':len(rows),'maximum_allocated_reclaim_bytes':facts['allocated'],'historical_integrity_claimed':False,
        'current_full_sha_pending_operator_custody':True,'actual_gain_known':False}

if __name__=='__main__':
    if sys.argv[1:]==['inspect']:print(json.dumps(inspect(),sort_keys=True))
    elif sys.argv[1:]==['compress']:
        sys.argv=[sys.argv[0],'--profile','mvp-h04-current'];cold.main()
    else:raise SystemExit('Only fixed inspect|compress; no path or cleanup arguments')
