"""Source parser/layout/denial fixtures; no compile, mkfs, disk or VM execution."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/build/phase2'/(name+'.py'));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
n=module('dosfstools_native');i=module('dosfstools_inspect');p=module('dosfstools_file_probe')


class DosfstoolsSourceTests(unittest.TestCase):
    def test_direct_script_import_and_wrong_uid_refusal_precede_native_calls(self):
        for name in ('dosfstools_native','dosfstools_inspect','dosfstools_file_probe'):
            result=subprocess.run(['python3','-I',str(ROOT/'scripts/build/phase2'/(name+'.py')),'--help'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        with patch.object(p.os,'getuid',return_value=1000),patch.object(p.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'unprivileged native tester'):p.probe(Path('/dev'),Path('/usr/sbin'))
            run.assert_not_called()
        with patch.object(n.sys,'argv',['driver','prepare']),patch.object(n.os,'getuid',return_value=1000),patch.object(n.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'builder root'):n.main()
            run.assert_not_called()

    def fixture_results(self,root):
        names=['fixture-%02d.fsck'%num for num in range(39)]+['check-huge.fsck']
        makefile=root/'Makefile.am';makefile.write_text('TESTS = '+' \\\n\t'.join(names)+'\n\nXFAIL_TESTS = check-huge.fsck\n')
        for name in names:(root/(Path(name).stem+'.trs')).write_text(':test-result: '+('XFAIL' if name=='check-huge.fsck' else 'PASS')+'\n')
        return makefile

    def test_all40_results_and_only_upstream_expected_failure_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);makefile=self.fixture_results(root)
            result=i.tests(root,makefile);self.assertEqual(result['total'],40);self.assertEqual(result['pass'],39);self.assertEqual(result['skip'],0)
            for outcome in ('SKIP','FAIL','ERROR','XPASS'):
                (root/'fixture-00.trs').write_text(':test-result: '+outcome+'\n')
                with self.assertRaisesRegex(ValueError,'failure/skip'):i.tests(root,makefile)
            (root/'fixture-00.trs').unlink()
            with self.assertRaisesRegex(ValueError,'All40'):i.tests(root,makefile)

    def test_native_layout_requires_regular_sbin_programs_and_exact_relative_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sbin=root/'usr/sbin';sbin.mkdir(parents=True)
            for name in ('mkfs.fat','fsck.fat','fatlabel'):(sbin/name).write_bytes(b'\x7fELF source-only fixture')
            for name,target in i.ALIASES.items():(sbin/name).symlink_to(target)
            doc=root/'usr/share/doc/dosfstools-4.2';doc.mkdir(parents=True)
            for name in ('COPYING','README'):(doc/name).write_text('Source fixture only')
            self.assertEqual(len(i.layout(root)['programs']),3)
            (sbin/'mkdosfs').unlink();(sbin/'mkdosfs').symlink_to('/dev/sda')
            with self.assertRaisesRegex(ValueError,'compatibility'):i.layout(root)

    def test_fat32_geometry_checks_real_layout_fields_without_formatting(self):
        boot=bytearray(512);boot[510:512]=b'\x55\xaa';boot[82:90]=b'FAT32   ';boot[71:82]=b'TODDYTEST  '
        struct.pack_into('<H',boot,11,512);boot[13]=1;struct.pack_into('<H',boot,14,32);boot[16]=2;struct.pack_into('<I',boot,32,p.SIZE//512);struct.pack_into('<I',boot,36,2017)
        self.assertGreater(p.inspect_boot(boot,p.SIZE)['clusters'],65525)
        struct.pack_into('<H',boot,17,512)
        with self.assertRaisesRegex(ValueError,'geometry'):p.inspect_boot(boot,p.SIZE)

    def test_recipe_pins_frozen_configuration_xxd_and_safe_fixed_file_operand(self):
        build=(ROOT/'scripts/build/phase2/dosfstools-build.sh').read_text()
        self.assertIn('command -v xxd',build);self.assertIn("XXD_FOUND = yes",build)
        self.assertIn('--sbindir=/usr/sbin --enable-compat-symlinks',build)
        self.assertIn('make -j1 check',build);self.assertNotIn('|| true',build)
        self.assertEqual(n.SHA,'64926eebf90092dca21b14259a5301b7b98e7b1943e8a201c7d726084809b527')
        self.assertEqual(n.VERSION,'4.2-1+toddy1');self.assertEqual(n.DEPENDS,'glibc (>= 2.44-1)')
        source=(ROOT/'scripts/build/phase2/dosfstools_file_probe.py').read_text()
        self.assertIn('os.O_EXCL|os.O_NOFOLLOW',source);self.assertIn("operand='/proc/self/fd/'",source)
        self.assertNotIn('losetup',source);self.assertNotIn('/dev/sd',source)
        with patch.object(n.shutil,'disk_usage',return_value=type('Space',(),{'free':16*1024**3})()):
            with self.assertRaisesRegex(ValueError,'reserve'):n.reserve()


if __name__=='__main__':unittest.main()
