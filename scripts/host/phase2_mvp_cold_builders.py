#!/usr/bin/env python3
"""Only two unreferenced H07 builder backups; opaque reversible custody."""
import hashlib,json,os,stat,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import phase2_compress_cold_checkpoints as cold
import phase2_candidate_vm as candidate
ROOT=cold.ROOT
PROFILES={
 'h07-native-crypto-builder.qcow2':{'manifest':'h07-native-crypto.json','manifest_sha256':'5773f3d1bfe98462d7b390423dd4ef4c76daf7b7cd711421646abfd1f2884c1e',
  'sha256':'6a77a6e96e2b57b30563ea3376b25662e72e4a2d9b7b7fd02628bd3e0ca80d95','device':66306,'inode':11832394,'bytes':6102843392,'allocated':6071943168,'mtime_ns':1793944970541824335,'ctime_ns':1793944970541824335},
 'h07-native-services-builder.qcow2':{'manifest':'h07-native-services.json','manifest_sha256':'82c43defc19d31017554f2673a5eca6fed81f343ea0ea10c67fff936f4b33048',
  'sha256':'04f0d30eaf79e029948feae68255b20c3cab9a79dd4d67756af5128d6de44519','device':66306,'inode':11832772,'bytes':6299451392,'allocated':6273445888,'mtime_ns':1793953098338625719,'ctime_ns':1793953098338625719}}

def canonical(path):
 path=Path(path)
 if not path.is_absolute() or not path.is_relative_to(ROOT/'.local') or not path.exists() or path.resolve(strict=True)!=path:raise ValueError('Only canonical project-local image paths')
 return path

def manifest(name):
 expected=PROFILES[name];path=canonical(ROOT/'.local/vm/checkpoints'/expected['manifest'])
 if cold.sha(path)!=expected['manifest_sha256']:raise ValueError('Exact historical checkpoint manifest changed')
 value=json.loads(path.read_bytes())
 if value.get('base_sha256')!='04e8f2461a16a44e78a370284471f29616cdd9baf1893df25807b71f985b6c94' or value['disks']['builder']!={'file':name,'sha256':expected['sha256']}:raise ValueError('Exact original builder receipt binding required')
 return path

def image_identity(path):
 path=canonical(path);expected=PROFILES[path.name];info=path.lstat();manifest(path.name)
 if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode)!=0o644 or info.st_uid!=os.getuid() or info.st_gid!=os.getgid() or info.st_nlink!=1 or
     (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)!=(expected['device'],expected['inode'],expected['bytes'],expected['mtime_ns'],expected['ctime_ns'])):
  raise ValueError('Exact historical builder inode/metadata changed')
 return expected

def resolve_backing(image,backing):
 """Resolve virtual QEMU aliases through actual retained mount receipts only."""
 virtual=Path(backing)
 if not virtual.is_absolute():return canonical(image.parent/virtual)
 if virtual.is_relative_to('/vm'):return canonical(ROOT/'.local/vm'/virtual.relative_to('/vm'))
 if virtual.is_relative_to('/evidence'):return canonical(ROOT/'.local/phase2'/virtual.relative_to('/evidence'))
 if virtual.is_relative_to(ROOT/'.local'):return canonical(virtual)
 result_path=canonical(image.parent/'result.json');value=json.loads(result_path.read_bytes());cid=value.get('container_id')
 if not isinstance(cid,str) or not __import__('re').fullmatch('[a-f0-9]{64}',cid):raise ValueError('Actual retained container mount binding required for virtual backing')
 mounts=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .Mounts}}',cid],text=True))
 matches=[]
 for row in mounts:
  destination=Path(row['Destination'])
  if row['Type']=='bind' and (virtual==destination or virtual.is_relative_to(destination)):
   matches.append((len(destination.parts),canonical(Path(row['Source'])/virtual.relative_to(destination))))
 if not matches:raise ValueError('Unresolved virtual backing; never infer from basename')
 return max(matches,key=lambda row:row[0])[1]

def active_attachments():
 ids=set()
 for label in ('toddy.candidate','toddy.boot-test'):
  values=subprocess.check_output(['docker','ps','-q','--filter','label='+label],text=True).split()
  if label=='toddy.candidate' and values:candidate.owned()
  ids.update(values)
 attached=set()
 for cid in ids:
  mounts=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .Mounts}}',cid],text=True))
  command=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .Config.Cmd}}',cid],text=True))
  for item in command:
   if not isinstance(item,str) or not item.startswith('file='):continue
   virtual=Path(item[5:].split(',',1)[0]);matches=[]
   for row in mounts:
    destination=Path(row['Destination'])
    if row['Type']=='bind' and (virtual==destination or virtual.is_relative_to(destination)):
     matches.append((len(destination.parts),canonical(Path(row['Source'])/virtual.relative_to(destination))))
   if not matches:raise ValueError('Unresolved active QEMU file attachment')
   attached.add(str(max(matches,key=lambda row:row[0])[1]))
 return attached

def no_open_qemu():
 wanted={(row['device'],row['inode']) for row in PROFILES.values()}
 for process in Path('/proc').iterdir():
  if not process.name.isdigit():continue
  try:
   if not (process/'comm').read_text().startswith(('qemu-system','qemu-img','qemu-nbd')):continue
   for descriptor in (process/'fd').iterdir():
    try:info=descriptor.stat()
    except FileNotFoundError:continue
    if (info.st_dev,info.st_ino) in wanted:raise ValueError('Selected checkpoint has open QEMU consumer')
  except FileNotFoundError:continue

def graph():
 no_open_qemu()
 candidate.bases() # Accepted foundation/B02 identity remains the original guard.
 selected={str(ROOT/'.local/vm/checkpoints'/name) for name in PROFILES}
 attached=active_attachments()
 if selected&attached:raise ValueError('Historical builder is actively attached')
 names=subprocess.check_output(['rg','--files','--hidden','--no-ignore','-g','*.qcow2','-g','*.img',str(ROOT/'.local/vm'),str(ROOT/'.local/phase2')],text=True).splitlines()
 rows=[];references=set()
 for name in names:
  image=canonical(Path(name));metadata=json.loads(subprocess.check_output(['qemu-img','info','-U','--output=json',str(image)],text=True))
  backing=resolve_backing(image,metadata['backing-filename']) if metadata.get('backing-filename') else None
  if str(image) in selected and (metadata['format']!='qcow2' or backing!=ROOT/'.local/vm/builder-base.img'):raise ValueError('Historical builder exact original base chain required')
  if backing is not None:
   if not backing.is_file():raise ValueError('Backing reference must resolve to an existing canonical file')
   references.add(str(backing))
  rows.append({'path':str(image.relative_to(ROOT)),'format':metadata['format'],'backing':metadata.get('backing-filename'),
      'absolute_backing':str(backing) if backing is not None else None})
 if selected&references:raise ValueError('Historical builder has incoming absolute backing reference')
 # A source is not an ancestor if no image in the complete graph references it.
 return {Path(path).name for path in references},rows

def inspect():
 _,rows=graph();facts={name:{**image_identity(ROOT/'.local/vm/checkpoints'/name),'checkpoint_manifest':str(manifest(name))} for name in PROFILES}
 return {'scope':'read-only fixed two historical builder backups','facts':facts,'absolute_graph':rows,
     'maximum_source_allocated_bytes':sum(row['allocated'] for row in facts.values()),'actual_gain_known':False}

if __name__=='__main__':
 if sys.argv[1:]==['inspect']:print(json.dumps(inspect(),sort_keys=True))
 elif sys.argv[1:]==['compress']:
  sys.argv=[sys.argv[0],'--profile','mvp-builders'];cold.main()
 else:raise SystemExit('Only fixed inspect|compress actions; no path arguments')
