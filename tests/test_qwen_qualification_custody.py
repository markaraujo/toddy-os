"""Small synthetic custody fixtures; no real model/native copy."""
import hashlib,importlib.util,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('qwen',Path(__file__).resolve().parents[1]/'scripts/build/phase2/qwen_qualification_custody.py')
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)
class CustodyTests(unittest.TestCase):
 def test_reserves_include_entire_extra_copy(self):
  with patch.object(p.shutil,'disk_usage',return_value=type('Usage',(),{'free':16*1024**3+p.MARGIN+p.ADDITIONAL-1})()):
   with self.assertRaisesRegex(ValueError,'reserve'):p.reserve('/',16*1024**3)
 def test_exact_fixed_model_namespace(self):
  self.assertEqual(p.ROWS[0][2],1834426016)
  self.assertIn('qualification-qwen3-1.7b-1/',p.ROWS[0][1]);self.assertEqual(p.ROWS[1][2],11544)
 def test_copy_and_changed_source_refusal(self):
  with tempfile.TemporaryDirectory() as folder:
   source=Path(folder)/'source';source.write_bytes(b'fixture');source.chmod(0o644)
   fd=os.open(source,os.O_RDONLY|os.O_NOATIME)
   try:
    info=os.fstat(fd);before=[info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_atime_ns]
    with patch.object(p,'protected'),patch.object(p,'fingerprint',return_value=before):
     p.copy_one(fd,source,Path(folder)/'out',7,hashlib.sha256(b'fixture').hexdigest(),before)
     self.assertEqual((Path(folder)/'out').read_bytes(),b'fixture');self.assertEqual((Path(folder)/'out').stat().st_mode&0o777,0o444)
     os.lseek(fd,0,os.SEEK_SET)
     with self.assertRaisesRegex(ValueError,'source_changed'):p.copy_one(fd,source,Path(folder)/'bad',7,'0'*64,before)
   finally:os.close(fd)
 def test_private_receipt_is_once_only_part(self):
  with tempfile.TemporaryDirectory() as folder,patch.object(p,'RECEIPT',Path(folder)/'receipt.json'):
   p.save({'state':'copy-intended-no-replay'});self.assertEqual(p.RECEIPT.stat().st_mode&0o777,0o600)
   p.RECEIPT.with_suffix('.part').write_text('interrupted')
   with self.assertRaises(FileExistsError):p.save({'state':'complete'})
