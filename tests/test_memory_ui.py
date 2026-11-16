"""Owner-memory UI boundaries, no database, model, dconf or secret service."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from runtime.ui.memory import page,sealed_local_backup,reviewed_document,reviewed_preferences

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

 def test_readonly_document_requires_full_seals_exact_hash_size_and_bounded_valid_text(self):
  fd=os.memfd_create('test-reviewed-notes',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
  self.addCleanup(os.close,fd);os.fchmod(fd,0o600)
  raw=b'Private plain <b>notes</b>\n';os.write(fd,raw)
  snapshot={'user_document_bytes':len(raw),'user_document_sha256':hashlib.sha256(raw).hexdigest()}
  with self.assertRaises(ValueError):reviewed_document(fd,snapshot)
  fcntl.fcntl(fd,fcntl.F_ADD_SEALS,fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK)
  self.assertEqual(reviewed_document(fd,snapshot),raw.decode())
  with self.assertRaises(ValueError):reviewed_document(fd,{**snapshot,'user_document_sha256':'0'*64})
  with self.assertRaises(ValueError):reviewed_document(fd,{**snapshot,'user_document_bytes':len(raw)+1})

 def test_reviewed_preferences_rejects_invalid_ambiguous_or_excessive_maps(self):
  self.assertEqual(reviewed_preferences('{"language":"Portuguese"}'),{'language':'Portuguese'})
  for value in ('[]','{"language":1}','{"language":""}','{"A":"text"}','{"x":"first","x":"second"}',
                json.dumps({'p-'+str(i):'text' for i in range(33)}),json.dumps({'language':'a'*4097})):
   with self.subTest(value=value[:40]),self.assertRaises(ValueError):reviewed_preferences(value)

if __name__=='__main__':unittest.main()
