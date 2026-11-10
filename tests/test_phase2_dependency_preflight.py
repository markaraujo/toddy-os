"""Package safety: stale revisions and unpacked dependencies fail before writes."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('dependency_preflight',Path(__file__).resolve().parents[1]/'scripts/build/phase2/dependency_preflight.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class DependencyPreflightTests(unittest.TestCase):
 def test_stale_exact_revision_refused(self):
  with self.assertRaisesRegex(ValueError,'Unsatisfied owned dependency'):
   module.verify('gtk3 (= 3.24.52-1+toddy1)',lambda _:('install ok installed','3.24.52-1+toddy2'),lambda a,op,b:a==b)
 def test_unpacked_is_not_installed(self):
  with self.assertRaisesRegex(ValueError,'Unsatisfied owned dependency'):
   module.verify('gtk3',lambda _:('install ok unpacked','3.24.52-1+toddy2'),lambda *_:True)
 def test_alternative_can_use_owned_dependency(self):
  module.verify('missing | gtk3 (= 3.24.52-1+toddy2)',lambda n:('install ok installed','3.24.52-1+toddy2') if n=='gtk3' else ('absent',''),lambda a,op,b:a==b)
 def test_unsupported_syntax_cannot_bypass_guard(self):
  with self.assertRaisesRegex(ValueError,'Unsupported dependency syntax'):
   module.verify('gtk3 [amd64]',lambda _:('install ok installed','1'),lambda *_:True)
