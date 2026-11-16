#!/usr/bin/env python3
"""Return only two verified public signatures to fixed native export3."""
import base64,hashlib,json,os,shlex,stat,subprocess,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(HERE),str(ROOT/'scripts/build/phase2')]
import phase2_candidate_vm as candidate
import export3_public_signatures as native
CONTEXT=ROOT/'.local/phase2/mvp-package-export-3';ASSETS=CONTEXT/'assets'


def digest(data):return hashlib.sha256(data).hexdigest()
def safe(path):
    path=Path(path);info=path.lstat()
    if path.resolve()!=path or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o022:raise ValueError('Owned exact public host input required')
    if info.st_size>native.MAX_PACKET:raise ValueError('Bounded public host input required')
    return path.read_bytes()

def fixed_context(generation=3):
    if type(generation) is not int or generation not in (3,4,5):raise ValueError('Only fixed signature export3/export4/export5 generation')
    return CONTEXT if generation==3 else ROOT/('.local/phase2/mvp-package-export-'+str(generation))

def verify_public(key,release,bodies,fingerprint,generation=3):
    with tempfile.TemporaryDirectory(prefix='public-signature-check-',dir=fixed_context(generation)) as directory:
        folder=Path(directory);(folder/'home').mkdir(mode=0o700)
        for name,data in {'keyring.gpg':key,'Release':release,**bodies}.items():(folder/name).write_bytes(data)
        common=['/usr/bin/gpgv','--homedir',str(folder/'home'),'--keyring',str(folder/'keyring.gpg'),'--status-fd','1']
        native.verify_command([*common,str(folder/'Release.gpg'),str(folder/'Release')],fingerprint)
        native.verify_command([*common,'--output',str(folder/'clear'),str(folder/'InRelease')],fingerprint)
        if (folder/'clear').read_bytes()!=release:raise ValueError('Host InRelease cleartext differs from exact Release')

def packet(generation=3):
    context=fixed_context(generation);assets=context/'assets'
    for folder in (context,assets):
        info=folder.lstat()
        if folder.resolve()!=folder or not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:raise ValueError('Private owned export3 context required')
    verified_raw=safe(context/'verified.json');signed_raw=safe(context/'signed.json')
    verified=json.loads(verified_raw);signed=json.loads(signed_raw)
    if verified.get('state')!='verified-unsigned-export-transfer' or verified.get('source')!='/mnt/lfs/sources/stage/toddy-package-export-'+str(generation) or verified.get('signed') is not False or verified.get('published') is not False:raise ValueError('Actual unsigned export3 transfer receipt required')
    if set(signed)!={'state','signatures','published'} or signed['state']!='signed-publicly-verified-export'+str(generation) or signed['published'] is not False or set(signed['signatures'])!=set(native.LIMITS):raise ValueError('Actual host signed3 receipt required')
    raw={name:safe(assets/name) for name in ('archive-export.json','Release','archive-keyring.gpg',*native.LIMITS)}
    for name in ('archive-export.json','Release','archive-keyring.gpg'):
        if verified.get('files',{}).get(name,{}).get('sha256')!=digest(raw[name]) or verified['files'][name].get('bytes')!=len(raw[name]):raise ValueError('Host public input differs from actual transferred bytes')
    if verified.get('archive_export_sha256')!=digest(raw['archive-export.json']):raise ValueError('Host export receipt changed')
    trust=json.loads((ROOT/'config/phase2/archive-public-trust.json').read_bytes());key=raw['archive-keyring.gpg']
    if digest(key)!=trust['public_keyring_sha256']:raise ValueError('Independent approved public key required')
    native.p.public_key_only(key)
    bodies={name:raw[name] for name in native.LIMITS}
    if any(signed['signatures'][name]!=digest(data) for name,data in bodies.items()):raise ValueError('Host signed3 public signature bytes changed')
    value={'version':1,'archive_export_sha256':digest(raw['archive-export.json']),'release_sha256':digest(raw['Release']),
        'public_key_sha256':digest(key),'host_verified_receipt_sha256':digest(verified_raw),'host_signed_receipt_sha256':digest(signed_raw),
        'signatures':{name:{'bytes':len(data),'sha256':digest(data),'base64':base64.b64encode(data).decode('ascii')} for name,data in bodies.items()}}
    encoded=native.p.encoded(value);native.decode_packet(encoded)
    verify_public(key,raw['Release'],bodies,trust['fingerprint'],generation)
    return encoded

def main():
    if sys.argv[1:]:raise SystemExit('No arbitrary path/action/signing-context arguments')
    result_path=CONTEXT/'native-signatures-verified.json'
    if os.path.lexists(result_path):raise ValueError('Preserve prior signature3 return receipt; no replay')
    encoded=packet();owned=candidate.owned();candidate.bases()
    result=subprocess.run(candidate.ssh()+['bash /opt/toddy-build/scripts/build/phase2/image_native.sh signatures-export3'],input=encoded,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=True)
    if len(result.stdout)>65536 or candidate.owned()!=owned:raise ValueError('Bounded actual same-candidate result required')
    value=json.loads(result.stdout)
    if value.get('state')!='native-public-signatures-verified' or value.get('packet_sha256')!=digest(encoded) or value.get('cleartext_equals_release') is not True or value.get('public_temporary_home_removed') is not True or set(value.get('native_verification',{}))!=set(native.LIMITS) or any(row.get('exit')!=0 for row in value['native_verification'].values()):raise ValueError('Actual native verification/cleanup receipt required')
    fd=os.open(result_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(native.p.encoded(value));stream.flush();os.fsync(stream.fileno())
    native.sync(CONTEXT)
    print(json.dumps({'state':value['state'],'receipt':str(result_path),'published':False,'private_material_transferred':False}))

if __name__=='__main__':main()
