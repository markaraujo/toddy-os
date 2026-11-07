#!/usr/bin/env python3
"""Export accepted foundation inputs for local owner testing; never publish binaries."""
import argparse,hashlib,json,shutil,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description='Export verified foundation ISO and corresponding source archives outside Git')
for name in ('iso','manifest','inventory','destination'):parser.add_argument(name,type=Path)
args=parser.parse_args()
states={r['id']:r['status'] for r in json.loads((root/'status.json').read_text())['milestones']}
if states['H12']!='completed' or states['H13'] not in ('in_progress','completed'):
 raise SystemExit('Foundation export requires completed H12 and active/completed H13')
for path in (args.iso,args.manifest,args.inventory):
 path=path.absolute()
 if path.resolve()!=path or not path.is_file() or not path.is_relative_to(root/'.local'):
  raise SystemExit('Use verified physical project-local artifact inputs')
work=args.destination.absolute()
if work.resolve()!=work or not work.is_relative_to(root/'.local/releases') or work.exists():
 raise SystemExit('Use a fresh physical project-local release destination')
manifest=json.loads(args.manifest.read_text());inventory=json.loads(args.inventory.read_text())
review=json.loads((root/'docs/evidence/H11-artifact-review.json').read_text())
if (not review['complete'] or not manifest['complete'] or manifest['validation_only'] is not False
 or manifest['media']['sha256']!=review['iso_sha256'] or manifest['media']['bytes']!=review['iso_bytes']
 or hashlib.sha256(args.inventory.read_bytes()).hexdigest()!=review['inventory_sha256']):
 raise SystemExit('Inputs differ from the independently reviewed artifact')
assert shutil.disk_usage(root).free>110*1024**3
work.mkdir(parents=True,mode=0o700)
sources={}
for row in inventory['components']:
 for item in row['sources']:
  assert Path(item['filename']).name==item['filename']
  if item['filename'] in sources:assert sources[item['filename']]['sha256']==item['sha256']
  sources[item['filename']]=item
assert len(sources)==review['corresponding_source_inputs']
checksums=[]
for name,row in sorted(sources.items()):
 p=root/'.local/sources'/name
 assert p.resolve()==p and p.is_file(),name
 with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],name
 checksums.append(row['sha256']+'  '+name)
(work/'SOURCE-SHA256SUMS').write_text('\n'.join(checksums)+'\n')
(work/'source-inputs.json').write_text(json.dumps({'source_count':len(sources),'sources':[sources[k] for k in sorted(sources)]},indent=2)+'\n')
with tarfile.open(work/'source-archives.tar','x') as out:
 for name in sorted(sources):
  p=root/'.local/sources'/name;info=out.gettarinfo(str(p),'sources/'+name)
  info.uid=info.gid=0;info.uname=info.gname='root';info.mtime=1793836800;info.mode=0o644
  with p.open('rb') as f:out.addfile(info,f)
# Read and verify every actual bundled source, not only its staging input.
with tarfile.open(work/'source-archives.tar') as inp:
 members=inp.getmembers();assert len(members)==len(sources)
 for member in members:
  assert member.isfile() and member.name.startswith('sources/')
  with inp.extractfile(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sources[member.name.removeprefix('sources/')]['sha256']
shutil.copyfile(args.inventory,work/'components.json')
shutil.copyfile(args.manifest,work/'result.json')
shutil.copyfile(args.iso,work/'toddy-foundation-x86_64.iso')
artifacts={}
for path in sorted(work.iterdir()):
 with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 artifacts[path.name]={'sha256':sha,'bytes':path.stat().st_size}
assert artifacts['toddy-foundation-x86_64.iso']['sha256']==review['iso_sha256']
report={'complete':True,'scope':'Verified local owner-testing artifact and source export; consult separate H13 G1 acceptance','artifact_directory':str(work.relative_to(root)),'artifacts':artifacts,'sources_verified_from_bundle':len(sources),'public_binary_release_authorized':False}
(work/'staging.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
