"""Source-only adoption guards and actual temporary-file effects; no native proof."""
import hashlib,importlib.util,json,os,stat,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mvp_adoption_fixture',ROOT/'scripts/build/phase2/image_assemble.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
from runtime.installer.native_finalizer import account_files
ORIGINAL_LSTAT=Path.lstat

def owner_lstat(path,*args,**kwargs):
 values=list(ORIGINAL_LSTAT(path,*args,**kwargs));values[4]=values[5]=0;return os.stat_result(values)

class AdoptionTests(unittest.TestCase):
 def accounts(self,root):
  policy={'accounts':{'passwd':'root:x:0:0:root:/root:/bin/bash\n','group':'root:x:0:\nwheel:x:97:\n'}}
  generated={};(root/'etc').mkdir()
  for relative,(data,mode) in account_files(policy['accounts']).items():
   path=root/relative;path.write_bytes(data);path.chmod(mode)
   generated['/'+relative]={'mode':stat.S_IFREG|mode,'uid':0,'gid':0,'sha256':hashlib.sha256(data).hexdigest(),'origin':'fresh-system-accounts'}
  return SimpleNamespace(policy=policy,manifest={'ownership':{'entries':{}}},generated=generated)
 def test_only_seven_exact_unowned_synthetic_files_are_eligible_for_reset(self):
  with tempfile.TemporaryDirectory() as temporary,patch.object(Path,'lstat',owner_lstat):
   root=Path(temporary);inputs=self.accounts(root)
   self.assertEqual(len(a.synthetic_accounts(root,inputs)),7)
   shadow=root/'etc/shadow';original=shadow.read_bytes();shadow.write_bytes(b'not synthetic fixture')
   with self.assertRaises(ValueError):a.synthetic_accounts(root,inputs)
   shadow.write_bytes(original);os.link(shadow,root/'external-link')
   with self.assertRaises(ValueError):a.synthetic_accounts(root,inputs)
   (root/'external-link').unlink();inputs.manifest['ownership']['entries']['/etc/shadow']={}
   with self.assertRaises(ValueError):a.synthetic_accounts(root,inputs)
 def test_loader_reset_requires_exact_unowned_real_generator_receipt(self):
  with tempfile.TemporaryDirectory() as temporary,patch.object(Path,'lstat',owner_lstat):
   root=Path(temporary);inputs=self.accounts(root);cache=root/'etc/ld.so.cache';cache.write_bytes(b'loader fixture');cache.chmod(0o644)
   sha=hashlib.sha256(cache.read_bytes()).hexdigest();inputs.generated['/etc/ld.so.cache']={'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':sha,'origin':'generated-caches'}
   inputs.manifest['ownership']['entries']['/usr/sbin/ldconfig']={'sha256':'a'*64}
   candidate={'loader':{'output':'/etc/ld.so.cache','sha256':sha,'generator':'/usr/sbin/ldconfig','generator_sha256':'a'*64,'flags':['-X','-i'],'source_cache_copied':False,'package_inputs_unchanged':True}}
   self.assertEqual(a.synthetic_loader(root,inputs,candidate),cache)
   candidate['loader']['source_cache_copied']=True
   with self.assertRaises(ValueError):a.synthetic_loader(root,inputs,candidate)
   candidate['loader']['source_cache_copied']=False;os.link(cache,root/'borrowed')
   with self.assertRaises(ValueError):a.synthetic_loader(root,inputs,candidate)
 def test_failure_after_atomic_move_is_checkpointed_and_cannot_replay(self):
  from runtime.installer.native_finalizer import payload_module
  real=payload_module()
  with tempfile.TemporaryDirectory() as temporary:
   base=Path(temporary);stage=base/'stage';stage.mkdir();source_work=stage/a.GENERATIONS['mvp-base'][0];source_work.mkdir();root=source_work/'root';root.mkdir();inode=root.stat().st_ino
   with patch.object(Path,'lstat',owner_lstat):inputs=self.accounts(root)
   cache=root/'etc/ld.so.cache';cache.write_bytes(b'loader');cache.chmod(0o644);sha=real.digest(cache)
   inputs.manifest.update(delivery_class=a.MVP_CLASS,g2_eligible=False,bytes=10,catalog_sha256='a'*64)
   inputs.manifest['ownership']['entries']['/usr/sbin/ldconfig']={'sha256':'b'*64};inputs.generated['/etc/ld.so.cache']={'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':sha,'origin':'generated-caches'}
   inputs.bundle=base/'bundle';inputs.bundle.mkdir();(inputs.bundle/'manifest.json').write_bytes(b'{}');manifest_sha=real.digest(inputs.bundle/'manifest.json');image={'fixture':'not native evidence'}
   expected_image=hashlib.sha256(real.encoded(image)).hexdigest();inputs.descriptor={'payload_manifest_sha256':manifest_sha,'policy_sha256':'c'*64,'image_manifest_sha256':expected_image};inputs.source_hashes={'fixture':'d'*64};inputs.recheck=lambda:None
   repository=base/'repo';recipe=repository/'scripts/build/phase2/resource_recipe.py';recipe.parent.mkdir(parents=True);recipe.write_bytes(b'# fixture')
   candidate={'state':'native-candidate-awaiting-independent-review','blockers':[],'manifest_sha256':manifest_sha,'policy_sha256':'c'*64,'root_inode':inode,'root_device':root.stat().st_dev,'source_sha256':real.digest(recipe),'loader':{'output':'/etc/ld.so.cache','sha256':sha,'generator':'/usr/sbin/ldconfig','generator_sha256':'b'*64,'flags':['-X','-i'],'source_cache_copied':False,'package_inputs_unchanged':True}}
   inputs.pins={}
   for old,new,field,value in (('candidate-generated-entries.json','generated-entries.json','generated_entries_sha256',inputs.generated),('candidate-clean-image-manifest.json','expected-image-manifest.json','candidate_image_manifest_sha256',image)):
    path=source_work/old;path.write_bytes(real.encoded(value));inputs.pins[new]=real.digest(path);candidate[field]=real.digest(path)
   for name,value in (('unpack-intent.json',{'planned_adoption':True,'allocation_factor':1}),('unpacked.json',{}),('resource-intent.json',{}),('candidate-resource-receipt.json',candidate)):(source_work/name).write_bytes(real.encoded(value))
   (source_work/'dpkg.log').write_bytes(b'fixture');journals={p.name:p.read_bytes() for p in source_work.iterdir() if p.is_file()}
   source=SimpleNamespace(work=source_work,root=root,pin=(root.stat().st_dev,source_work.stat().st_ino,inode),recheck=lambda:None)
   class Prepared:
    def __init__(self,*args,**kwargs):pass
    def verify_payload(self,plan):return {}
    @staticmethod
    def audit_tree(*args):return image
   fake=SimpleNamespace(strict=json.loads,encoded=real.encoded,digest=real.digest,PreparedPayload=Prepared,CHECKS=real.CHECKS)
   actual_path=Path;reports=base/'reports';mapping=lambda value:reports if str(value)=='/run/toddy-installer' else actual_path(value)
   with patch.object(a,'STAGE',stage),patch.object(a,'ROOT',repository),patch.object(a,'Path',side_effect=mapping),patch.object(a,'private_directory',side_effect=lambda p,m:actual_path(p).stat()),patch.object(a,'ReviewedInputs',return_value=inputs),patch.object(a,'adopt_unpacked',return_value=source),patch.object(a,'payload_module',return_value=fake),patch.object(a,'secured',side_effect=lambda p,*args:actual_path(p)),patch.object(Path,'lstat',owner_lstat),patch.object(a.os,'statvfs',return_value=SimpleNamespace(f_bavail=2**40,f_frsize=4096)),patch('runtime.installer.native_finalizer.NativeFinalizer',return_value=Mock(side_effect=ValueError('injected failure'))) as finalizer:
    with self.assertRaisesRegex(ValueError,'injected failure'):a.adopt_finalize_mvp('mvp-base',Mock())
    destination=stage/a.GENERATIONS['mvp-base-reviewed'][0]/a.reviewed_root_name('mvp-base')
    self.assertFalse(root.exists());self.assertEqual(destination.stat().st_ino,inode)
    self.assertTrue((destination.parent/'adoption-blocked.json').is_file());self.assertFalse((destination.parent/'finalized.json').exists())
    self.assertTrue(all((source_work/name).read_bytes()==raw for name,raw in journals.items()))
    self.assertFalse((destination/'etc/passwd').exists());self.assertFalse((destination/'etc/ld.so.cache').exists())
    with self.assertRaisesRegex(ValueError,'no replay'):a.adopt_finalize_mvp('mvp-base',Mock())
    finalizer.assert_called_once()
 def test_planned_allocation_is_explicit_only_for_mvp_first_candidate(self):
  manifest={'delivery_class':a.MVP_CLASS,'g2_eligible':False}
  for kind,planned,factor in (('mvp-base',True,1),('mvp-base-reviewed',False,3)):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temporary:
    stage=Path(temporary);stage.chmod(0o755)
    def stage_lstat(path,*args,**kwargs):
     row=list(owner_lstat(path,*args,**kwargs));row[2]=Path('/').stat().st_dev;return os.stat_result(row)
    with patch.object(a,'STAGE',stage),patch.object(Path,'lstat',stage_lstat),patch.object(a,'private_directory',side_effect=lambda path,mode:Path(path).stat()),patch.object(a.os,'statvfs',return_value=SimpleNamespace(f_bavail=2**40,f_frsize=4096)),patch.object(a,'root_storage_budget',return_value={'root_bound_bytes':1000,'fixed_filesystem_and_generated_headroom_bytes':512*1024**2}):
     previous=os.umask(0o077)
     try:value=a.AssemblyRoot(kind,manifest,planned_adoption=planned)
     finally:os.umask(previous)
     self.assertEqual(value.required,a.RESERVE+factor*1000+512*1024**2);self.assertEqual(value.root.stat().st_mode&0o777,0o755)
  with self.assertRaisesRegex(ValueError,'fixed MVP first'):a.AssemblyRoot('base',{},planned_adoption=True)
  with self.assertRaisesRegex(ValueError,'fixed MVP first'):a.AssemblyRoot('mvp-base-reviewed',manifest,planned_adoption=True)
 def test_adoption_refuses_standard_and_existing_uncertain_destination(self):
  with self.assertRaises(ValueError):a.adopt_finalize_mvp('base',Mock())
 def test_real_finalizer_and_all_reports_remain_required_without_install_replay(self):
  import ast
  tree=ast.parse(Path(a.__file__).read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='adopt_finalize_mvp');source=ast.unparse(node)
  self.assertIn('os.rename(source.root, destination)',source)
  self.assertIn('finalizer(destination, inputs.manifest)',source)
  self.assertIn('validate_finalizer_report',source);self.assertIn('PreparedPayload.audit_tree',source)
  self.assertNotIn('native.install_payload',source);self.assertNotIn('rmtree',source)
  self.assertIn("'adoption-blocked.json'",source)

if __name__=='__main__':unittest.main()
