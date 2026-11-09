"""Controlled own-package revision of exactly four Systemd runtime files plus PAM."""
import hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from package_backend import PackageBackend
from stage_package import payload
from qualify_systemd_pam import qualify
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2');WORK=TARGET/'sources/phase2/work/systemd-pam-1'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify_installed(record,excluded=()):
    for name,row in record['payload'].items():
        if name in excluded:continue
        p=TARGET/name.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid']),name
        if 'symlink' in row:assert p.is_symlink() and str(p.readlink())==row['symlink'],name
        elif 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256'],name

def main():
    candidate,abi=qualify();backend=PackageBackend(TARGET);assert backend.native
    assert backend.run('dpkg-query','-W','-f=${Status} ${Version}','systemd',capture_output=True,text=True).stdout=='install ok installed 261.2-1+toddy2'
    stem='systemd_261.2-1+toddy2_amd64';archive=Path('/var/cache/toddy/packages')/(stem+'.deb');record_path=Path('/var/log/toddy/packages')/(stem+'.json');old=json.loads(record_path.read_text())
    assert old['installed'] and digest(archive)==old['archive_sha256'];verify_installed(old)
    stage=TARGET/'sources/stage/phase2-systemd-pam-3';receipt=LOG/'systemd-pam-install-3.json'
    assert not stage.exists() and not receipt.exists(),'Reconcile prior transaction; never replay'
    assert not Path('/var/cache/toddy/packages/systemd_261.2-1+toddy3_amd64.deb').exists()
    assert shutil.disk_usage(TARGET).free>=16*1024**3+128*1024**2
    state={'state':'verified-predecessor','previous_version':old['version'],'previous_archive_sha256':old['archive_sha256'],'previous_record_sha256':digest(record_path),'version':'261.2-1+toddy3','private_export_surface':abi,'scope':'Same-version four runtime replacements and new PAM module/user policy only; native cold boot/session/recovery still mandatory'}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();temporary=backend.workspace()/archive.name;assert not temporary.exists();shutil.copy2(archive,temporary)
    try:
        # The71MB own data archive is held in RAM rather than allocating another
        # uncompressed target copy. Native tar preserves numeric owner/modes.
        data=backend.run('dpkg-deb','--fsys-tarfile','/'+str(temporary.relative_to(TARGET)),capture_output=True).stdout
        stage.mkdir();backend.run('tar','--extract','--numeric-owner','--same-permissions','--file','-','--directory','/'+str(stage.relative_to(TARGET)),input=data)
    finally:temporary.unlink()
    del data
    assert payload(stage)==old['payload'],'Complete predecessor archive must match recorded payload'
    replaced={'/usr/lib/systemd/'+n for n in ['systemd','systemd-executor','libsystemd-core-261.so','libsystemd-shared-261.so']}
    added={'/usr/lib/security/pam_systemd.so','/etc/pam.d/systemd-user'}
    assert set('/'+n for n in candidate['artifacts'])==replaced|added
    for relative,sha in candidate['artifacts'].items():
        destination=stage/relative
        if '/'+relative in added:assert not destination.exists() and not (TARGET/relative).exists()
        else:assert '/'+relative in old['payload']
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(WORK/'stage'/relative,destination);os.chown(destination,0,0)
        assert digest(destination)==sha
    expected=payload(stage)
    changed={n for n in old['payload'] if old['payload'][n]!=expected.get(n)}
    extras=set(expected)-set(old['payload']);assert changed==replaced
    assert extras==added|{'/etc/pam.d','/usr/lib/security'}
    state.update(state='stage-reviewed',replaced_paths=sorted(replaced),added_paths=sorted(extras),unchanged_existing_payload_entries=len(old['payload'])-len(replaced));save()
    depends=backend.run('dpkg-query','-W','-f=${Depends}','systemd',capture_output=True,text=True).stdout
    assert 'linux-pam' not in depends;depends+=', linux-pam (= 1.7.2-1+toddy2)'
    command=[sys.executable,str(ROOT/'scripts/build/stage_package.py'),'systemd','261.2-1+toddy3',str(stage),'--recipe','scripts/build/phase2/systemd-pam-install.sh','--depends',depends]
    for r in old['sources']:command+=['--source',r['filename']]
    conffiles=sorted(n for n,r in expected.items() if n.startswith('/etc/') and 'sha256' in r)
    for name in conffiles:command+=['--conffile',name]
    subprocess.run(command,cwd=ROOT,check=True)
    new_record=Path('/var/log/toddy/packages/systemd_261.2-1+toddy3_amd64.json');new=json.loads(new_record.read_text())
    assert not new['installed'] and new['payload']==expected,'Review entire built payload BEFORE installation'
    new_archive=Path('/var/cache/toddy/packages/systemd_261.2-1+toddy3_amd64.deb');assert digest(new_archive)==new['archive_sha256']
    state.update(state='archive-reviewed',archive_sha256=new['archive_sha256']);save()
    backend.install(new_archive);verify_installed(old,excluded=replaced);verify_installed(new)
    assert backend.run('dpkg-query','-W','-f=${Status} ${Version}','systemd',capture_output=True,text=True).stdout=='install ok installed 261.2-1+toddy3'
    new['installed']=True;new_record.write_text(json.dumps(new,indent=2)+'\n')
    state.update(state='installed-pending-native-boot',payload_entries=len(new['payload']),all_unrelated_payload_unchanged=True);save();print(json.dumps({'state':state['state'],'replaced':len(replaced),'added':len(extras),'payload_entries':len(new['payload'])}))
if __name__=='__main__':main()
