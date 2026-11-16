"""Private GUI file handoff primitives, independent of GTK or agent availability."""
import fcntl
import json
import os
from pathlib import Path
import tempfile
import unittest

from runtime.ui.model import open_profile_import,save_profile_export
from runtime.ui.task_state import TaskState


class ProfileFiles(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)

 def sealed(self,data=b'{"bundle_version":1,"scope":"test-only"}'):
  fd=os.memfd_create('test-profile-export',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
  os.fchmod(fd,0o600);os.write(fd,data)
  fcntl.fcntl(fd,fcntl.F_ADD_SEALS,fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_SEAL)
  self.addCleanup(os.close,fd)
  return fd

 def test_private_sealed_export_is_atomic_and_never_overwrites_existing_or_symlink(self):
  descriptor=self.sealed();path=self.root/'export.json'
  save_profile_export(descriptor,path)
  self.assertEqual(path.stat().st_mode&0o777,0o600)
  self.assertEqual(path.read_bytes(),os.pread(descriptor,1024,0))
  with self.assertRaises(FileExistsError):save_profile_export(descriptor,path)
  target=self.root/'other';target.write_text('preserved')
  link=self.root/'link';link.symlink_to(target)
  with self.assertRaises(FileExistsError):save_profile_export(descriptor,link)
  self.assertEqual(target.read_text(),'preserved')
  self.assertEqual(list(self.root.glob('.toddy-profile-*')),[])

 def test_unsealed_fd_is_not_exported_and_import_rejects_symlink_fifo_and_oversize(self):
  source=self.root/'source';source.write_text('ordinary unsealed data')
  fd=os.open(source,os.O_RDONLY)
  try:
   with self.assertRaises((ValueError,OSError)):save_profile_export(fd,self.root/'not-written')
  finally:os.close(fd)
  self.assertFalse((self.root/'not-written').exists())
  fd=open_profile_import(source)
  try:self.assertEqual(os.read(fd,1024),source.read_bytes())
  finally:os.close(fd)
  link=self.root/'link';link.symlink_to(source)
  with self.assertRaises(OSError):open_profile_import(link)
  fifo=self.root/'fifo';os.mkfifo(fifo,0o600)
  with self.assertRaisesRegex(ValueError,'profile_import_file'):open_profile_import(fifo)
  with source.open('wb') as stream:stream.truncate(8*1024*1024+1)
  with self.assertRaisesRegex(ValueError,'profile_import_file'):open_profile_import(source)

 def test_known_task_profile_cannot_be_rebound_by_a_snapshot(self):
  state=TaskState();state.submitting=True;state.profile_id='first';state.profile_revision='a'*64
  state.submitted('task-example')
  view={'version':1,'task_id':'task-example','profile_id':'second','profile_revision':'a'*64,
        'sequence':1,'state':'running','cancel_requested':False,'result_uncertain':False,
        'summary':'running','operation_id':None}
  with self.assertRaisesRegex(ValueError,'invalid_snapshot'):state.observe(json.dumps(view))
  self.assertIsNone(state.snapshot)
  view['profile_id']='first';state.observe(json.dumps(view))
  self.assertEqual(state.snapshot['profile_id'],'first')


if __name__=='__main__':unittest.main()
