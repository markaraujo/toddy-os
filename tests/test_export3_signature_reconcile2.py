"""Reconcile pin/stream fixtures; real native stream evidence belongs coordinator."""
import base64,hashlib,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import export3_public_signatures_reconcile2 as p
class ReconcileTests(unittest.TestCase):
 def test_only_exact_prior_intent_and_same_host_packet(self):
  raw=b'actual packet bytes';value={name:'a'*64 for name in ('host_verified_receipt_sha256','host_signed_receipt_sha256','archive_export_sha256','release_sha256','public_key_sha256')}
  old={'version':1,'state':'public-signature3-staging-intended-no-replay','packet_sha256':hashlib.sha256(raw).hexdigest(),'private_material_transferred':False,
    'host_verified_receipt_sha256':value['host_verified_receipt_sha256'],'host_signed_receipt_sha256':value['host_signed_receipt_sha256'],
    'public_input_sha256':{'archive-export.json':value['archive_export_sha256'],'Release':value['release_sha256'],'archive-keyring.gpg':value['public_key_sha256']}}
  p.previous_binding(value,raw,old)
  with self.assertRaises(ValueError):p.previous_binding(value,b'changed packet',old)
  with self.assertRaises(ValueError):p.previous_binding(value,raw,{**old,'state':'native-public-signatures-verified'})
 def test_stream_separates_native_cleartext_stdout_status_stderr_and_stdin(self):
  with tempfile.TemporaryDirectory() as temporary:
   directory=Path(temporary);run=directory/'run';export=directory/'export';run.mkdir();export.mkdir()
   (run/'InRelease').write_bytes(b'public signed fixture');(export/'Release').write_bytes(b'exact cleartext\n')
   fingerprint='A'*40;result=Mock(returncode=0,stdout=b'exact cleartext\n',stderr=('[GNUPG:] VALIDSIG '+fingerprint+' metadata\n').encode())
   argv=['/usr/sbin/chroot','/mnt/lfs','/usr/bin/gpgv','--status-fd','1','--output','/run/clear','/run/InRelease']
   with patch.object(p,'RUN',run),patch.object(p.frozen,'EXPORT',export),patch.object(p.subprocess,'run',return_value=result) as native:
    value=p.stream_verify(argv,fingerprint)
    actual=native.call_args.args[0]
    self.assertEqual(actual[actual.index('--status-fd')+1],'2');self.assertEqual(actual[-2:],['-','-'])
    self.assertEqual(native.call_args.kwargs['input'],b'public signed fixture')
    self.assertEqual((run/'clear').read_bytes(),b'exact cleartext\n');self.assertEqual(value['exit'],0)
 def test_successful_signature_status_cannot_substitute_for_cleartext(self):
  with tempfile.TemporaryDirectory() as temporary:
   directory=Path(temporary);(directory/'InRelease').write_bytes(b'fixture');(directory/'Release').write_bytes(b'expected')
   result=Mock(returncode=0,stdout=b'',stderr=('[GNUPG:] VALIDSIG '+'A'*40+' metadata\n').encode())
   with patch.object(p,'RUN',directory),patch.object(p.frozen,'EXPORT',directory),patch.object(p.subprocess,'run',return_value=result):
    with self.assertRaisesRegex(ValueError,'stdout cleartext'):p.stream_verify(['gpgv','--status-fd','1','--output','clear','InRelease'],'A'*40)
    self.assertFalse((directory/'clear').exists())
