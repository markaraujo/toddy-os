"""Mutable metadata cannot select new executable input or expose corrupt plugins."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('vim_download_guard',ROOT/'scripts/build/h07/verified-vim-curl.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
class DownloadGuard(unittest.TestCase):
    def setUp(self):self.manifest=json.loads((ROOT/'config/vim-glvs-inputs.lock.json').read_text())
    def test_all_fixed_plugin_versions_and_metadata_are_selected(self):
        for row in self.manifest['components']:
            self.assertEqual(guard.classify(row['download_url'],self.manifest,False),('plugin',row))
            self.assertEqual(guard.classify(row['page_url'],self.manifest,False),('metadata',row))
    def test_unknown_origin_version_and_ambiguous_query_are_rejected(self):
        for url in ['http://www.vim.org/scripts/script.php?script_id=4979','https://www.vim.org/scripts/download_script.php?src_id=999999','https://www.vim.org/scripts/script.php?script_id=4979&script_id=514','https://evil.example/scripts/script.php?script_id=4979','https://www.vim.org@evil.example/scripts/script.php?script_id=4979']:
            with self.assertRaises(ValueError):guard.classify(url,self.manifest,False)
    def test_historical_source_is_head_only(self):
        url='https://www.vim.org/scripts/download_script.php?src_id=1'
        self.assertEqual(guard.classify(url,self.manifest,True)[0],'historical-head-only')
        with self.assertRaises(ValueError):guard.classify(url,self.manifest,False)
    def test_changed_metadata_and_modelines_are_rejected(self):
        row=self.manifest['components'][0]
        page='Click on the package to download\n'+row['observed_row']+'\n'
        guard.validate(page.encode(),'metadata',row)
        for changed in [page.replace(str(row['source_id']),'999999'),page.replace(row['upstream_filename'],'other.vim'),page+'vim: set shell=evil:\n']:
            with self.assertRaises(ValueError):guard.validate(changed.encode(),'metadata',row)
    def test_unverified_plugin_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'hash/size'):guard.validate(b'changed executable','plugin',self.manifest['components'][0])
if __name__=='__main__':unittest.main()
