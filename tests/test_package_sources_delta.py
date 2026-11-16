from types import SimpleNamespace
from unittest import mock
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
import package_sources_delta as delta


class SourceDeltaTests(unittest.TestCase):
    def packages(self):
        old=[dict(name='toddy-installer',version=delta.OLD_VERSION,architecture='amd64',archive_sha256='a'*64,component_record_sha256='b'*64,recipe_sha256='c'*64),dict(name='unchanged',version='1',architecture='all',archive_sha256='d'*64,component_record_sha256='e'*64,recipe_sha256='f'*64)]
        new=[dict(old[0],version=delta.NEW_VERSION,archive_sha256='1'*64,component_record_sha256='2'*64),old[1]]
        return old,new

    def test_only_exact_installer_transition_reuses_other_decisions(self):
        old,new=self.packages()
        self.assertEqual(delta.changes(old,new),['unchanged'])
        new[1]=dict(new[1],recipe_sha256='3'*64)
        with self.assertRaisesRegex(ValueError,'Only actual installer'):
            delta.changes(old,new)

    def test_same_name_or_archive_alone_does_not_authorize_new_scope(self):
        old,new=self.packages()
        new[0]=dict(new[0],version='0.2.0-1+toddy5')
        with self.assertRaises(ValueError):delta.changes(old,new)
        with self.assertRaises(ValueError):delta.changes(old,new+[dict(new[1],name='additional')])

    def test_reuse_requires_identical_group_order_content_and_sizes(self):
        a=SimpleNamespace(size=10000,sha256='a'*64);b=SimpleNamespace(size=10000,sha256='b'*64)
        prior=SimpleNamespace(inventory={'source_assets':[{'name':'selected-sources-001.tar','sha256':'1'*64,'bytes':1},{'name':'selected-sources-002.tar','sha256':'2'*64,'bytes':1}],'license_assets':[]},asset_members={'selected-sources-001.tar':['a'],'selected-sources-002.tar':['b']},rows={'a':{'sha256':'a'*64,'bytes':10000},'b':{'sha256':'b'*64,'bytes':10000}})
        with mock.patch.object(delta.s,'MAX_ASSET',35000):
            plan=delta.planned({'a':a,'b':b},'selected-sources',prior)
            self.assertIsNotNone(plan[0][2]);self.assertIsNotNone(plan[1][2])
            plan=delta.planned({'a':SimpleNamespace(size=10000,sha256='c'*64),'b':b},'selected-sources',prior)
            self.assertIsNone(plan[0][2]);self.assertIsNotNone(plan[1][2])
