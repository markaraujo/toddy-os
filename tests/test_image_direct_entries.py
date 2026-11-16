"""Real isolated Python entry imports and fixed source wrapper syntax/denial."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


class DirectImageEntryTests(unittest.TestCase):
    @unittest.skipIf(ROOT==Path('/opt/toddy-build'),'Configured guest entry is not executed by this host import fixture')
    def test_isolated_real_entry_imports_reach_fixed_path_gate_without_guest_access(self):
        for script,args in [('image_projection.py',[]),('image_assemble.py',['base']),('image_media.py',['compress'])]:
            path=ROOT/'scripts/build/phase2'/script
            result=subprocess.run([sys.executable,'-I',str(path),*args],capture_output=True,text=True,
                env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C'},timeout=30)
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn('ModuleNotFoundError',result.stderr)
            self.assertNotIn('ImportError',result.stderr)
            self.assertIn('coordinator',result.stderr)

    def test_native_outer_wrapper_has_valid_shell_and_denies_unprivileged_host(self):
        path=ROOT/'scripts/build/phase2/image_native.sh'
        subprocess.run(['/usr/bin/bash','-n',str(path)],check=True)
        if os.getuid()==0:self.skipTest('Non-root host denial fixture requires unprivileged user')
        result=subprocess.run(['/usr/bin/bash',str(path),'base'],capture_output=True,text=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('mount:',result.stderr)
        self.assertNotIn('chroot:',result.stderr)


if __name__=='__main__':unittest.main()
