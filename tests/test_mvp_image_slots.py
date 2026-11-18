"""Typed MVP slot isolation, not boot/release acceptance."""
import importlib.util,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def module(name):
 spec=importlib.util.spec_from_file_location('mvp_'+name,ROOT/'scripts/build/phase2'/f'{name}.py')
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
a=module('image_assemble');m=module('image_media');i=module('image_inputs');c=module('candidate_root_custody')
class MVPSlotsTests(unittest.TestCase):
 def test_failed_mvp_root_is_preserved_and_next_generation_is_distinct(self):
  self.assertEqual(a.GENERATIONS['mvp-live'][0],'toddy-mvp-live-image-4')
  self.assertNotEqual(a.GENERATIONS['mvp-live'][0],'toddy-mvp-live-image-1')
  self.assertEqual(a.GENERATIONS['mvp-live-reviewed'][0],'toddy-mvp-live-image-2')
  with patch.object(c,'PROFILE','offline'):
   c.configure('mvp-live')
   self.assertEqual(c.WORK.name,a.GENERATIONS['mvp-live'][0])
   self.assertEqual(c.REVIEWED.name,a.GENERATIONS['mvp-live-reviewed'][0])
  c.configure('offline')
 def test_delivery_class_cannot_cross_standard_or_mvp_slots(self):
  manifest={'delivery_class':a.MVP_CLASS,'g2_eligible':False}
  a.check_delivery_kind('mvp-live',manifest);a.check_delivery_kind('base',{})
  for kind,wrong in [('live',manifest),('mvp-base',{}),('mvp-live',{'delivery_class':a.MVP_CLASS,'g2_eligible':True})]:
   with self.assertRaisesRegex(ValueError,'delivery class'):a.check_delivery_kind(kind,wrong)
  self.assertEqual(a.reviewed_root_name('mvp-base-reviewed'),'mvp-offline-root-2')
  self.assertEqual(a.reviewed_root_name('mvp-live'),'mvp-live-root-2')
  for kind in ('base','live'):
   self.assertNotEqual(a.GENERATIONS[kind],a.GENERATIONS['mvp-'+kind])
   self.assertNotEqual(i.OUTPUT[kind],i.OUTPUT['mvp-'+kind])
 def test_mvp_media_uses_only_separate_fixed_generations(self):
  names=('IMAGE','JOURNAL','COMPRESSION','INITRAMFS','MEDIA','PROJECTION','MVP')
  before={name:getattr(m,name) for name in names}
  with patch.multiple(m,**before):
   m.configure_mvp()
   for name in names[:-1]:self.assertIn('toddy-mvp-',str(getattr(m,name)))
   self.assertTrue(m.MVP)
   self.assertEqual(m.IMAGE.name,'mvp-live-root-2')
   self.assertEqual(m.PROJECTION.parent.name,'toddy-mvp-image-projection-4')
  self.assertEqual({name:getattr(m,name) for name in names},before)
 def test_exact_wrapper_input_split_keeps_mvp_kind_intact(self):
  result=subprocess.run(['/bin/bash','-c','set -eu; action=${1#inputs-}; kind=${action%-*}; operation=${action##*-}; printf "%s %s" "$operation" "$kind"','fixture','inputs-mvp-live-prepare'],check=True,capture_output=True,text=True)
  self.assertEqual(result.stdout,'prepare mvp-live')
  source=(ROOT/'scripts/build/phase2/image_native.sh').read_text()
  for action in ('inputs-mvp-base-prepare','inputs-mvp-live-prepare','finalize-mvp-base','finalize-mvp-live','stage-mvp-live','media-mvp-iso'):self.assertIn(action,source)
