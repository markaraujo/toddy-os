import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('kernel_guest_scratch',Path(__file__).resolve().parents[1]/'scripts/build/phase2/prepare_kernel_landlock_scratch.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class GuestScratchIdentity(unittest.TestCase):
 def setUp(self):self.row=dict(type='disk',serial='TODDY-B02-KERNEL',size=805306368,ro=False,fstype=None,uuid=None,mountpoints=[None],path='/dev/vdc')
 def test_exact_blank_virtual_identity(self):m.validate_identity(self.row)
 def test_wrong_serial_or_capacity(self):
  for key,value in [('serial','TODDY-LFS-TARGET'),('size',805306367),('type','part'),('ro',True)]:
   with self.subTest(key=key),self.assertRaises(AssertionError):m.validate_identity(dict(self.row,**{key:value}))
 def test_mounted_or_swap_or_existing_filesystem(self):
  for key,value in [('mountpoints',['/']),('mountpoints',['[SWAP]']),('fstype','ext4'),('uuid','existing')]:
   with self.subTest(key=key,value=value),self.assertRaises(AssertionError):m.validate_identity(dict(self.row,**{key:value}))
 def test_partitioned_or_known_root_disk(self):
  for key,value in [('children',[{'path':'/dev/vdc1'}]),('path','/dev/vda'),('path','/dev/vdb')]:
   with self.subTest(key=key,value=value),self.assertRaises(AssertionError):m.validate_identity(dict(self.row,**{key:value}))
if __name__=='__main__':unittest.main()
