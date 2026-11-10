"""Preserve installed Terminal code; remove unbuilt addon metadata/retain notices."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from package_backend import PackageBackend
from stage_package import payload
from phase2.schema_union_install import verify
from phase2.qualify_gnome_terminal import qualify
from phase2.package_copyright import write_copyright
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 qualify(R);backend=PackageBackend(T);assert backend.native
 failed=json.loads(Path('/var/log/toddy/build/b02-gnome-terminal-install.failed.json').read_text());assert failed['recipe_exit']==0 and failed['postcheck_exit']==1
 assert 'Failed to open /dev/null: Permission denied' in Path('/var/log/toddy/build/b02-gnome-terminal-install.log').read_text()
 assert backend.run('dpkg-query','-W','-f=${Status} ${Version}','gnome-terminal',capture_output=True,text=True).stdout=='install ok installed 3.60.0-1+toddy1'
 record=Path('/var/log/toddy/packages/gnome-terminal_3.60.0-1+toddy1_amd64.json');old=json.loads(record.read_text());assert old['installed'] and len(old['payload'])==346;verify(old)
 archive=Path('/var/cache/toddy/packages/gnome-terminal_3.60.0-1+toddy1_amd64.deb');assert digest(archive)==old['archive_sha256']=='fc0d7765aa21dacf2ab5a66b77de8462138e680ee68e1d5d9704c89d1d568607'
 depends=backend.run('dpkg-query','-W','-f=${Depends}','gnome-terminal',capture_output=True,text=True).stdout
 stage=T/'sources/stage/phase2-gnome-terminal-metadata-2';receipt=L/'terminal-metadata-recovery-2.json';assert not stage.exists() and not receipt.exists()
 assert not Path('/var/cache/toddy/packages/gnome-terminal_3.60.0-1+toddy2_amd64.deb').exists()
 excluded='/usr/share/metainfo/org.gnome.Terminal.Nautilus.metainfo.xml';legal='/usr/share/doc/gnome-terminal/'
 state={'state':'verified-installed','scope':'Existing Terminal code/runtime/schema/user configuration preserved; remove only metadata advertising unbuilt Nautilus extension and retain full bundled notices. No source/compiler/original suite/first install replay. Original missing /dev/null post failure retained; new consumer private device namespace.','old_version':'3.60.0-1+toddy1','new_version':'3.60.0-1+toddy2','old_archive_sha256':old['archive_sha256'],'old_record_sha256':digest(record),'excluded_addon_metadata':excluded,'excluded_sha256':old['payload'][excluded]['sha256']}
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
 (stage/excluded.lstrip('/')).unlink()
 write_copyright(stage,'gnome-terminal',['gnome-terminal-3.60.0.tar.gz'])
 doc=stage/'usr/share/doc/gnome-terminal';common=R/'LICENSES/third-party/LGPL-2.1.txt';shutil.copyfile(common,doc/'LGPL-2.1.txt')
 with (doc/'copyright').open('ab') as f:f.write(b'\nBundled per-file LGPL2.1 terms; complete text:\n'+common.read_bytes())
 current=payload(stage);runtime={k:v for k,v in old['payload'].items() if not k.startswith(legal) and k!=excluded}
 assert runtime=={k:v for k,v in current.items() if not k.startswith(legal)}
 state.update(state='metadata-prepared',unchanged_runtime_entries=len(runtime),legal_payload_changes=[k for k in sorted(set(old['payload'])|set(current)) if old['payload'].get(k)!=current.get(k) and k.startswith(legal)]);save()
 subprocess.run([sys.executable,str(R/'scripts/build/stage_package.py'),'gnome-terminal','3.60.0-1+toddy2',str(stage),'--source','gnome-terminal-3.60.0.tar.gz','--recipe','scripts/build/phase2/recover_terminal_metadata.py','--depends',depends,'--install'],cwd=R,check=True)
 new=json.loads(Path('/var/log/toddy/packages/gnome-terminal_3.60.0-1+toddy2_amd64.json').read_text());assert new['installed'];verify(new)
 assert runtime=={k:v for k,v in new['payload'].items() if not k.startswith(legal)}
 assert not (T/excluded.lstrip('/')).exists()
 state.update(state='complete',new_archive_sha256=new['archive_sha256'],new_owned_entries=len(new['payload']));save();print(json.dumps(state))
if __name__=='__main__':main()
