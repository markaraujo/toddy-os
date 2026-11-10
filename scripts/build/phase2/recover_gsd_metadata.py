"""Correct two package revision declarations; preserve every unpacked GSD byte."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from package_backend import PackageBackend
from stage_package import payload
from phase2.schema_union_install import verify
from phase2.qualify_gnome_settings_daemon import qualify
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 qualify(R);backend=PackageBackend(T);assert backend.native
 failed=json.loads(Path('/var/log/toddy/build/b02-gnome-settings-daemon-install.failed.json').read_text());assert failed['recipe_exit']==1 and failed['postcheck_exit'] is None
 for n,v in [('libcanberra','0.30-1+toddy2'),('pulseaudio','17.0-1+toddy2')]:assert backend.run('dpkg-query','-W','-f=${Status} ${Version}',n,capture_output=True,text=True).stdout=='install ok installed '+v
 assert backend.run('dpkg-query','-W','-f=${Status} ${Version}','gnome-settings-daemon',capture_output=True,text=True).stdout=='install ok unpacked 50.1-1+toddy1'
 record_path=Path('/var/log/toddy/packages/gnome-settings-daemon_50.1-1+toddy1_amd64.json');old=json.loads(record_path.read_text());assert not old['installed'] and len(old['payload'])==458;verify(old)
 archive=Path('/var/cache/toddy/packages/gnome-settings-daemon_50.1-1+toddy1_amd64.deb');assert digest(archive)==old['archive_sha256']=='e9ad0df678c592c2c738597b1c39faecd0c74b0de00cf65cf8b2c0638ee7c511'
 depends=backend.run('dpkg-query','-W','-f=${Depends}','gnome-settings-daemon',capture_output=True,text=True).stdout
 for a,b in [('libcanberra (= 0.30-1+toddy1)','libcanberra (= 0.30-1+toddy2)'),('pulseaudio (= 17.0-1+toddy1)','pulseaudio (= 17.0-1+toddy2)')]:assert depends.count(a)==1;depends=depends.replace(a,b)
 stage=T/'sources/stage/phase2-gnome-settings-daemon-metadata-2';receipt=L/'gsd-metadata-recovery-2.json';assert not stage.exists() and not receipt.exists()
 assert not Path('/var/cache/toddy/packages/gnome-settings-daemon_50.1-1+toddy2_amd64.deb').exists()
 state={'state':'verified-unpacked','scope':'Correct only two native dependency revisions, existing same upstream libraries retained. All458payload entries must remain identical; no compiler/original/stage replay.','old_version':'50.1-1+toddy1','new_version':'50.1-1+toddy2','old_archive_sha256':old['archive_sha256'],'old_record_sha256':digest(record_path),'new_depends':depends}
 def save():
  part=receipt.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(state,indent=2)+'\n');part.replace(receipt)
 save();temporary=backend.workspace()/archive.name;data=temporary.with_suffix('.data.tar');assert not temporary.exists() and not data.exists();shutil.copy2(archive,temporary)
 try:
  with data.open('xb') as f:backend.run('dpkg-deb','--fsys-tarfile','/'+str(temporary.relative_to(T)),stdout=f)
  stage.mkdir();backend.run('tar','--extract','--numeric-owner','--same-permissions','--file','/'+str(data.relative_to(T)),'--directory','/'+str(stage.relative_to(T)))
 finally:
  temporary.unlink()
  if data.exists():data.unlink()
 assert payload(stage)==old['payload'];state['state']='stage-identical';save()
 subprocess.run([sys.executable,str(R/'scripts/build/stage_package.py'),'gnome-settings-daemon','50.1-1+toddy2',str(stage),'--source','gnome-settings-daemon-50.1.tar.xz','--recipe','scripts/build/phase2/recover_gsd_metadata.py','--depends',depends,'--install'],cwd=R,check=True)
 new=json.loads(Path('/var/log/toddy/packages/gnome-settings-daemon_50.1-1+toddy2_amd64.json').read_text());assert new['installed'] and new['payload']==old['payload'];verify(new)
 state.update(state='complete',new_archive_sha256=new['archive_sha256'],unchanged_payload_entries=len(old['payload']));save();print(json.dumps(state))
if __name__=='__main__':main()
