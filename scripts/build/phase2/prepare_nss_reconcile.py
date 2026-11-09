"""Finish only the rejected NSS manifest hunk after full partial-state review."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,tarfile
root=Path('/opt/toddy-build');source=Path('/mnt/lfs/sources/phase2/inputs/nss-3.126');work=Path('/mnt/lfs/sources/phase2/work/nss-1');log=Path('/var/log/toddy/phase2');receipt=log/'nss-input-reconcile-1.json'
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=Path('/var/log/toddy/build/build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json')) and not list(log.glob('nss-1.*'))
assert not receipt.exists() and source.is_dir() and not work.exists() and not (source/'toddy-prepared.json').exists()
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
patch=json.loads((root/'config/phase2/nss-patches.lock.json').read_text());assert digest(root/patch['patch_file'])==patch['patch_sha256']
archive=Path('/mnt/lfs/sources/nss-3.126.tar.gz');official=archive.with_name('nss-standalone-1.patch')
assert digest(archive)==patch['source_sha256'] and digest(official)==patch['official_patch_sha256']
original={};dirs=set()
with tarfile.open(archive) as tar:
 for member in tar:
  parts=Path(member.name).parts;assert parts[0]=='nss-3.126' and '..' not in parts
  name='/'.join(parts[1:])
  if member.isdir():dirs.add(name);continue
  assert member.isfile(),'No unreviewed source link'
  original[name]=hashlib.sha256(tar.extractfile(member).read()).hexdigest()
expected=dict(original);expected.update({k:v for k,v in patch['expected_changed_files'].items() if k!='nss/manifest.mn'})
expected['nss/manifest.mn.orig']=patch['original_manifest_sha256']
reject=source/'nss/manifest.mn.rej';assert reject.is_file()
reject_text=reject.read_text();assert '-DIRS = coreconf lib cmd cpputil gtests\n+DIRS = coreconf lib cmd cpputil gtests config' in reject_text
expected['nss/manifest.mn.rej']=digest(reject)
actual={str(f.relative_to(source)):digest(f) for f in source.rglob('*') if f.is_file() and not f.is_symlink()}
assert actual==expected and not any(f.is_symlink() for f in source.rglob('*')),'Partial source differs; never replay unknown writes'
manifest=source/'nss/manifest.mn';assert digest(manifest)==patch['original_manifest_sha256']
before=manifest.read_bytes();assert before.count(b'DIRS = coreconf lib cmd cpputil gtests\n')==1
after=before.replace(b'DIRS = coreconf lib cmd cpputil gtests\n',b'DIRS = coreconf lib cmd cpputil gtests config\n');assert hashlib.sha256(after).hexdigest()==patch['expected_changed_files']['nss/manifest.mn']
record={'state':'reviewed-before-write','source':str(source),'work':str(work),'original_regular_files':len(original),'before_partial_regular_files':len(actual),'patch':patch,'retained_patch_reject':reject_text,'reject_sha256':digest(reject),'recovery':'Inspect manifest/reject/receipt/work before any retry; never apply original or adjusted whole patch to partial source'}
receipt.write_text(json.dumps(record,indent=2)+'\n')
manifest.write_bytes(after);reject.unlink();(source/'nss/manifest.mn.orig').unlink()
expected=dict(original);expected.update(patch['expected_changed_files'])
assert {str(f.relative_to(source)):digest(f) for f in source.rglob('*') if f.is_file()}==expected
recipe=(root/'scripts/build/phase2/nss-build.sh').read_bytes();probe=(root/'scripts/build/phase2/nss-probe.c').read_bytes()
(source/'toddy-build.sh').write_bytes(recipe);(source/'toddy-probe.c').write_bytes(probe)
row=next(r for r in json.loads((root/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='nss')
prepared={'source_sha256':row['sha256'],'reference':row['reference'],'book_page_sha256':row['book_page_sha256'],'recipe_sha256':hashlib.sha256(recipe).hexdigest(),'probe_sha256':hashlib.sha256(probe).hexdigest(),'source_patches':[{'path':name,'before_sha256':original.get(name),'after_sha256':sha,'patch_sha256':patch['patch_sha256']} for name,sha in sorted(patch['expected_changed_files'].items())],'patch_reconciliation_receipt':str(receipt)}
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n');work.mkdir();os.chown(work,101,101)
record.update({'state':'complete','only_reconciled_source_path':'nss/manifest.mn','patch_tool_backups_removed_after_full_identity_check':True,'source_files_final':len(expected),'prepared_sha256':digest(source/'toddy-prepared.json')});receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'state':record['state'],'original_regular_files':len(original),'source_patch_paths':list(patch['expected_changed_files']),'receipt':str(receipt)}))
