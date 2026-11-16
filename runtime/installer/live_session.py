"""Live-only root producer and independently checked installer session authority."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import signal
import stat
import subprocess
import sys
import threading

from .composition import secured
from .disk_plan import InstallError
from ..shared.json import strict_json

LIVE_UID=1000
LIVE_USER='toddy-live'
IMAGE_CLASS=Path('/usr/share/toddy/live-image.json')
UNIT='toddy-live-owner.service'
UNIT_PATH=Path('/etc/systemd/system')/UNIT
DIRECTORY=Path('/run/toddy-live-owner')
ATTESTATION=DIRECTORY/'session.json'
INIT_MARKER=Path('/run/toddy/live-session')
HASH=re.compile('[a-f0-9]{64}\\Z')
UUID=re.compile('[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\\Z')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(argv):
    secured(argv[0]);result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,env={'PATH':'/usr/bin:/usr/sbin','HOME':'/nonexistent','LC_ALL':'C'},
        timeout=3,close_fds=True)
    if result.returncode or len(result.stdout)>65536:raise InstallError('installer_live_fact_unavailable')
    return result.stdout.decode('utf-8',errors='strict').strip()


def properties(text):
    rows=[line.split('=',1) for line in text.splitlines()]
    if any(len(row)!=2 for row in rows) or len({row[0] for row in rows})!=len(rows):raise InstallError('installer_live_fact_invalid')
    return dict(rows)


def image_class():
    value=strict_json(secured(IMAGE_CLASS,16384).read_bytes())
    keys={'version','image_class','live_uid','live_user','media_id','producer_sha256','unit_sha256','profile_source_sha256'}
    if not isinstance(value,dict) or set(value)!=keys or type(value['version']) is not int or value['version']!=1 or value['image_class']!='phase2-live-installer' or type(value['live_uid']) is not int or value['live_uid']!=LIVE_UID or value['live_user']!=LIVE_USER or any(not isinstance(value[key],str) or not HASH.fullmatch(value[key]) for key in ('media_id','producer_sha256','unit_sha256','profile_source_sha256')):
        raise InstallError('installer_live_image_class')
    if digest(secured(__file__))!=value['producer_sha256'] or digest(secured(UNIT_PATH))!=value['unit_sha256']:raise InstallError('installer_live_source_changed')
    return value


def boot_facts():
    release=Path('/etc/os-release')
    if release.is_symlink():
        if os.readlink(release) not in ('../usr/lib/os-release','/usr/lib/os-release') or release.resolve()!=Path('/usr/lib/os-release'):raise InstallError('installer_live_os')
        release=Path('/usr/lib/os-release')
    rows=secured(release,16384).read_text().splitlines()
    ids=[line.removeprefix('ID=') for line in rows if line.startswith('ID=')]
    if ids not in (['toddy'],['"toddy"'],["'toddy'"]) or 'toddy.live' not in Path('/proc/cmdline').read_text().split():raise InstallError('installer_live_os')
    image=image_class()
    marker=secured(INIT_MARKER,256).read_text().strip()
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if marker!=image['media_id'] or not UUID.fullmatch(boot):raise InstallError('installer_live_boot_identity')
    account=pwd.getpwuid(LIVE_UID)
    if account.pw_name!=LIVE_USER or account.pw_gid!=LIVE_UID or account.pw_dir!='/home/'+LIVE_USER or account.pw_shell!='/bin/bash':raise InstallError('installer_live_account_identity')
    return {'boot_id':boot,'image_class_sha256':digest(IMAGE_CLASS),'media_id':marker,
            'producer_sha256':image['producer_sha256'],'unit_sha256':image['unit_sha256']}


def active_session():
    session=command(['/usr/bin/loginctl','show-user',str(LIVE_UID),'-p','Display','--value'])
    if not re.fullmatch('[A-Za-z0-9_-]{1,128}',session):raise InstallError('installer_live_session_required')
    value=properties(command(['/usr/bin/loginctl','show-session',session,'-p','User','-p','Name','-p','Active','-p','Remote','-p','LockedHint','-p','Type','-p','Class','-p','State','-p','Service']))
    if value!={'User':str(LIVE_UID),'Name':LIVE_USER,'Active':'yes','Remote':'no','LockedHint':'no',
               'Type':'wayland','Class':'user','State':'active','Service':'gdm-autologin'}:raise InstallError('installer_live_session_required')
    return session


def producer_facts():
    value=properties(command(['/usr/bin/systemctl','show',UNIT,'-p','MainPID','-p','ActiveState','-p','SubState','-p','InvocationID','-p','FragmentPath']))
    if set(value)!={'MainPID','ActiveState','SubState','InvocationID','FragmentPath'} or not re.fullmatch('[1-9][0-9]{0,9}',value['MainPID']) or value['ActiveState']!='active' or value['SubState']!='running' or value['FragmentPath']!=str(UNIT_PATH) or not re.fullmatch('[a-f0-9]{32}',value['InvocationID']):raise InstallError('installer_live_producer_required')
    pid=int(value['MainPID']);status=Path('/proc')/str(pid)/'status'
    uids=[line.split()[1:] for line in status.read_text().splitlines() if line.startswith('Uid:')]
    cgroup=(Path('/proc')/str(pid)/'cgroup').read_text().splitlines()
    if uids!=[['0','0','0','0']] or cgroup!=['0::/system.slice/'+UNIT]:raise InstallError('installer_live_producer_required')
    return {'producer_pid':pid,'producer_invocation':value['InvocationID']}


def validate_attestation(value,boot,producer,session,uid):
    expected={'version':1,'uid':LIVE_UID,'user':LIVE_USER,'session_id':session,**boot,**producer}
    if type(uid) is not int or uid!=LIVE_UID or not isinstance(value,dict) or value!=expected or any(type(value.get(key)) is not int for key in ('version','uid','producer_pid')):
        raise InstallError('installer_live_authority_mismatch')
    return True


def authorize_live_owner(uid):
    if os.getuid()!=0 or os.geteuid()!=0:raise InstallError('installer_live_root_required')
    boot=boot_facts();producer=producer_facts();session=active_session()
    info=DIRECTORY.lstat()
    if DIRECTORY.resolve()!=DIRECTORY or (info.st_mode,info.st_uid,info.st_gid)!=(stat.S_IFDIR|0o700,0,0):raise InstallError('installer_live_authority_directory')
    value=strict_json(secured(ATTESTATION,16384).read_bytes())
    if stat.S_IMODE(ATTESTATION.stat().st_mode)!=0o644:raise InstallError('installer_live_authority_metadata')
    return validate_attestation(value,boot,producer,session,uid)


def produce():
    if os.getuid()!=0 or os.geteuid()!=0:raise InstallError('installer_live_root_required')
    boot=boot_facts();info=DIRECTORY.lstat()
    if DIRECTORY.resolve()!=DIRECTORY or (info.st_mode,info.st_uid,info.st_gid)!=(stat.S_IFDIR|0o700,0,0):raise InstallError('installer_live_authority_directory')
    stopped=threading.Event();signal.signal(signal.SIGTERM,lambda *_:stopped.set());signal.signal(signal.SIGINT,lambda *_:stopped.set())
    previous=None;inode=None
    def remove_own():
        nonlocal inode,previous
        if inode is not None:
            try:
                if ATTESTATION.lstat().st_ino==inode:ATTESTATION.unlink()
            except FileNotFoundError:pass
        inode=None;previous=None
    try:
        while not stopped.is_set():
            # Polls only kernel/logind state; no credentials, model/network or
            # repeated authentication. Root unit/cgroup attribution is mandatory.
            producer=producer_facts()
            if producer['producer_pid']!=os.getpid():raise InstallError('installer_live_producer_required')
            if boot_facts()!=boot:raise InstallError('installer_live_boot_changed')
            try:session=active_session()
            except (InstallError,FileNotFoundError):remove_own();stopped.wait(2);continue
            value={'version':1,'uid':LIVE_UID,'user':LIVE_USER,'session_id':session,**boot,**producer}
            if value!=previous:
                if ATTESTATION.exists() or ATTESTATION.is_symlink():
                    secured(ATTESTATION,16384)
                    if inode is None or ATTESTATION.lstat().st_ino!=inode:raise InstallError('installer_live_existing_authority')
                part=DIRECTORY/('.session-'+os.urandom(12).hex())
                with part.open('xb') as stream:
                    os.fchmod(stream.fileno(),0o644);stream.write(json.dumps(value,sort_keys=True).encode()+b'\n');stream.flush();os.fsync(stream.fileno())
                os.replace(part,ATTESTATION);inode=ATTESTATION.lstat().st_ino;previous=value
                fd=os.open(DIRECTORY,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
                try:os.fsync(fd)
                finally:os.close(fd)
            stopped.wait(2)
    finally:remove_own()


def main():
    if sys.argv[1:]==['produce']:produce()
    elif sys.argv[1:]==['pam']:
        if os.getuid()!=0 or os.geteuid()!=0 or os.environ.get('PAM_USER')!=LIVE_USER or os.environ.get('PAM_SERVICE')!='gdm-autologin' or os.environ.get('PAM_TYPE')!='auth':raise InstallError('installer_live_pam_scope')
        boot_facts()
    else:raise InstallError('installer_live_arguments')


if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Toddy live session authority unavailable.') from None
