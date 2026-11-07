#!/usr/bin/env python3
"""Verify complete native compression/readback on a private metadata fixture."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from vm import ssh_args

ROOT = Path(__file__).resolve().parents[2]
REMOTE = r'''
import base64,hashlib,json,os,shutil,stat,struct,subprocess,sys,tempfile
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
root=Path('/mnt/lfs');base=Path(tempfile.mkdtemp(prefix='toddy-root-compression-',dir=root/'tmp'))
print('COMPRESSION_FIXTURE '+str(base),flush=True)
for name,body in SOURCES.items():(base/name).write_bytes(base64.b64decode(body))
sys.path[:0]=[str(base),'/opt/toddy-build/scripts/build']
import compress_root as compression
from package_backend import PackageBackend
backend=PackageBackend(root)
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
probe=Path(TOOL_FIXTURE)
assert probe.resolve()==probe and probe.parent==root/'sources/recovery' and probe.name.startswith('squashfs-native-')
result=json.loads((probe/'result.json').read_text())
assert result['complete'] and json.loads((probe/'driver.exit.json').read_text())['exit']==0
assert result['source_sha256']=='547b7b7f4d2e44bf91b6fc554664850c69563701deab9fd9cd7e21f694c88ea6'
tools={'accepted_package':False,'private_source_sha256':result['source_sha256'],'binaries':{}}
for name,sha in result['binaries'].items():
 path=probe/'squashfs-tools-4.7.5/squashfs-tools'/name;assert digest(path)==sha
 tools['binaries'][name]={'path':str(path),'sha256':sha}
before=digest(root/'var/lib/dpkg/status')
try:
 image=base/'image';image.mkdir(mode=0o755)
 (image/'usr/share/toddy').mkdir(parents=True)
 (image/'empty').mkdir()
 path=image/'ação\\literal\nfile';path.write_text('Private native roundtrip bytes\n');os.chown(path,18,18);path.chmod(0o4750)
 os.setxattr(path,'user.toddy',b'exact attribute bytes');os.link(path,image/'hardlink')
 (image/'symlink').symlink_to(path.name);os.link(image/'symlink',image/'symlink-hardlink',follow_symlinks=False)
 sparse=image/'sparse'
 with sparse.open('wb') as f:f.seek(8*1024*1024);f.write(b'tail')
 capability=image/'capability';shutil.copy2(root/'usr/bin/true',capability)
 def native(program,*args,**kw):return backend.run(program,*args,**kw)
 def virtual(path):return '/'+str(path.relative_to(root))
 native('bash','-c','exec /usr/sbin/setcap "$@"','setcap','cap_net_bind_service=ep',virtual(capability))
 native('setfacl','-m','u:101:r--',virtual(path))
 directory=image/'default-acl';directory.mkdir()
 native('setfacl','-m','u:101:r-x,d:u:101:r-x',virtual(directory))
 acl=native('bash','-c','cd "$1" && exec getfacl -R -P -p -n --skip-base --one-file-system .','capture',virtual(image),capture_output=True).stdout
 (image/'usr/share/toddy/live-root.acl').write_bytes(acl)
 for entry in [image,*image.rglob('*')]:os.utime(entry,ns=(1600000000123456789,1600000000123456789),follow_symlinks=False)
 expected=compression.snapshot(image,compression.tree_names(image))
 first=compression.compress(backend,image,base/'first',expected,tools,1793923200)
 assert first['complete'] and first['source_unchanged'] and not first['release_accepted']
 extracted=base/'first/extracted'
 assert (extracted/'sparse').stat().st_blocks*512<(extracted/'sparse').stat().st_size
 cases=[]
 def refused(label,call):
  try:call()
  except (ValueError,OSError) as error:cases.append({'case':label,'reason':str(error)})
  else:raise AssertionError(label+' was accepted')
 restored_expected=compression.format_manifest(expected,restored=True)
 def restored():
  for relative,row in restored_expected['entries'].items():
   os.utime(extracted/relative,ns=(row['mtime_ns'],row['mtime_ns']),follow_symlinks=False)
  result=compression.compare(restored_expected,compression.snapshot(extracted,compression.tree_names(extracted)))
  assert result['matches'],result
 def compare_failure(label,relative=None,field=None):
  result=compression.compare(compression.format_manifest(expected,restored=True),compression.snapshot(extracted,compression.tree_names(extracted)))
  assert not result['matches'],label
  if field:assert any(row['path']==relative and field in row['fields'] for row in result['changed']),result
  if label=='unexpected extracted entry':assert result['unknown']==['unexpected'],result
  if label=='split regular hardlink':assert not result['hardlinks_match'],result
  cases.append({'case':label,'comparison':result})
 changed=extracted/path.name;original=changed.read_bytes();timestamps=(changed.stat().st_atime_ns,changed.stat().st_mtime_ns)
 changed.write_bytes(original+b'changed');compare_failure('changed restored bytes',path.name,'sha256');changed.write_bytes(original);restored()
 extra=extracted/'unexpected';extra.write_text('unexpected\n');compare_failure('unexpected extracted entry');extra.unlink();restored()
 alias=extracted/'symlink';old=alias.readlink();alias.unlink();alias.symlink_to('sparse');compare_failure('changed symbolic link','symlink','symlink')
 alias.unlink();os.link(extracted/'symlink-hardlink',alias,follow_symlinks=False);restored()
 mode=changed.stat().st_mode & 0o7777;changed.chmod(0o600);compare_failure('changed restored mode',path.name,'mode');changed.chmod(mode);restored()
 os.setxattr(changed,'user.extra',b'unexpected');compare_failure('changed extended metadata',path.name,'xattrs');os.removexattr(changed,'user.extra');restored()
 link=extracted/'hardlink';held=base/'held-hardlink';shutil.copy2(link,held);link.unlink();shutil.copy2(held,link)
 compare_failure('split regular hardlink');link.unlink();os.link(changed,link);restored()
 refused('existing output generation',lambda:compression.compress(backend,image,base/'first',expected,tools,1793923200))
 refused('installed builder as image',lambda:compression.compress(backend,root,base/'invalid',expected,tools,1793923200))
 outside=base/'redirect';outside.symlink_to(base/'first')
 refused('redirected output',lambda:compression.compress(backend,image,outside,expected,tools,1793923200))
 path.write_bytes(original+b'input changed')
 refused('changed assembled source',lambda:compression.compress(backend,image,base/'not-created',expected,tools,1793923200))
 assert not (base/'not-created').exists();path.write_bytes(original);os.utime(path,ns=(1600000000123456789,1600000000123456789))
 second=compression.compress(backend,image,base/'second',expected,tools,1793923200)
 assert first['artifact_sha256']==second['artifact_sha256']
 broken=base/'truncated.squashfs';broken.write_bytes((base/'first/rootfs.squashfs').read_bytes()[:128])
 command=['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C',virtual(Path(tools['binaries']['unsquashfs']['path'])),'-strict-errors','-d',virtual(base/'broken-output'),virtual(broken)]
 failure=subprocess.run(command,capture_output=True,text=True)
 assert failure.returncode!=0
 cases.append({'case':'truncated compressed artifact','exit':failure.returncode,'stderr':failure.stderr})
 artifact=base/'first/rootfs.squashfs'
 refused('incorrect filesystem epoch',lambda:compression.superblock(artifact,1793923201))
 for label,flag,enabled in [('export metadata disabled',7,False),('extended attributes disabled',9,True)]:
  raw=bytearray(artifact.read_bytes());flags=struct.unpack_from('<H',raw,24)[0]
  struct.pack_into('<H',raw,24,flags | (1<<flag) if enabled else flags & ~(1<<flag))
  bad=base/('changed-flag-'+str(flag)+'.squashfs');bad.write_bytes(raw)
  refused(label,lambda:compression.superblock(bad,1793923200))
 initramfs_result=None
 if INITRAMFS:
  import copy,gzip
  import initramfs_input,initramfs_archive
  # Only the assembly journal is a metadata fixture. Compression, readback,
  # native runtime selection and archive creation execute their real code.
  # This thirteen-entry source is explicitly not a complete foundation root.
  evidence=base/'assembly';evidence.mkdir(mode=0o700)
  manifest=evidence/'image-manifest.json';compression.atomic_json(manifest,expected)
  journal_path=evidence/'assembly.json'
  journal={'assembled':True,'release_profile':False,'evidence':str(evidence),'image':str(image),
   'assembler_sha256':digest(base/'assemble_root.py'),
   'actions':[{'step':'image-manifest','report':manifest.name,'finished':'private metadata fixture',
    'sha256':digest(manifest)}]}
  compression.atomic_json(journal_path,journal)
  def attach(profile):
   journal['release_profile']=profile;compression.atomic_json(journal_path,journal)
   first['assembly_binding']={'journal':str(journal_path),'journal_sha256':digest(journal_path),
    'manifest':str(manifest),'manifest_sha256':digest(manifest),'release_profile':profile}
   compression.atomic_json(base/'first/compression.json',first)
  attach(False)
  input_path=base/'first/compression.json'
  def binding():return initramfs_input.verify(root,input_path,False)
  bound=binding();assert bound['rootfs_sha256']==first['artifact_sha256']
  media_id=hashlib.sha256(b'private compression-bound initramfs').hexdigest()
  generated=initramfs_archive.assemble(root,base/'initramfs',Path('/var/log/toddy/packages'),
    base/'live_init.sh',base/'live_media.sh',media_id,bound['rootfs_sha256'],bound['epoch'])
  initramfs_input.unchanged(root,bound)
  raw=gzip.decompress((base/'initramfs/initramfs.cpio.gz').read_bytes())
  assert initramfs_archive.validate_newc(raw,generated['entries'],bound['epoch'])==generated['entry_count']
  assert (base/'initramfs/runtime/etc/toddy-live/rootfs.sha256').read_text()==first['artifact_sha256']+'\n'
  initial=len(cases)
  original_report=input_path.read_bytes()
  for label,alter in (
   ('compression has no assembly binding',lambda row:row.pop('assembly_binding')),
   ('unfinished compression',lambda row:row.update(complete=False)),
   ('wrong compression profile',lambda row:row['assembly_binding'].update(release_profile=True)),
   ('failed native extraction',lambda row:row['steps'][1].update(exit=1)),
   ('missing native stage',lambda row:row['steps'].pop()),
   ('invalid archive epoch',lambda row:row.update(epoch=2**32)),
   ('wrong compressed artifact digest',lambda row:row.update(artifact_sha256='0'*64))):
   changed=copy.deepcopy(first);alter(changed);compression.atomic_json(input_path,changed)
   refused(label,binding);input_path.write_bytes(original_report)
  for label,changed_path in (
    ('changed assembly journal',journal_path),('changed final assembly manifest',manifest),
    ('changed native extraction log',base/'first/extract.log')):
   original_bytes=changed_path.read_bytes();changed_path.write_bytes(original_bytes+b'\n')
   refused(label,binding);changed_path.write_bytes(original_bytes)
  source=base/'first/source-manifest.json';original_bytes=source.read_bytes()
  compression.atomic_json(source,{'entries':{},'hardlink_groups':[]})
  refused('source manifest from another generation',binding);source.write_bytes(original_bytes)
  original_bytes=artifact.read_bytes();artifact.write_bytes(original_bytes[:-1]+bytes([original_bytes[-1]^1]))
  refused('changed compressed root',binding)
  refused('bound input changes during archive creation',lambda:initramfs_input.unchanged(root,bound))
  artifact.write_bytes(original_bytes)
  artifact.chmod(0o666);refused('unprotected compressed root',binding);artifact.chmod(0o644)
  held=base/'held.squashfs';artifact.rename(held);artifact.symlink_to(held)
  refused('redirected compressed root',binding);artifact.unlink();held.rename(artifact)
  assert binding()==bound
  attach(True)
  release_binding=initramfs_input.verify(root,input_path,True)
  assert release_binding['rootfs_sha256']==bound['rootfs_sha256']
  refused('release compression used as H10 input',binding)
  attach(False);assert binding()==bound
  initramfs_result={'binding':bound,'release_binding_verified':True,
   'negative_cases':cases[initial:],'archive_entries':generated['entry_count'],'gzip_bytes':generated['gzip_bytes'],
   'gzip_sha256':generated['gzip_sha256'],'embedded_actual_compressed_root_digest':True,
   'native_archive_and_readback':True,'assembly_journal_is_metadata_fixture':True,
   'full_foundation_assembly_or_boot_verified':False,
   'component_sha256':{name:digest(base/name) for name in ('initramfs_input.py','initramfs_archive.py','compress_root.py')}}
 assert digest(root/'var/lib/dpkg/status')==before
 reports={str(p.relative_to(base)):p.read_text() for d in ['first','second'] for p in (base/d).glob('*.json')}
 logs={str(p.relative_to(base)):p.read_text() for d in ['first','second'] for p in (base/d).glob('*.log')}
 report={'fixture':str(base),'first':first,'second':second,'negative_cases':cases,'reports':reports,'logs':logs,
 'same_fixture_two_generations_identical':True,'sparse_allocation_preserved':True,'installed_status_unchanged':True,
 'component_sha256':digest(base/'compress_root.py'),'initramfs':initramfs_result,'full_foundation_image_or_boot_verified':False}
 print('COMPRESSION_RESULT '+json.dumps(report),flush=True)
 shutil.rmtree(base)
except BaseException:
 print('PRESERVED_COMPRESSION_FIXTURE '+str(base),flush=True)
 raise
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool_fixture')
    parser.add_argument('--initramfs', action='store_true', help='Bind and build a native initramfs from the actual compressed fixture')
    args = parser.parse_args()
    sources = {name: base64.b64encode((ROOT / 'scripts/build/h10' / name).read_bytes()).decode()
               for name in ('compress_root.py', 'copy_selected_root.py', 'restore_live_acls.sh')}
    if args.initramfs:
        for name in ('initramfs_input.py', 'initramfs_archive.py', 'initramfs_runtime.py',
                     'assemble_root.py', 'live_init.sh', 'live_media.sh'):
            sources[name] = base64.b64encode((ROOT / 'scripts/build/h10' / name).read_bytes()).decode()
    sources['package_backend.py'] = base64.b64encode((ROOT / 'scripts/build/package_backend.py').read_bytes()).decode()
    run = subprocess.run(ssh_args() + ['python3 -B -'],
                         input='SOURCES=' + repr(sources) + '\nTOOL_FIXTURE=' + repr(args.tool_fixture) + '\nINITRAMFS=' + repr(args.initramfs) + '\n' + REMOTE,
                         text=True, capture_output=True, timeout=600)
    raw = (run.stdout + run.stderr).encode();sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h10-root-compression-' + sha + '.log');path.write_bytes(raw)
    print(json.dumps({'exit': run.returncode, 'report': str(path), 'sha256': sha}))
    if run.returncode:
        print(run.stdout + run.stderr)
        raise SystemExit(run.returncode)
    report = json.loads(next(line.removeprefix('COMPRESSION_RESULT ') for line in run.stdout.splitlines()
                             if line.startswith('COMPRESSION_RESULT ')))
    print(json.dumps({'entries': report['first']['entries'], 'bytes': report['first']['artifact_bytes'],
                      'negative_cases': len(report['negative_cases']), 'two_generations_identical': True,
                      'initramfs_negative_cases': len(report['initramfs']['negative_cases']) if report['initramfs'] else None,
                      'full_foundation_image_or_boot_verified': False}))


if __name__ == '__main__':
    main()
