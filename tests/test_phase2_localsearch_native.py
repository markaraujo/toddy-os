"""Native selection must retain denials and actual nonzero original case counts."""
import copy,importlib.util,json,tarfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('localsearch_native',ROOT/'scripts/build/phase2/prepare_localsearch_native.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class LocalSearchSelection(unittest.TestCase):
 def fixture(self):
  # Shape of frozen upstream Meson registration; no OS/runtime success fixture.
  return [{'name':n,'cmd':['/usr/bin/python3','/src/tests/functional-tests/'+('test_'+n+'.py')],
           'protocol':'exitcode','workdir':None,'timeout':120 if n.startswith('test_') else 30,
           'suite':['localsearch:functional' if n.startswith('test_') else 'localsearch:malice']}
          for n in module.SELECTED]
 def test_missing_or_duplicate_denial_program_is_rejected(self):
  rows=self.fixture()
  for changed in [rows[:-1],rows+[copy.deepcopy(rows[-1])]]:
   with self.assertRaises(AssertionError):module.select_tests(changed)
 def test_functional_only_or_unexpected_launcher_is_rejected(self):
  rows=self.fixture();rows[-1]['suite']=['localsearch:functional']
  with self.assertRaises(AssertionError):module.select_tests(rows)
  rows=self.fixture();rows[-1]['cmd'][0]='/bin/true'
  with self.assertRaises(AssertionError):module.select_tests(rows)
 def test_full_selection_requires_twenty_real_cases(self):
  self.assertEqual(len(module.select_tests(self.fixture())),9)
  self.assertEqual(sum(module.SELECTED.values()),20)
