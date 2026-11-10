"""Storage identity guards must fail closed before any optional QEMU attachment."""
import json,os,sys,tempfile,unittest
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
