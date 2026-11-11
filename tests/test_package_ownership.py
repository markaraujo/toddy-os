import sys
from pathlib import Path
import stat
import unittest
import json
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

class CupsOwnershipTests(unittest.TestCase):
    def setUp(self):
        source=Path(__file__).resolve().parents[1]/'config/package-ownership-policy.json'
        rows=json.loads(source.read_text())['privileged_exceptions']
        self.policy={(row['package'],row['path']):row for row in rows}

    def test_cups_policy_has_only_exact_service_paths_without_setuid(self):
        rows=[row for (package,path),row in self.policy.items() if package=='cups']
        self.assertEqual(len(rows),14)
        for row in rows:
            self.assertTrue(row['path'].startswith(('/etc/cups','/var/cache/cups','/var/spool/cups','/run/cups/certs')))
            self.assertFalse(row['mode']&0o6000)
        self.assertEqual(ownership_action('cups','/run/cups/certs',9,19,stat.S_IFDIR|0o511,101,101,self.policy),(9,19,False))

    def test_wrong_service_identity_or_elevated_mode_is_refused(self):
        for uid,gid,mode in [(0,19,0o511),(9,9,0o511),(9,19,0o4511)]:
            with self.assertRaises(ValueError):
                ownership_action('cups','/run/cups/certs',uid,gid,stat.S_IFDIR|mode,101,101,self.policy)

    def test_service_user_cannot_own_an_unreviewed_executable(self):
        with self.assertRaises(ValueError):
            ownership_action('cups','/usr/bin/unreviewed',9,19,stat.S_IFREG|0o755,101,101,self.policy)


class FuseOwnershipTests(unittest.TestCase):
    def test_only_exact_reviewed_native_helper_is_allowed(self):
        rows=json.loads((Path(__file__).resolve().parents[1]/'config/package-ownership-policy.json').read_text())['privileged_exceptions']
        policy={(r['package'],r['path']):r for r in rows}
        selected=[r for r in rows if r['package']=='fuse']
        self.assertEqual([(r['path'],r['uid'],r['gid'],r['mode']) for r in selected],[('/usr/bin/fusermount3',0,0,0o4755)])
        self.assertEqual(ownership_action('fuse','/usr/bin/fusermount3',0,0,stat.S_IFREG|0o4755,101,101,policy),(0,0,False))
        for name,uid,gid,mode in [('/usr/bin/fusermount3',101,101,0o4755),('/usr/bin/fusermount3',0,1,0o4755),('/usr/bin/fusermount3',0,0,0o6755),('/usr/sbin/mount.fuse3',0,0,0o4755)]:
            with self.subTest(name=name,uid=uid,gid=gid,mode=mode):
                with self.assertRaises(ValueError):ownership_action('fuse',name,uid,gid,stat.S_IFREG|mode,101,101,policy)
