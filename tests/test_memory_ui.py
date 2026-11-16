"""Owner-memory UI boundaries, no database, model, dconf or secret service."""
import fcntl
import json
import os
from pathlib import Path
import tempfile
import unittest
from runtime.ui.memory import page,sealed_local_backup

class MemoryUI(unittest.TestCase):
 def test_memory_page_is_bounded_and_profile_bound(self):
  good={'version':1,'profile_id':'first','profile_revision':'a'*64,'memory_generation':0,
        'records':[],'next_cursor':'','complete':True,'user_document_review_required':False}
  self.assertEqual(page(json.dumps(good),'first'),good)
  with self.assertRaises(ValueError):page(json.dumps(good),'second')
  for field,bad in [('memory_generation',True),('complete',1),('profile_revision','bad'),('records',[{}])]:
   changed={**good,field:bad}
   with self.subTest(field=field),self.assertRaises(ValueError):page(json.dumps(changed),'first')

 def test_selected_local_backup_is_copied_to_immutable_owned_readonly_fd(self):
  with tempfile.TemporaryDirectory() as temporary:
   source=Path(temporary)/'selected.json';source.write_bytes(b'{"test":"explicit-untrusted-owner-backup"}')
   descriptor=sealed_local_backup(source)
   try:
    self.assertEqual(os.pread(descriptor,1024,0),source.read_bytes())
    self.assertEqual(os.fstat(descriptor).st_mode&0o777,0o600)
    seals=fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK
    self.assertEqual(fcntl.fcntl(descriptor,fcntl.F_GET_SEALS)&seals,seals)
    self.assertEqual(fcntl.fcntl(descriptor,fcntl.F_GETFL)&os.O_ACCMODE,os.O_RDONLY)
    source.write_bytes(b'changed-after-capture')
    self.assertNotEqual(os.pread(descriptor,1024,0),source.read_bytes())
   finally:os.close(descriptor)
   link=Path(temporary)/'link';link.symlink_to(source)
   with self.assertRaises(OSError):sealed_local_backup(link)

if __name__=='__main__':unittest.main()
