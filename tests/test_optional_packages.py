"""Optional source-stage checks; no engine/model/plugin acceptance or install."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('optional_packages',ROOT/'scripts/build/phase2/optional_packages.py')
optional=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(optional)
ASSISTANT_SPEC=importlib.util.spec_from_file_location('assistant_package',ROOT/'scripts/build/phase2/assistant_package.py')
assistant=importlib.util.module_from_spec(ASSISTANT_SPEC);ASSISTANT_SPEC.loader.exec_module(assistant)


class OptionalPackageTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.base=Path(self.temp.name)

 def test_voice_stage_is_deterministic_optional_model_free_and_importable_installed(self):
  stage=self.base/'voice';second=self.base/'voice-two'
  record=optional.stage_voice(ROOT,stage)
  self.assertEqual(record,optional.stage_voice(ROOT,second))
  self.assertFalse(record['engines_bundled']);self.assertFalse(record['models_or_voices_bundled'])
  self.assertFalse(record['always_listening']);self.assertFalse(record['offline_base'])
  self.assertEqual(record['depends_on_packages'],['toddy-assistant'])
  self.assertFalse((stage/'usr/lib/toddy/__init__.py').exists())
  self.assertFalse((stage/'DEBIAN').exists())
  namespace=self.base/'namespace';assistant.stage(ROOT,namespace)
  import shutil
  shutil.copytree(stage/'usr/lib/toddy/voice',namespace/'usr/lib/toddy/voice')
  code='''
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1]+'/usr/lib')
from toddy.voice.session import VoiceSession
assert VoiceSession({},{}).capabilities('pt-BR') == {
 'language':'pt-BR','text_available':True,'always_listening':False,
 'push_to_talk':False,'speech_output':False,'playback':False,
 'tts_engine':'espeak-ng','automatic_download':False}
print('ACTUAL_STAGED_VOICE_IMPORT_TEXT_FALLBACK_PASS')
'''
  result=subprocess.run([sys.executable,'-I','-c',code,str(namespace)],
   cwd=self.base,capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn('ACTUAL_STAGED_VOICE_IMPORT_TEXT_FALLBACK_PASS',result.stdout)

 def test_integration_fixture_stage_has_no_enabled_server_browser_or_hook(self):
  # Synthetic source files exercise payload ownership only. Actual plugin/browser
  # source staging is verified separately against the committed integration tree.
  root=self.base/'fixture-source';root.mkdir()
  for source in ['LICENSE','LICENSES/CC-BY-4.0.txt','config/phase2/profile/skills/explain-system/SKILL.md']:
   target=root/source;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/source).read_bytes())
  for name in optional.PLUGINS:
   target=root/'runtime/plugins'/name;target.parent.mkdir(parents=True,exist_ok=True)
   target.write_text('"""Synthetic staging fixture, not a functioning integration."""\n')
  (root/'runtime/plugins/README.md').write_text('Synthetic source fixture only.\n')
  stage=self.base/'integrations'
  record=optional.stage_integrations(root,stage)
  policy=json.loads((stage/'usr/share/toddy/integrations/defaults.json').read_text())
  self.assertFalse(policy['enabled']);self.assertFalse(policy['browser_enabled'])
  self.assertFalse(policy['hooks_enabled']);self.assertEqual(policy['registered_plugins'],[])
  self.assertEqual(record['registered_plugins'],[]);self.assertFalse(record['unknown_code_enabled'])
  self.assertFalse((stage/'usr/lib/toddy/__init__.py').exists())
  self.assertTrue((stage/'usr/share/toddy/skills/explain-system/SKILL.md').is_file())

 def test_missing_or_corrupt_complete_vendor_custody_blocks_without_creating_a_stage(self):
  b=optional.Payload(ROOT,self.base/'unwritten','toddy-agent','0.2.0-1')
  with self.assertRaisesRegex(optional.PackageBlocked,'vendor_archive_missing'):
   optional.vendor(b,self.base/'missing-cache',self.base/'missing-notices')
  self.assertFalse(b.destination.exists())
  cache=self.base/'cache';cache.mkdir()
  lock=json.loads((ROOT/'runtime/engine/package-lock.json').read_text())
  location=sorted(key for key in lock['packages'] if key)[0]
  sha512=base64.b64decode(lock['packages'][location]['integrity'].split('-',1)[1])
  (cache/('npm-'+sha512.hex()+'.tgz')).write_bytes(b'tampered')
  with self.assertRaisesRegex(optional.PackageBlocked,'vendor_archive_integrity'):
   optional.vendor(optional.Payload(ROOT,self.base/'also-unwritten','toddy-agent','0.2.0-1'),cache,self.base/'notices')
  self.assertFalse((self.base/'also-unwritten').exists())

 def test_native_host_bytes_and_existing_stages_are_refused(self):
  payload=optional.Payload(ROOT,self.base/'payload','toddy-voice','0.2.0-1')
  for magic in [b'\x7fELF',b'MZ',b'\xcf\xfa\xed\xfe']:
   with self.assertRaisesRegex(optional.PackageBlocked,'native_artifact_requires_separate_qualification'):
    payload.put('/usr/lib/toddy/voice/unqualified',magic+b'fixture')
  self.assertFalse(payload.destination.exists())
  self.base.joinpath('existing').mkdir()
  with self.assertRaisesRegex(optional.PackageBlocked,'fresh_canonical_stage_required'):
   optional.stage_voice(ROOT,self.base/'existing')


if __name__=='__main__':unittest.main()
