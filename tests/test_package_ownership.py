import sys
from pathlib import Path
import stat
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build'))
from package_ownership import ownership_action

class OwnershipTests(unittest.TestCase):
    def test_build_docs_become_root_owned(self):
        self.assertEqual(ownership_action('cmake','/usr/share/doc/cmake/Licenses',101,101,stat.S_IFDIR|0o755,101,101,{}),(0,0,True))
    def test_build_owned_suid_is_not_silently_elevated(self):
        with self.assertRaises(ValueError):ownership_action('probe','/usr/bin/probe',101,101,stat.S_IFREG|0o4755,101,101,{})
    def test_reviewed_system_group_and_mode_preserved(self):
        policy={('util-linux','/usr/bin/wall'):{'uid':0,'gid':5,'mode':0o2755}}
        self.assertEqual(ownership_action('util-linux','/usr/bin/wall',0,5,stat.S_IFREG|0o2755,101,101,policy),(0,5,False))
        with self.assertRaises(ValueError):ownership_action('util-linux','/usr/bin/wall',0,5,stat.S_IFREG|0o4755,101,101,policy)
    def test_undeclared_privileged_helper_refused(self):
        with self.assertRaises(ValueError):ownership_action('probe','/usr/bin/probe',0,0,stat.S_IFREG|0o4755,101,101,{})
