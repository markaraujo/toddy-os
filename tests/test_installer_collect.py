"""Synthetic completed-journal/report fixtures; no native install or boot proof."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('installer_collect',ROOT/'scripts/build/phase2/installer_collect.py')
c=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(c)
from runtime.installer.disk_plan import InstallError,make_plan


class InstallerCollectTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.inputs=self.root/'inputs';self.inputs.mkdir()
        self.journal=self.root/'journal';self.journal.mkdir();(self.journal/'writer.lock').touch(mode=0o600)
        self.reports=self.root/'reports';self.reports.mkdir()
        self.disk={'path':'/dev/fixture-disk','major_minor':'253:16','serial':'TODDY-INSTALL-FIXTURE',
            'size':16*1024**3,'sector_size':512,'model':'QEMU HARDDISK','driver':'virtio_blk',
            'readonly':False,'mounted':False,'blank':True,'virtual':True}
        options={'operation_id':'a'*32,'boot_mode':'bios','username':'owner','uid':1000,'gid':1000,
            'locale':'en_US.UTF-8','timezone':'UTC','hostname':'toddy-owner','ai_choice':'later','extras':[]}
        self.manifest={'catalog_sha256':'c'*64,'bytes':2*1024**3,'storage':{'fixture_only':True}}
        self.descriptor={'payload_manifest_sha256':'b'*64,'policy_sha256':'d'*64,'image_manifest_sha256':'e'*64}
        self.plan=make_plan(self.disk,options,{'sha256':'b'*64,'catalog_sha256':'c'*64,'bytes':2*1024**3})
        self.native=SimpleNamespace(manifest=self.manifest,descriptor=self.descriptor,boot={'kernel_sha256':'f'*64},
            pins={'source:installed_boot.py':'1'*64},recheck=Mock())
        self.system=SimpleNamespace(require_root=Mock(),probe=Mock(return_value={**self.disk,'blank':False}))
        db=sqlite3.connect(self.journal/'operations.sqlite')
        db.executescript('CREATE TABLE operations(id TEXT PRIMARY KEY,plan_sha256 TEXT,state TEXT,step TEXT,cancel INTEGER); CREATE TABLE receipts(operation_id TEXT,step TEXT,body TEXT,PRIMARY KEY(operation_id,step));')
        db.execute('INSERT INTO operations VALUES(?,?,?,?,?)',('a'*32,self.plan['plan_sha256'],'completed','complete',0))
        receipts={'filesystems':{'root_uuid':'abcd-1234','esp_uuid':None},
            'boot':{'verified':True,'kernel':'vmlinuz-'+c.RELEASE,'initramfs':'initramfs-'+c.RELEASE+'-installed.img','kernel_sha256':'f'*64,'initramfs_sha256':'2'*64},
            'grub':{'verified':True,'config_path':'/etc/toddy/grub.cfg','boot_link':'../../etc/toddy/grub.cfg','config_sha256':'3'*64}}
        db.executemany('INSERT INTO receipts VALUES(?,?,?)',[('a'*32,k,json.dumps(v)) for k,v in receipts.items()]);db.commit();db.close()
        self.reportdir=self.reports/('finalization-target-'+'a'*32);self.reportdir.mkdir()
        post={
            'native-dpkg-database':{'configured_packages':3,'database_audit_empty':True},
            'fresh-system-accounts':{'account_policy_sha256':'d'*64,'locked_accounts':3,'fresh_files':7},
            'pam-service-policy':{'selected_owned_policy_files':1,'policy_sha256':'d'*64,'default_target':'graphical.target','display_manager':'gdm.service'},
            'generated-caches':{'native_commands':2,'qualified_cache_outputs':0},
            'private-state-and-keys':{'fresh_account_policy':True,'root_and_home_empty':True,'known_secret_namespaces_empty':True,'complete_image_bound_to_qualified_projection':'e'*64},
            'runtime-linkage':{'native_elf_consumers':['/usr/bin/bash','/usr/bin/python3','/usr/bin/gnome-shell','/usr/sbin/gdm'],'unresolved_dependencies':0},
            'ownership-xattrs':{'entries':10,'unreviewed_xattrs':0,'cross_device_entries':0},
            'whole-image-attribution':{'image_manifest_sha256':'e'*64,'entries':10},
            'foundation-recovery':{'source_owned_recovery_paths':list(c.payload_module().RECOVERY_PATHS),'unchanged':True}}
        for name,values in post.items():
            (self.reportdir/(name+'.json')).write_bytes(c.payload_module().encoded({'check':name,'input_manifest_sha256':'b'*64,'passed':True,'exit_status':0,'postconditions':values}))
        # Only root ownership/path checks and available host capacity are fixtures.
        # Real report schemas, journal SQL, exact plan checks and writes are exercised.
        for mocked in [patch.object(c,'INPUTS',self.inputs),patch.object(c,'JOURNAL',self.journal),patch.object(c,'REPORTS',self.reports),
                patch.object(c,'secured',side_effect=lambda path,**kw:Path(path) if Path(path).is_file() and not Path(path).is_symlink() else (_ for _ in ()).throw(InstallError('fixture_missing'))),
                patch.object(c,'private_directory'),patch.object(c.payload_module(),'available_bytes',return_value=128*1024**3)]:
            mocked.start();self.addCleanup(mocked.stop)

    def test_preserves_real_bytes_without_install_replay_or_boot_claim(self):
        before=(self.journal/'operations.sqlite').read_bytes()
        result=c.collect(self.plan,self.native,self.system)
        handoff=json.loads(Path(result['handoff']).read_bytes())
        self.assertFalse(handoff['production_ready']);self.assertFalse(handoff['fresh_owner_login_verified'])
        self.assertFalse(handoff['recovery_verified']);self.assertEqual(handoff['detached_boots_collected'],0)
        self.assertEqual(handoff['payload_storage'],self.manifest['storage'])
        for name,sha in handoff['finalizer_reports_sha256'].items():
            raw=(self.inputs/'qualification'/(name+'.json')).read_bytes()
            self.assertEqual(raw,(self.reportdir/(name+'.json')).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
        self.assertEqual(before,(self.journal/'operations.sqlite').read_bytes())
        self.assertEqual(c.collect(self.plan,self.native,self.system),result)
        self.system.probe.assert_called_with('/dev/fixture-disk',require_blank=False)
        self.assertEqual(list(self.inputs.glob('qualification/boot-*')),[])

    def test_incomplete_journal_and_missing_report_fail_before_outputs(self):
        db=sqlite3.connect(self.journal/'operations.sqlite');db.execute("UPDATE operations SET state='needs-reconciliation'");db.commit();db.close()
        with self.assertRaisesRegex(InstallError,'completed_exact'):c.collect(self.plan,self.native,self.system)
        self.system.probe.assert_not_called();self.assertEqual(list(self.inputs.iterdir()),[])
        db=sqlite3.connect(self.journal/'operations.sqlite');db.execute("UPDATE operations SET state='completed'");db.commit();db.close()
        (self.reportdir/'ownership-xattrs.json').unlink()
        with self.assertRaises(InstallError):c.collect(self.plan,self.native,self.system)
        self.assertEqual(list(self.inputs.iterdir()),[])

    def test_differing_or_redirected_evidence_is_not_overwritten(self):
        destination=self.inputs/'qualification';destination.mkdir();output=destination/'ownership-xattrs.json';output.write_bytes(b'old')
        with self.assertRaisesRegex(InstallError,'existing_finalizer'):c.collect(self.plan,self.native,self.system)
        self.assertEqual(output.read_bytes(),b'old')
        output.unlink();output.symlink_to(self.root/'absent')
        with self.assertRaises(InstallError):c.collect(self.plan,self.native,self.system)
        self.assertTrue(output.is_symlink())

    def test_active_writer_and_changed_target_fail_without_output(self):
        import fcntl
        with (self.journal/'writer.lock').open('rb') as writer:
            fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):c.collect(self.plan,self.native,self.system)
        self.system.probe.return_value={**self.disk,'blank':False,'mounted':True}
        with self.assertRaises(InstallError):c.collect(self.plan,self.native,self.system)
        self.assertEqual(list(self.inputs.iterdir()),[])

    def test_missing_measurements_and_insufficient_capacity_never_publish(self):
        path=self.reportdir/'whole-image-attribution.json';original=path.read_bytes()
        path.write_text(json.dumps({'passed':True}))
        with self.assertRaisesRegex(InstallError,'finalizer_receipt'):c.collect(self.plan,self.native,self.system)
        self.assertEqual(list(self.inputs.iterdir()),[])
        path.write_bytes(original)
        with patch.object(c.payload_module(),'available_bytes',return_value=16*1024**3):
            with self.assertRaisesRegex(ValueError,'storage_reserve'):c.collect(self.plan,self.native,self.system)
        self.assertEqual(list(self.inputs.iterdir()),[])

    def test_review_refuses_extra_secret_field_and_cannot_create_missing_journal(self):
        review=self.root/'review.json';value={'state':'qualification-review-only','disk_writes':False,'plan':self.plan}
        review.write_text(json.dumps(value));self.assertEqual(c.read_review(review),self.plan)
        review.write_text(json.dumps({**value,'password':'never-accepted'}))
        with self.assertRaises(InstallError):c.read_review(review)
        (self.journal/'operations.sqlite').unlink()
        with self.assertRaises(InstallError):c.read_operation(self.plan)
        self.assertFalse((self.journal/'operations.sqlite').exists())

if __name__=='__main__':unittest.main()
