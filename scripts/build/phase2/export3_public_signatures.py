#!/usr/bin/env python3
"""Fixed export3 public signatures only; never sign or import private material."""
import base64,hashlib,json,os,re,shutil,stat,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path[:0]=[str(HERE)]
import offline_payload as p
from image_media import inherited_media_lease,trusted_log_parent
TARGET=Path('/mnt/lfs');EXPORT=TARGET/'sources/stage/toddy-package-export-3'
RUN=TARGET/'run/toddy-export3-public-verification-1'
RECEIPT=Path('/var/log/toddy/phase2/package-export3-public-signatures-1.json')
LIMITS={'Release.gpg':65536,'InRelease':2*1024**2}
MAX_PACKET=4*1024**2

def protected(path,directory=False):
    path=Path(path)
    if path.resolve()!=path:raise ValueError('Signature3 redirected path')
    for parent in path.parents:
        info=parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid or (info.st_mode&0o022 and not trusted_log_parent(parent,info)):raise ValueError('Signature3 unprotected ancestor')
    info=path.lstat()
    if info.st_uid or info.st_gid or info.st_mode&0o022 or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1):raise ValueError('Signature3 unprotected input')
    return path

def decode_packet(raw):
    if len(raw)>MAX_PACKET:raise ValueError('Signature3 packet bound')
    value=p.strict(raw)
    fields={'version','archive_export_sha256','release_sha256','public_key_sha256','host_verified_receipt_sha256','host_signed_receipt_sha256','signatures'}
    if not isinstance(value,dict) or set(value)!=fields or type(value['version']) is not int or value['version']!=1 or any(not isinstance(value[key],str) or not p.HASH.fullmatch(value[key]) for key in fields-{'version','signatures'}):raise ValueError('Signature3 exact public packet schema')
    if not isinstance(value['signatures'],dict) or set(value['signatures'])!=set(LIMITS):raise ValueError('Signature3 only two public files')
    bodies={}
    for name,limit in LIMITS.items():
        row=value['signatures'][name]
        if not isinstance(row,dict) or set(row)!={'sha256','bytes','base64'} or type(row['bytes']) is not int or not 0<row['bytes']<=limit:raise ValueError('Signature3 bounded public file')
        data=base64.b64decode(row['base64'],validate=True)
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Signature3 file integrity')
        bodies[name]=data
    return value,bodies

def write(path,data,mode=0o600):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())

def sync(path):
    fd=os.open(path,os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def save(value):
    part=RECEIPT.with_suffix('.part');write(part,p.encoded(value));os.replace(part,RECEIPT);sync(RECEIPT.parent)

def verify_command(argv,fingerprint):
    result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        env={'PATH':'/usr/bin:/usr/sbin','HOME':'/root','LC_ALL':'C'},timeout=30,check=False)
    if result.returncode or len(result.stdout)>65536 or len(result.stderr)>65536:raise ValueError('Actual native gpgv verification failed')
    rows=[line.split() for line in result.stdout.decode('ascii').splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
    if len(rows)!=1 or rows[0][2]!=fingerprint:raise ValueError('Native gpgv approved primary fingerprint required')
    return {'exit':0,'status_sha256':hashlib.sha256(result.stdout).hexdigest()}

def stage(raw):
    value,bodies=decode_packet(raw);protected(EXPORT,True);protected(RECEIPT.parent,True);protected(TARGET/'run',True)
    if any(os.path.lexists(path) for path in (RECEIPT,RECEIPT.with_suffix('.part'),RUN,*(EXPORT/name for name in LIMITS))):raise ValueError('Signature3 existing/uncertain operation; no replay')
    original={name:p.digest(protected(EXPORT/name)) for name in ('archive-export.json','Release','archive-keyring.gpg')}
    trust=p.strict(protected(ROOT/'config/phase2/archive-public-trust.json').read_bytes())
    if original['archive-export.json']!=value['archive_export_sha256'] or original['Release']!=value['release_sha256'] or original['archive-keyring.gpg']!=value['public_key_sha256'] or value['public_key_sha256']!=trust['public_keyring_sha256']:raise ValueError('Signature3 host/guest Release/export/public key differ')
    receipt=p.strict(protected(EXPORT/'archive-export.json').read_bytes())
    if receipt.get('kind')!='unsigned-flat-native-archive-export' or receipt.get('signed') is not False or receipt.get('published') is not False or set(path.name for path in EXPORT.iterdir())!=set(receipt['files'])|{'archive-export.json'}:raise ValueError('Signature3 exact unsigned export namespace required')
    key=(EXPORT/'archive-keyring.gpg').read_bytes();p.public_key_only(key)
    executable=protected(TARGET/'usr/bin/gpgv')
    version=subprocess.check_output(['/usr/sbin/chroot',str(TARGET),'/usr/bin/dpkg-query','-W','-f=${Version}','gnupg'],text=True,timeout=30).strip()
    record=p.strict(protected(Path('/var/log/toddy/packages')/('gnupg_'+version+'_amd64.json')).read_bytes())
    if record.get('installed') is not True or record.get('payload',{}).get('/usr/bin/gpgv',{}).get('sha256')!=p.digest(executable):raise ValueError('Native gpgv installed source ownership required')
    state={'version':1,'state':'public-signature3-staging-intended-no-replay','packet_sha256':hashlib.sha256(raw).hexdigest(),'public_input_sha256':original,
        'host_verified_receipt_sha256':value['host_verified_receipt_sha256'],'host_signed_receipt_sha256':value['host_signed_receipt_sha256'],
        'native_gpgv_sha256':p.digest(executable),'native_gpgv_package_version':version,'private_material_transferred':False}
    save(state);RUN.mkdir(mode=0o700);(RUN/'home').mkdir(mode=0o700)
    try:
        write(RUN/'keyring.gpg',key)
        for name,data in bodies.items():write(RUN/name,data)
        virtual='/'+RUN.relative_to(TARGET).as_posix()
        common=['/usr/sbin/chroot',str(TARGET),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C','HOME='+virtual+'/home',
            '/usr/bin/gpgv','--homedir',virtual+'/home','--keyring',virtual+'/keyring.gpg','--status-fd','1']
        reports={'Release.gpg':verify_command([*common,virtual+'/Release.gpg','/'+(EXPORT/'Release').relative_to(TARGET).as_posix()],trust['fingerprint']),
            'InRelease':verify_command([*common,'--output',virtual+'/clear',virtual+'/InRelease'],trust['fingerprint'])}
        if (RUN/'clear').read_bytes()!=(EXPORT/'Release').read_bytes():raise ValueError('Native InRelease cleartext differs from exact Release')
        if any(p.digest(protected(EXPORT/name))!=sha for name,sha in original.items()):raise ValueError('Signature3 original public input changed')
        for name,data in bodies.items():
            write(EXPORT/name,data,0o644)
            if p.digest(protected(EXPORT/name))!=hashlib.sha256(data).hexdigest():raise ValueError('Signature3 installed public bytes changed')
        sync(EXPORT)
        state.update(state='native-public-signatures-verified',signatures={name:hashlib.sha256(data).hexdigest() for name,data in bodies.items()},native_verification=reports,cleartext_equals_release=True,published=False)
    finally:
        protected(RUN,True);shutil.rmtree(RUN);sync(RUN.parent)
    state['public_temporary_home_removed']=not os.path.lexists(RUN);save(state);return state

def main():
    if sys.argv[1:] or os.geteuid()!=0 or Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/export3_public_signatures.py'):raise ValueError('Fixed root signature3 entry required')
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    inherited_media_lease();raw=sys.stdin.buffer.read(MAX_PACKET+1);print(json.dumps(stage(raw),sort_keys=True))

if __name__=='__main__':main()
