"""Source fixtures only; no guest install, desktop, dconf or artwork mutation."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('desktop_background_upgrade',ROOT/'scripts/build/phase2/desktop_background_upgrade.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)


def inventory(root):
    result={}
    for path in root.rglob('*'):
        info=path.stat();row={'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid}
        if path.is_dir():row['directory']=True
        else:row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        result['/'+str(path.relative_to(root))]=row
    return result


class BackgroundUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.stage=self.root/'stage'
        u.defaults.stage(self.stage,ROOT)
        (self.stage/u.defaults.DATABASE.lstrip('/')).write_bytes(b'Unqualified source-only database fixture')
        (self.stage/u.defaults.DATABASE.lstrip('/')).chmod(0o644)
        self.record={'name':u.NAME,'version':u.OLD,'installed':True,'payload':inventory(self.stage)}
        self.approved={'version':u.OLD,'archive_sha256':'a'*64,'component_record_sha256':'b'*64}

    def test_only_three_settings_change_and_other_defaults_and_assets_are_preserved(self):
        before={name:path.read_bytes() for name in self.record['payload'] if not self.record['payload'][name].get('directory') for path in [self.stage/name.lstrip('/')]}
        result=u.render(self.stage,ROOT,self.approved,self.record)
        after={name:(self.stage/name.lstrip('/')).read_bytes() for name in before}
        changed={name for name in before if before[name]!=after[name]}
        self.assertEqual(changed,{u.defaults.KEYFILE,'/usr/share/doc/'+u.NAME+'/README'})
        old=before[u.defaults.KEYFILE].decode().splitlines();new=after[u.defaults.KEYFILE].decode().splitlines()
        self.assertEqual(len(old),len(new))
        self.assertEqual([a.partition('=')[0] for a,b in zip(old,new) if a!=b],['picture-uri','picture-uri-dark','picture-options'])
        self.assertIn(u.LIGHT,after[u.defaults.KEYFILE].decode());self.assertIn(u.DARK,after[u.defaults.KEYFILE].decode())
        self.assertFalse((self.stage/'usr/share/backgrounds').exists())
        self.assertFalse((self.stage/'home').exists());self.assertFalse((self.stage/'etc/dconf/db/toddy-desktop.d/locks').exists())
        manifest=json.loads((self.stage/'usr/share/doc'/u.NAME/'source-manifest.json').read_text())
        self.assertEqual(manifest,result);self.assertEqual(manifest['version'],u.VERSION)
        self.assertEqual(manifest['source_inputs']['scripts/build/phase2/branding_stage.py']['sha256'],u.digest(ROOT/'scripts/build/phase2/branding_stage.py'))

    def test_edited_conffile_or_generated_database_is_rejected_before_render(self):
        for name in (u.defaults.KEYFILE,u.defaults.PROFILE,u.defaults.DATABASE):
            with self.subTest(name=name):
                path=self.stage/name.lstrip('/');original=path.read_bytes();path.write_bytes(original+b'owner edit')
                with self.assertRaisesRegex(ValueError,'payload drift'):u.render(self.stage,ROOT,self.approved,self.record)
                path.write_bytes(original)
        self.assertFalse((self.stage/'usr/share/doc'/u.NAME/'source-manifest.json').exists())

    def test_unexpected_files_symlinks_or_modes_are_rejected(self):
        extra=self.stage/'etc/unexpected';extra.write_text('preserve')
        with self.assertRaisesRegex(ValueError,'Unexpected'):u.render(self.stage,ROOT,self.approved,self.record)
        extra.unlink();path=self.stage/u.defaults.KEYFILE.lstrip('/');original=path.read_bytes();path.unlink();path.symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError,'canonical regular'):u.render(self.stage,ROOT,self.approved,self.record)
        path.unlink();path.write_bytes(original);path.chmod(0o600)
        with self.assertRaisesRegex(ValueError,'payload drift'):u.render(self.stage,ROOT,self.approved,self.record)

    def test_frozen_old_archive_and_record_custody_detect_changed_bytes(self):
        if not shutil.which('dpkg-deb'):self.skipTest('Tiny archive fixture requires dpkg-deb; no install is run')
        repo=self.root/'repo';evidence=repo/'docs/evidence';evidence.mkdir(parents=True)
        records=self.root/'records';records.mkdir();cache=self.root/'cache';cache.mkdir()
        control=self.stage/'DEBIAN';control.mkdir();(control/'control').write_text('Package: '+u.NAME+'\nVersion: '+u.OLD+'\nArchitecture: all\nMaintainer: Source Fixture <fixture@example.invalid>\nDescription: unqualified fixture only\n')
        archive=cache/(u.NAME+'_'+u.OLD+'_all.deb')
        subprocess.run(['dpkg-deb','--build',str(self.stage),str(archive)],check=True,capture_output=True);archive.chmod(0o644)
        self.record['archive_sha256']=u.digest(archive)
        record=records/(u.NAME+'_'+u.OLD+'_all.json');record.write_text(json.dumps(self.record));record.chmod(0o644)
        approved=dict(self.approved,name=u.NAME,archive_sha256=u.digest(archive),component_record_sha256=u.digest(record))
        (evidence/'B02-desktop-runtime-manifest.json').write_text(json.dumps({'components':[approved]}))
        self.assertEqual(u.baseline(repo,records,cache)[2],archive)
        with archive.open('ab') as stream:stream.write(b'tamper')
        with self.assertRaisesRegex(ValueError,'custody differs'):u.baseline(repo,records,cache)

    def test_direct_script_import_and_consumer_compile_without_native_execution(self):
        compile(u.CONSUMER,'fixed-native-consumer','exec')
        result=subprocess.run(['python3','-I',str(ROOT/'scripts/build/phase2/desktop_background_upgrade.py'),'invalid'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('Expected install or check',result.stderr)
        with patch.object(u.os,'getuid',return_value=1000),patch.object(u.sys,'argv',['driver','install']),patch.object(u.subprocess,'run') as run:
            with self.assertRaises(AssertionError):u.main()
            run.assert_not_called()


if __name__=='__main__':unittest.main()
