"""Info registration must declare its generated resource without a staged index."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/build'))
spec=importlib.util.spec_from_file_location('info_packager',ROOT/'scripts/build/stage_package.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class InfoRegistration(unittest.TestCase):
 def test_docs_without_staged_index_declare_actual_shared_write(self):
  paths=['/usr/bin/aspell','/usr/share/info/aspell.info','/usr/share/info/aspell-dev.info.gz']
  documents,generated=module.info_registration(paths)
  self.assertEqual(documents,paths[1:]);self.assertEqual(generated,['/usr/share/info/dir'])
 def test_only_supported_info_paths_trigger_registration(self):
  paths=['/usr/share/info/manual.info.xz','/usr/share/info/other.info.bz2','/usr/share/info/dir','/usr/share/info/draft.info.old','/opt/misplaced.info']
  self.assertEqual(module.info_registration(paths),(paths[:2],['/usr/share/info/dir']))
  self.assertEqual(module.info_registration(paths[2:]),([],[]))
