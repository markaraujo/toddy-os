"""Bounded public packet/refusal fixtures, no VM or fabricated signature proof."""
import base64,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import export3_public_signatures as p
class PublicSignatureTests(unittest.TestCase):
 def packet(self):
  bodies={'Release.gpg':b'public fixture signature','InRelease':b'public fixture signed release'}
  return {'version':1,**{key:'a'*64 for key in ('archive_export_sha256','release_sha256','public_key_sha256','host_verified_receipt_sha256','host_signed_receipt_sha256')},
      'signatures':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode()} for name,data in bodies.items()}}
 def test_only_exact_bounded_public_signature_bytes(self):
  value=self.packet();_,bodies=p.decode_packet(p.p.encoded(value));self.assertEqual(set(bodies),{'Release.gpg','InRelease'})
  value['signatures']['private.asc']=value['signatures']['Release.gpg']
  with self.assertRaisesRegex(ValueError,'two public'):p.decode_packet(p.p.encoded(value))
  value=self.packet();value['signatures']['InRelease']['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'integrity'):p.decode_packet(p.p.encoded(value))
  with self.assertRaisesRegex(ValueError,'bound'):p.decode_packet(b'x'*(p.MAX_PACKET+1))
 def test_existing_intent_refused_before_any_native_command(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);receipt=root/'receipt.json';receipt.write_text('uncertain')
   with patch.object(p,'RECEIPT',receipt),patch.object(p,'protected'),patch.object(p.subprocess,'run') as native:
    with self.assertRaisesRegex(ValueError,'no replay'):p.stage(p.p.encoded(self.packet()))
    native.assert_not_called()
 def test_actual_gpgv_status_exit_and_approved_primary_are_mandatory(self):
  fingerprint='A'*40
  good=Mock(returncode=0,stdout=('[GNUPG:] VALIDSIG '+fingerprint+' metadata\n').encode(),stderr=b'')
  with patch.object(p.subprocess,'run',return_value=good):self.assertEqual(p.verify_command(['fixed-gpgv-fixture'],fingerprint)['exit'],0)
  for result in (Mock(returncode=1,stdout=good.stdout,stderr=b''),Mock(returncode=0,stdout=b'[GNUPG:] VALIDSIG WRONG metadata\n',stderr=b'')):
   with patch.object(p.subprocess,'run',return_value=result):
    with self.assertRaises(ValueError):p.verify_command(['fixed-gpgv-fixture'],fingerprint)
 def test_wrapper_forwards_original_packet_fd_not_shell_source(self):
  source=(ROOT/'scripts/build/phase2/image_native.sh').read_text()
  self.assertIn('export3_public_signatures.py <&8 8<&-',source)
  self.assertIn('signatures-export3',source)
  self.assertLess(source.index('exec 8<&0'),source.index("<<'NAMESPACE'"))
