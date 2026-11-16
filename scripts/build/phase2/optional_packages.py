#!/usr/bin/env python3
"""Stage optional Toddy source payloads; no install, network or lifecycle scripts.

Agent vendor input must match the complete accepted B01 npm archive/file/legal
inventory. Missing or changed custody blocks staging rather than shrinking scope.
"""
import argparse
import ast
import base64
import hashlib
import io
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat
import tarfile

AGENT={
 'broker':('core.py','engine.py','configured_engine.py','text.py','profile_registry.py','profile_runtime.py',
           'memory.py','memory_api.py','memory_control.py','automation.py','automation_control.py',
           'integrations.py','skill_documents.py','profiles.py','protocol.py','scheduler.py','service.py','tasks.py',
           'io.github.markaraujo.Toddy.Service1.xml'),
 'tools':('native.py','child.py','scoped.py','scoped_child.py'),
 'local':('server.py','managed.py'),
 'acquisition':('choices.py','cli.py','download.py'),
}
WORKER=('worker.mjs','framing.mjs','provider.mjs','local-transport.mjs','package.json','package-lock.json')
VOICE=('artifacts.py','process.py','session.py','child.py','catalog.py','controller.py','candidates.json')
PLUGINS=('atspi_read.py','browser.py','limits.py','mcp.py','skills.py')


class PackageBlocked(ValueError):pass


def digest(data):return hashlib.sha256(data).hexdigest()

def encoded(value):return (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()


class Payload:
 def __init__(self,root,destination,name,version):
  self.root=Path(root);self.destination=Path(destination);self.name=name;self.version=version
  if not self.root.is_absolute() or self.root.resolve()!=self.root or not self.root.is_dir():
   raise PackageBlocked('canonical_repository_required')
  if not self.destination.is_absolute() or self.destination.resolve()!=self.destination or \
    self.destination.exists() or self.destination.is_symlink() or not self.destination.parent.is_dir():
   raise PackageBlocked('fresh_canonical_stage_required')
  if not re.fullmatch(r'[0-9][0-9A-Za-z.+:~_-]{0,127}',version):raise PackageBlocked('invalid_version')
  self.inputs={};self.files={};self.content={};self.dependencies=['toddy-assistant']
  recipe=Path(__file__).read_bytes()
  self.inputs['scripts/build/phase2/optional_packages.py']={'sha256':digest(recipe),'bytes':len(recipe)}

 def source(self,relative):
  path=self.root/relative
  try:
   if any(component.is_symlink() for component in (path,*path.parents)):raise PackageBlocked('source_symlink')
   info=path.lstat()
   if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise PackageBlocked('source_regular_file_required')
   data=path.read_bytes()
  except OSError:raise PackageBlocked('required_source_missing:'+relative) from None
  self.inputs[relative]={'sha256':digest(data),'bytes':len(data)}
  return data

 def put(self,path,data,mode=0o644,source='generated'):
  if not path.startswith('/') or '..' in PurePosixPath(path).parts or path in self.content:
   raise PackageBlocked('payload_collision')
  if data.startswith((b'\x7fELF',b'MZ',b'\xfe\xed\xfa\xce',b'\xfe\xed\xfa\xcf',b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe',
    b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca')):
   raise PackageBlocked('native_artifact_requires_separate_qualification')
  self.content[path]=data
  self.files[path]={'sha256':digest(data),'bytes':len(data),'mode':format(mode,'04o'),'source':source}

 def copy(self,relative,path):self.put(path,self.source(relative),source=relative)

 def python(self,source_dir,target_dir,names):
  self.put(target_dir+'/__init__.py',b'"""Original Toddy OS optional component."""\n')
  for name in names:self.copy(source_dir+'/'+name,target_dir+'/'+name)

 def legal(self,description):
  base='/usr/share/doc/'+self.name+'/'
  self.copy('LICENSE',base+'copyright')
  self.copy('LICENSES/CC-BY-4.0.txt',base+'CC-BY-4.0.txt')
  self.put(base+'README',(description+'\n\nNo source stage proves installed runtime acceptance. This package depends on\n'
   'toddy-assistant, sole owner of the root namespace/shared/connection helpers.\n'
   'No root namespace init, credentials, user runtime data, models, autostart enablement,\n'
   'maintainer script or native host binary is owned by this payload. Original\n'
   'code MIT; original documentation/configuration CC BY4.0. Native dependency\n'
   'versions, ownership, archive transactions and real component behavior remain\n'
   'separate acceptance. See exact source/legal inventory in this directory.\n').encode())

 def finish(self,extra=None):
  record={'schema_version':1,'package':self.name,'version':self.version,'architecture':'all',
   'status':'optional-payload-staged-not-runtime-acceptance','offline_base':False,
   'native_archive_built':False,'installed':False,'depends_on_packages':self.dependencies,
   'source_inputs':dict(sorted(self.inputs.items())),'payload':dict(sorted(self.files.items())),
   'maintainer_scripts':[],'runtime_registrations_enabled':False}
  record.update(extra or {})
  self.put('/usr/share/doc/'+self.name+'/source-manifest.json',encoded(record))
  self.destination.mkdir(mode=0o755)
  for path,data in sorted(self.content.items()):
   target=self.destination/path.lstrip('/');target.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
   target.write_bytes(data);target.chmod(int(self.files[path]['mode'],8));os.utime(target,(0,0))
  for directory in sorted((p for p in self.destination.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
   directory.chmod(0o755);os.utime(directory,(0,0))
  self.destination.chmod(0o755);os.utime(self.destination,(0,0))
  return record


def vendor(builder,cache,notices):
 lock_bytes=builder.source('runtime/engine/package-lock.json')
 lock=json.loads(lock_bytes)
 evidence_bytes=builder.source('docs/evidence/B01-engine-components.json')
 evidence=json.loads(evidence_bytes)
 notice_lock_bytes=builder.source('config/phase2/engine-notices.lock.json')
 notice_lock=json.loads(notice_lock_bytes)
 rows={path:row for path,row in lock['packages'].items() if path}
 components={row['location']:row for row in evidence['components']}
 if evidence['lock_sha256']!=digest(lock_bytes) or evidence['notice_lock_sha256']!=digest(notice_lock_bytes) or \
   set(rows)!=set(components) or len(rows)!=88 or evidence.get('component_locations')!=88 or \
   evidence.get('distinct_archives')!=87 or evidence.get('missing_reviewed_terms'):
  raise PackageBlocked('complete_B01_vendor_custody_required')
 archives=set();file_count=0
 for location,row in sorted(rows.items()):
  relative=PurePosixPath(location)
  if relative.is_absolute() or '..' in relative.parts or relative.parts[0]!='node_modules':
   raise PackageBlocked('vendor_location')
  component=components[location]
  if component.get('lifecycle_scripts_executed') is not False or \
    component['version']!=row['version'] or component['integrity']!=row['integrity'] or \
    component['url']!=row['resolved'] or component['license']!=row['license']:
   raise PackageBlocked('vendor_lock_changed')
  try:
   algorithm,expected=row['integrity'].split('-',1)
   expected=base64.b64decode(expected,validate=True)
   archive=Path(cache)/('npm-'+expected.hex()+'.tgz')
   if algorithm!='sha512' or archive.is_symlink() or not archive.is_file():raise PackageBlocked('vendor_archive_missing')
   data=archive.read_bytes()
  except (OSError,ValueError):raise PackageBlocked('vendor_archive_missing_or_invalid') from None
  if len(data)!=component['archive_bytes'] or len(data)>64*1024**2 or \
    hashlib.sha512(data).digest()!=expected or digest(data)!=component['archive_sha256']:
   raise PackageBlocked('vendor_archive_integrity')
  archives.add(digest(data));payload={}
  with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as source:
   members=source.getmembers()
   if len(members)>20000 or sum(m.size for m in members)>128*1024**2:raise PackageBlocked('vendor_archive_bound')
   for member in members:
    path=PurePosixPath(member.name)
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!=component['archive_root']:
     raise PackageBlocked('vendor_archive_path')
    if member.isdir():continue
    if not member.isfile() or len(path.parts)<2:raise PackageBlocked('vendor_archive_special_file')
    name=PurePosixPath(*path.parts[1:]).as_posix()
    contents=source.extractfile(member).read()
    sha=digest(contents)
    if name in payload:
     if payload[name]!=sha:raise PackageBlocked('vendor_normalized_collision')
     continue
    payload[name]=sha
    builder.put('/usr/lib/toddy/worker/'+location+'/'+name,contents,
      0o755 if member.mode&0o111 else 0o644,'B01-npm:'+component['archive_sha256']+':'+name)
  manifest_sha=digest(json.dumps(payload,sort_keys=True,separators=(',',':')).encode())
  if len(payload)!=component['verified_files'] or manifest_sha!=component['file_manifest_sha256']:
   raise PackageBlocked('vendor_complete_file_inventory')
  metadata_path='/usr/lib/toddy/worker/'+location+'/package.json'
  metadata=builder.content.get(metadata_path,b'')
  if digest(metadata)!=component['package_metadata_sha256']:raise PackageBlocked('vendor_package_metadata')
  file_count+=len(payload)
  for notice in component['retained_notices']:
   contents=builder.content.get('/usr/lib/toddy/worker/'+location+'/'+notice['path'])
   if contents is None or digest(contents)!=notice['sha256'] or len(contents)!=notice['bytes']:
    raise PackageBlocked('vendor_original_notice')
 supplemental=[]
 for row in notice_lock['supplemental_notices']:
  try:
   path=Path(notices)/row['sha256']
   if path.is_symlink() or not path.is_file():raise PackageBlocked('supplemental_notice_missing')
   contents=path.read_bytes()
  except OSError:raise PackageBlocked('supplemental_notice_missing') from None
  if digest(contents)!=row['sha256']:raise PackageBlocked('supplemental_notice_integrity')
  builder.put('/usr/share/doc/toddy-agent/npm-supplemental-notices/'+row['sha256'],contents,source=row['url'])
  supplemental.append(row)
 if len(archives)!=87:raise PackageBlocked('vendor_distinct_archive_inventory')
 builder.put('/usr/share/doc/toddy-agent/npm-custody.json',encoded(evidence))
 builder.put('/usr/share/doc/toddy-agent/supplemental-notices.json',encoded(supplemental))
 return {'component_locations':88,'distinct_archives':87,'verified_files':file_count,
  'lock_sha256':digest(lock_bytes),'B01_evidence_sha256':digest(evidence_bytes),
  'lifecycle_scripts_executed':False,'native_binary_payload':False}


def stage_agent(root,destination,*,version='0.2.0-1+toddy1',cache=None,notices=None):
 b=Payload(root,destination,'toddy-agent',version)
 b.dependencies+=['nodejs']
 for directory,names in AGENT.items():b.python('runtime/'+directory,'/usr/lib/toddy/'+directory,names)
 engine=b.content['/usr/lib/toddy/broker/engine.py']
 constants={node.value for node in ast.walk(ast.parse(engine)) if isinstance(node,ast.Constant) and isinstance(node.value,str)}
 if 'worker/worker.mjs' not in constants:
  raise PackageBlocked('installed_worker_path_not_supported')
 for name in WORKER:b.copy('runtime/engine/'+name,'/usr/lib/toddy/worker/'+name)
 package=json.loads(b.content['/usr/lib/toddy/worker/package.json'])
 architecture=json.loads(b.source('config/phase2/architecture.lock.json'))
 if package['dependencies']!={'@earendil-works/pi-agent-core':'1.5.0','@earendil-works/pi-ai':'1.5.0'} or \
   package.get('engines',{}).get('node')!='>=24.19.0 <25' or \
   architecture['engine']['nodejs']!='24.19.0' or architecture['engine']['packages']!=package['dependencies']:
  raise PackageBlocked('frozen_Pi_versions_required')
 for name in ('profile.schema.json','local-model.lock.json'):
  b.copy('config/phase2/'+name,'/usr/share/toddy/profiles/'+name)
 for name in ('config.json','SOUL.md','IDENTITY.md','USER.md','AGENTS.md'):
  b.copy('config/phase2/profile/'+name,'/usr/share/toddy/profiles/profile/'+name)
 b.copy('config/phase2/profile/skills/explain-system/SKILL.md',
        '/usr/share/toddy/profiles/profile/skills/explain-system/SKILL.md')
 preset=json.loads(b.content['/usr/share/toddy/profiles/profile/config.json'])
 if preset['provider']['mode']!='deferred' or preset['provider']['allow_remote_fallback'] or \
   preset['budgets']['remote_spending_enabled'] or preset['memory']['history_enabled'] or \
   preset['memory']['retention_days']!=0 or preset['automation']['enabled'] or preset['extensions']['enabled']:
  raise PackageBlocked('disabled_default_profile_required')
 for filename,target,key in [('toddy-agent.service','/usr/lib/systemd/user/toddy-agent.service','ExecStart='),
   ('io.github.markaraujo.Toddy.Service.service','/usr/share/dbus-1/services/io.github.markaraujo.Toddy.Service.service','Exec=')]:
  source='runtime/broker/packaging/'+filename
  template=b.source(source).decode()
  old=key+'/usr/bin/python3 /usr/lib/toddy/broker/service.py'
  if template.count(old)!=1:raise PackageBlocked('service_template_changed')
  b.put(target,template.replace(old,old+' --defaults /usr/share/toddy/profiles').encode(),source=source+' + explicit installed defaults')
 closure=vendor(b,cache or Path(root)/'.local/sources',notices or Path(root)/'.local/phase2/engine-notices')
 b.legal('Optional Toddy broker/Pi worker source payload. Frozen Pi1.5/npm bytes and\nseparate original/supplemental notices are reverified from complete B01 custody.\nNo Node binary, llama runtime, model, credential or enabled agent profile is bundled.')
 return b.finish({'verified_npm_closure':closure,'node_version_requirement':'>=24.19.0 <25',
   'native_prerequisites':['python-gio','sqlite-fts5','libsecret','native nodejs24.19.0'],
   'optional_local_runtime':'separate verified llama.cpp/model acquisition'})


def stage_voice(root,destination,*,version='0.2.0-1+toddy1'):
 b=Payload(root,destination,'toddy-voice',version)
 b.python('runtime/voice','/usr/lib/toddy/voice',VOICE)
 for path,data in b.content.items():
  if path.endswith('.py') and b'from runtime.voice' in data:raise PackageBlocked('installed_voice_namespace_required')
 b.copy('runtime/voice/README.md','/usr/share/doc/toddy-voice/adapters.md')
 b.copy('runtime/voice/UI.md','/usr/share/doc/toddy-voice/ui.md')
 wrappers={}
 for name in ('pw-record','pw-play'):
  source='runtime/voice/wrappers/'+name
  data=b.source(source)
  b.put('/usr/lib/toddy/voice/'+name,data,0o755,source)
  wrappers[name]=digest(data)
 b.put('/usr/share/doc/toddy-voice/activation-inputs.json',encoded({
  'schema_version':1,'scope':'Source controls only; no audio, model or native qualification',
  'catalog_generated':False,'catalog_path':'/usr/share/toddy/voice/catalog.json',
  'launcher_sha256':digest(b.content['/usr/lib/toddy/voice/child.py']),
  'runner_sha256':digest(b.content['/usr/lib/toddy/voice/process.py']),
  'wrapper_sha256':wrappers,
  'required_native_versions':{'pipewire':'1.6.8','wireplumber':'0.5.15','whisper-cpp':'1.9.5','espeak-ng':'1.52.0'},
  'native_evidence_required':'Actual engine/model/license and selected-device/no-fallback/PTT/Stop/focus/close/parent-loss qualification before trusted catalog generation'}))
 b.legal('Optional speech adapters, root-catalog reader, per-profile UI worker and fixed\nsource pw-cat mode wrappers only. Native engines, voices, models and their exact\nsource/license/integrity receipts are separate. No catalog, microphone, device query\nor playback starts on import or installation. Text remains usable; local speech\nrequires qualified native inputs, notice review and explicit device/action selection.')
 return b.finish({'engines_bundled':False,'models_or_voices_bundled':False,'always_listening':False,
  'runtime_configuration':'no catalog, artifact or device selected','catalog_generated':False,
  'fixed_transport_wrappers':sorted(wrappers)})


def stage_integrations(root,destination,*,version='0.2.0-1+toddy1'):
 b=Payload(root,destination,'toddy-integrations',version)
 b.dependencies+=['toddy-agent']
 # Match the fixed broker import/catalog namespace. Do not create a root alias
 # or collide with broker/integrations.py, which is owned by toddy-agent.
 b.python('runtime/plugins','/usr/lib/toddy/plugins',PLUGINS)
 bundles={'release-reference':('server.py','release.json','NOTICE','manifest.json'),
          'browser-local-read':('page.html',)}
 for name,files in bundles.items():
  for filename in files:
   b.copy('runtime/plugins/bundled/'+name+'/'+filename,
          '/usr/lib/toddy/plugins/bundled/'+name+'/'+filename)
 manifest=json.loads(b.content['/usr/lib/toddy/plugins/bundled/release-reference/manifest.json'])
 if set(manifest)!={'plugin_version','id','entry','files','capabilities','tools'} or \
   type(manifest['plugin_version']) is not int or manifest['plugin_version']!=1 or \
   manifest['id']!='release-reference' or manifest['entry']!='server.py' or \
   manifest['capabilities']!=['mcp.tools.read'] or manifest['tools']!={'lookup-package':['package']} or \
   set(manifest['files'])!={'server.py','release.json','NOTICE'}:
  raise PackageBlocked('reviewed_release_reference_manifest_required')
 for filename,expected in manifest['files'].items():
  if digest(b.content['/usr/lib/toddy/plugins/bundled/release-reference/'+filename])!=expected:
   raise PackageBlocked('release_reference_payload_integrity')
 release=json.loads(b.content['/usr/lib/toddy/plugins/bundled/release-reference/release.json'])
 observed=b.source('docs/evidence/B02-desktop-runtime-manifest.json')
 components=json.loads(observed)['components']
 fields=('name','version','architecture','sources','copyright','source_notices_index')
 projection={r['name']:{k:r[k] for k in fields if k in r} for r in components}
 if release['source_manifest_sha256']!=digest(observed) or release['components']!=projection or \
   release['scope']!='Pinned accepted B02 desktop release reference; not current installed package inventory':
  raise PackageBlocked('complete_release_reference_projection_required')
 b.copy('runtime/plugins/README.md','/usr/share/doc/toddy-integrations/integrations.md')
 b.copy('runtime/plugins/BROKER.md','/usr/share/doc/toddy-integrations/broker.md')
 b.put('/usr/share/toddy/plugins/defaults.json',encoded({'schema_version':1,'enabled':False,
   'registered_plugins':[],'browser_enabled':False,'automatic_skill_execution':False,'hooks_enabled':False}))
 b.put('/usr/share/doc/toddy-integrations/activation-inputs.json',encoded({
   'schema_version':1,'scope':'Exact staged inputs only; no native qualification or owner activation',
   'qualification_receipts_generated':False,
   'release-reference':{'manifest_sha256':digest(b.content['/usr/lib/toddy/plugins/bundled/release-reference/manifest.json']),
     'receipt_path':'/usr/share/toddy/plugins/release-reference.receipt.json',
     'native_evidence_required':'Actual qualified Bubblewrap/kernel/filesystem/IPC/network/credential denial and native signed package transaction'},
   'browser-local-read':{'page_sha256':digest(b.content['/usr/lib/toddy/plugins/bundled/browser-local-read/page.html']),
     'reader_sha256':digest(b.content['/usr/lib/toddy/plugins/atspi_read.py']),
     'firefox_version':'153.7.0esr',
     'receipt_path':'/usr/share/toddy/plugins/browser-local-read.receipt.json',
     'native_evidence_required':'Actual frozen Firefox/scoped AT-SPI/local page/Stop and complete installed Firefox component record'},
   'receipt_rule':'Trusted native transaction generates independently managed receipts after qualification; never embed a circular own-archive hash in source package'}))
 b.legal('Optional native plugin/skill/browser adapters and reviewed release-reference MCP source.\nThe source server and exact public B02 metadata projection are bundled but never\nexecuted by staging. No enabled registration, qualified receipt, account key,\nbrowser profile, executable hook or implicit owner permission is shipped.\nThe data-only default skill belongs to toddy-agent; this package requires it\nfor canonical skill parsing and independent broker policy. Native confinement\nand browser proof must precede trusted receipt generation and explicit owner activation.')
 return b.finish({'registered_plugins':[],'unknown_code_enabled':False,
  'bundled_source_integrations':['release-reference','browser-local-read'],
  'qualification_receipts_generated':False,'native_qualification':False,
  'native_prerequisites':['qualified-bubblewrap-confinement','Firefox153.7.0esr/AT-SPI only when explicitly enabled']})


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('package',choices=('agent','voice','integrations'))
 parser.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[3])
 parser.add_argument('--destination',type=Path,required=True)
 parser.add_argument('--version',default='0.2.0-1+toddy1')
 parser.add_argument('--npm-cache',type=Path)
 parser.add_argument('--engine-notices',type=Path)
 args=parser.parse_args()
 try:
  options={'version':args.version}
  if args.package=='agent':options.update(cache=args.npm_cache,notices=args.engine_notices)
  record=globals()['stage_'+args.package](args.repository,args.destination,**options)
 except (PackageBlocked,OSError,ValueError,KeyError,tarfile.TarError) as exc:
  print(json.dumps({'status':'blocked','package':args.package,'reason':str(exc) if isinstance(exc,PackageBlocked) else type(exc).__name__},sort_keys=True))
  raise SystemExit(1)
 print(json.dumps({'status':record['status'],'package':record['package'],'files':len(record['payload'])+1},sort_keys=True))


if __name__=='__main__':main()
