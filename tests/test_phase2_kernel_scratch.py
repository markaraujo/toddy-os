"""Storage identity guards must fail closed before any optional QEMU attachment."""
import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/host'))
import phase2_vm

class ScratchGuard(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.work=Path(self.tmp.name)
  self.patch1=patch.object(phase2_vm,'WORK',self.work);self.patch2=patch.object(phase2_vm,'KERNEL_SCRATCH_BYTES',8192)
  self.patch1.start();self.patch2.start();self.addCleanup(self.patch1.stop);self.addCleanup(self.patch2.stop);self.addCleanup(self.tmp.cleanup)
 def prepare(self):
  p=self.work/'kernel-landlock-scratch.raw'
  with p.open('wb') as f:f.write(bytes(8192));f.flush();os.fsync(f.fileno())
  p.chmod(0o600);s=p.stat();row={'state':'prepared','filename':p.name,'format':'raw','bytes':8192,'serial':'TODDY-B02-KERNEL','device':s.st_dev,'inode':s.st_ino}
  self.write(row);return p,row
 def write(self,row):(self.work/'kernel-landlock-scratch.json').write_text(json.dumps(row))
 def test_no_scratch_preserves_default(self):self.assertEqual(phase2_vm.kernel_scratch_arguments(),[])
 def test_valid_identity_uses_only_fixed_virtual_path(self):
  self.prepare();args=phase2_vm.kernel_scratch_arguments();self.assertEqual(args[0],'-drive');self.assertIn('file=/vm/phase2/kernel-landlock-scratch.raw',args[1]);self.assertIn('discard=ignore',args[1])
 def test_partial_preparation_denied(self):
  (self.work/'kernel-landlock-scratch.json').write_text('{}')
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_symlink_denied(self):
  p,row=self.prepare();p.unlink();p.symlink_to('/dev/null')
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_wrong_inode_denied(self):
  p,row=self.prepare();row['inode']+=1;self.write(row)
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_wrong_size_denied(self):
  p,row=self.prepare();p.write_bytes(b'x')
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_external_or_pending_declaration_denied(self):
  p,row=self.prepare();row['filename']='/dev/sda';self.write(row)
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
  row['filename']=p.name;row['state']='preparing';self.write(row)
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_hardlink_or_shared_permissions_denied(self):
  p,row=self.prepare();os.link(p,self.work/'other')
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
  (self.work/'other').unlink();p.chmod(0o644)
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()

class GrownScratchGuard(unittest.TestCase):
 prepare=ScratchGuard.prepare
 write=ScratchGuard.write
 def setUp(self):
  ScratchGuard.setUp(self);p=patch.object(phase2_vm,'KERNEL_SCRATCH_GROWN_BYTES',16384);p.start();self.addCleanup(p.stop)
 def grown(self):
  p,row=self.prepare()
  with p.open('ab') as f:f.write(bytes(8192));f.flush();os.fsync(f.fileno())
  receipt=self.work/'kernel-landlock-growth.json'
  grown=dict(state='filesystem-grown',allocation_reconciled=True,serial='TODDY-B02-KERNEL',old_bytes=8192,new_bytes=16384,growth_bytes=8192,device=p.stat().st_dev,inode=p.stat().st_ino,original_receipt_sha256=hashlib.sha256((self.work/'kernel-landlock-scratch.json').read_bytes()).hexdigest(),filesystem_uuid='c6c4176d-faed-4ee3-9ae0-94914a0af666')
  receipt.write_text(json.dumps(grown));receipt.chmod(0o600);return p,receipt,grown
 def test_completed_bounded_growth(self):
  self.grown();self.assertIn('serial=TODDY-B02-KERNEL',phase2_vm.kernel_scratch_arguments()[-1])
 def test_pending_or_foreign_growth(self):
  p,r,g=self.grown()
  for key,value in [('state','qmp-grown-filesystem-pending'),('allocation_reconciled',False),('inode',g['inode']+1),('new_bytes',32768),('original_receipt_sha256','0'*64)]:
   with self.subTest(key=key):
    r.write_text(json.dumps(dict(g,**{key:value})))
    with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_unreceipted_grown_file(self):
  p,r,g=self.grown();r.unlink()
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_growth_symlink_rejected(self):
  p,r,g=self.grown();r.unlink();r.symlink_to('/dev/null')
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()


class FuseGrowthGuard(unittest.TestCase):
 prepare=ScratchGuard.prepare
 write=ScratchGuard.write
 grown=GrownScratchGuard.grown
 def setUp(self):
  GrownScratchGuard.setUp(self)
  p=patch.object(phase2_vm,'KERNEL_FUSE_SCRATCH_BYTES',32768);p.start();self.addCleanup(p.stop)
 def fuse_grown(self):
  p,parent,_=self.grown()
  with p.open('ab') as f:f.write(bytes(16384));f.flush();os.fsync(f.fileno())
  r=self.work/'kernel-fuse-growth.json'
  g=dict(state='filesystem-grown',allocation_reconciled=True,serial='TODDY-B02-KERNEL',old_bytes=16384,new_bytes=32768,growth_bytes=16384,device=p.stat().st_dev,inode=p.stat().st_ino,original_receipt_sha256=hashlib.sha256((self.work/'kernel-landlock-scratch.json').read_bytes()).hexdigest(),previous_growth_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),filesystem_uuid='c6c4176d-faed-4ee3-9ae0-94914a0af666')
  r.write_text(json.dumps(g));r.chmod(0o600);return p,r,g
 def test_completed_identity_and_parent_chain(self):
  self.fuse_grown();self.assertIn('serial=TODDY-B02-KERNEL',phase2_vm.kernel_scratch_arguments()[-1])
 def test_partial_or_foreign_growth_rejected(self):
  p,r,g=self.fuse_grown()
  for key,v in [('state','qmp-grown-filesystem-pending'),('allocation_reconciled',False),('previous_growth_sha256','0'*64),('inode',g['inode']+1),('serial','physical-disk'),('new_bytes',65536)]:
   with self.subTest(key=key):
    r.write_text(json.dumps(dict(g,**{key:v})))
    with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_valid_receipt_symlink_rejected(self):
  p,r,g=self.fuse_grown();r.rename(self.work/'retained.json');r.symlink_to('retained.json')
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
 def test_pending_intent_rejected_before_disk_change(self):
  self.grown();(self.work/'kernel-fuse-growth.part').write_text('{}')
  with self.assertRaises(ValueError):phase2_vm.kernel_scratch_arguments()
