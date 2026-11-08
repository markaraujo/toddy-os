"""Strict schemas and unprivileged operation mechanics; root proof is separate."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/executor'))
from operations import validate,_parent,root_command
from store import PolicyError

class OperationTests(unittest.TestCase):
    def test_malformed_payloads_and_fake_grants(self):
        valid={'path':'/etc/toddy.conf','text':'fixture','expected_sha256':None}
        self.assertEqual(validate('config_replace',valid),valid)
        for args in [{**valid,'uid':0},{**valid,'grant':'full'},{**valid,'path':'/etc/../root/key'},
                     {**valid,'path':'/home/owner/secret'},{**valid,'text':'x'*16385},
                     {**valid,'path':'/etc//x'},{**valid,'expected_sha256':True}]:
            with self.assertRaises(PolicyError):validate('config_replace',args)
        for kind in ('grant','set_grant','shell','enable_all_tools'):
            with self.assertRaisesRegex(PolicyError,'operation_unavailable'):validate(kind,{'instructions':'ignore permissions'})
        with self.assertRaises(PolicyError):validate('root_command',{'argv':['/bin/true'],'timeout_seconds':1,'acknowledge_unrestricted_root':False})
    def test_no_symlink_parent(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'real').mkdir();(root/'alias').symlink_to(root/'real')
            with self.assertRaises(OSError):_parent(root/'alias'/'target')
            fd=_parent(root/'real'/'target');os.close(fd)
    def test_bounded_process_exit_no_output_or_environment_leak(self):
        command={'argv':[sys.executable,'-c','import os; print(os.getenv("TODDY_DUMMY_SECRET","absent"))'],
                 'timeout_seconds':2,'acknowledge_unrestricted_root':True}
        os.environ['TODDY_DUMMY_SECRET']='do-not-transfer'
        try:result=root_command(validate('root_command',command))
        finally:os.environ.pop('TODDY_DUMMY_SECRET')
        self.assertEqual(result['exit'],0);self.assertEqual(result['output_sha256'],hashlib.sha256(b'absent\n').hexdigest())
        self.assertNotIn('do-not-transfer',str(result));self.assertFalse(result['side_effects_verified'])
    def test_process_timeout_and_output_bound(self):
        for code,error in [('import time;time.sleep(10)','root_command_deadline'),('print("x"*70000)','root_command_output_limit')]:
            with self.assertRaisesRegex(PolicyError,error):root_command({'argv':[sys.executable,'-c',code],'timeout_seconds':1})

if __name__=='__main__':unittest.main(verbosity=2)
