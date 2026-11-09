"""Revise only PAM's mistaken exact dependency; preserve its unpacked payload."""
import hashlib,json,shutil,stat,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from package_backend import PackageBackend
from stage_package import payload
from phase2.qualify_pam import qualify
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify_installed(record, *, pending=False):
    for name,row in record['payload'].items():
        p=TARGET/name.lstrip('/')
        if pending and name=='/etc/pam.d/other':
            assert not p.exists() and not p.is_symlink(),'Unexpected active PAM fallback policy'
            p=p.with_name('other.dpkg-new')
        st=p.lstat()
        # Shared directories can contain later payload; their identity remains.
        assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid']),name
        if 'symlink' in row:assert p.is_symlink() and str(p.readlink())==row['symlink'],name
        elif 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256'],name

def main():
    qualify(ROOT,LOG)
    backend=PackageBackend(TARGET);assert backend.native
    failed=json.loads(Path('/var/log/toddy/build/b02-linux-pam-install-2.failed.json').read_text())
    assert failed['recipe_exit']==1 and failed['postcheck_exit'] is None
    assert 'Version of libxcrypt on system is 4.5.2-1+toddy1' in Path('/var/log/toddy/build/b02-linux-pam-install-2.log').read_text()
    assert backend.run('dpkg-query','-W','-f=${Status} ${Version}','linux-pam',capture_output=True,text=True).stdout=='install ok unpacked 1.7.2-1+toddy1'
    assert backend.run('dpkg-query','-W','-f=${Status} ${Version}','libxcrypt',capture_output=True,text=True).stdout=='install ok installed 4.5.2-1+toddy1'
    name='linux-pam_1.7.2-1+toddy1_amd64';archive=Path('/var/cache/toddy/packages')/(name+'.deb');record_path=Path('/var/log/toddy/packages')/(name+'.json');record=json.loads(record_path.read_text())
    assert not record['installed'] and digest(archive)==record['archive_sha256']
    verify_installed(record,pending=True)
    stage=TARGET/'sources/stage/phase2-linux-pam-metadata-2';receipt=LOG/'pam-metadata-recovery-2.json'
    assert not stage.exists() and not receipt.exists(),'Reconcile metadata operation, never replay'
    state={'state':'verified-unpacked','previous_version':record['version'],'previous_archive_sha256':record['archive_sha256'],'previous_record_sha256':digest(record_path),'version':'1.7.2-1+toddy2','scope':'Exact dependency revision only; entire native unpacked payload must remain identical'}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(state,indent=2)+'\n');part.replace(receipt)
    save();temporary=backend.workspace()/archive.name;assert not temporary.exists();shutil.copy2(archive,temporary)
    data=temporary.with_suffix('.data.tar');assert not data.exists()
    try:
        with data.open('xb') as f:backend.run('dpkg-deb','--fsys-tarfile','/'+str(temporary.relative_to(TARGET)),stdout=f)
        stage.mkdir()
        backend.run('tar','--extract','--numeric-owner','--same-permissions','--file','/'+str(data.relative_to(TARGET)),'--directory','/'+str(stage.relative_to(TARGET)))
    finally:
        temporary.unlink()
        if data.exists():data.unlink()
    assert payload(stage)==record['payload'],'Preserved archive extraction must match complete original payload'
    state['state']='stage-identical';save()
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'linux-pam','1.7.2-1+toddy2',str(stage),'--source','Linux-PAM-1.7.2.tar.xz','--recipe','scripts/build/phase2/recover_pam_metadata.py','--depends','glibc (>= 2.44-1), libxcrypt (= 4.5.2-1+toddy1), systemd (>= 261.2-1+toddy2)','--conffile','/etc/pam.d/other','--install'],cwd=ROOT,check=True)
    revised=json.loads(Path('/var/log/toddy/packages/linux-pam_1.7.2-1+toddy2_amd64.json').read_text());assert revised['installed'] and revised['payload']==record['payload']
    verify_installed(record);state.update(state='complete',new_archive_sha256=revised['archive_sha256'],unchanged_payload_entries=len(record['payload']));save();print(json.dumps(state))

if __name__=='__main__':main()
