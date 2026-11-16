"""Tiny source-only tar/Git fixtures; no native/publication qualification."""
import hashlib
import importlib.util
import json
from unittest.mock import patch
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package_sources_fixture',ROOT/'scripts/build/phase2/package_sources.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class PackageSourceTests(unittest.TestCase):
    def test_only_explicit_flat_matching_cache_files_are_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'source.tar.gz').write_bytes(b'unqualified source fixture');resolver=r.Resolver([root])
            sha=hashlib.sha256(b'unqualified source fixture').hexdigest()
            source=resolver.source('source.tar.gz',sha);self.assertEqual(source.size,26)
            for filename in ('../private','/etc/shadow','.env','nested/source.tar.gz'):
                with self.assertRaises(ValueError):resolver.source(filename,sha)
            with self.assertRaisesRegex(ValueError,'Missing exact'):resolver.source('source.tar.gz','f'*64)
    def test_symlink_and_wrong_foundation_blob_never_supply_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'actual').write_bytes(b'fixture');(root/'source.tar').symlink_to(root/'actual')
            with self.assertRaises(ValueError):r.Resolver([root]).source('source.tar',hashlib.sha256(b'fixture').hexdigest())
            with self.assertRaisesRegex(ValueError,'foundation'):r.Resolver([],root/'actual')
    def test_source_tars_are_byte_deterministic_bounded_and_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);first=root/'first';second=root/'second';first.mkdir();second.mkdir()
            data=b'unqualified fixture';item=r.Input('upstream/'+hashlib.sha256(data).hexdigest()+'/source.tar',hashlib.sha256(data).hexdigest(),data=data,origin={'kind':'unqualified-source-fixture'})
            a=r.bundles({item.name:item},first);b=r.bundles({item.name:item},second)
            self.assertEqual(a,b)
            with tarfile.open(first/a[0]['name']) as archive:
                members=archive.getmembers();self.assertEqual(len(members),1);row=members[0]
                self.assertEqual((row.uid,row.gid,row.mode,row.mtime),(0,0,0o644,0))
                self.assertEqual(archive.extractfile(row).read(),data)
    def test_changed_cache_during_copy_preserves_failure_not_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'source.tar';path.write_bytes(b'original')
            item=r.Input('source.tar',hashlib.sha256(b'original').hexdigest(),path=path)
            path.write_bytes(b'changed!')
            with self.assertRaisesRegex(ValueError,'changed during'):r.bundles({item.name:item},root)
            self.assertFalse((root/'source-inventory.json').exists())
    def test_actual_git_snapshot_and_historical_input_use_exact_committed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);subprocess.run(['git','init','-q',str(root)],check=True)
            def git(*args):return subprocess.check_output(['git',*args],cwd=root).decode().strip()
            git('config','user.name','Unqualified fixture');git('config','user.email','fixture@example.invalid')
            path=root/'runtime/example.py';path.parent.mkdir();path.write_bytes(b'old fixture source')
            git('add','.');git('commit','-qm','Unqualified source fixture old');old=git('rev-parse','HEAD')
            path.write_bytes(b'new fixture source');git('commit','-qam','Unqualified source fixture new');current=git('rev-parse','HEAD')
            project=r.Project(root,current);item=project.source('runtime/example.py',hashlib.sha256(b'old fixture source').hexdigest())
            self.assertEqual(item.origin['commit'],old)
            # Other absent allowlist paths require snapshot to select existing roots only.
            snapshot=root/'snapshot.tar';project.snapshot(snapshot)
            with tarfile.open(snapshot) as archive:
                self.assertEqual(archive.extractfile('toddy-project/runtime/example.py').read(),b'new fixture source')
            with self.assertRaisesRegex(ValueError,'Missing exact'):project.source('runtime/example.py','f'*64)
    def test_publication_readback_requires_complete_source_members_and_real_git_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);repository=root/'repo';repository.mkdir()
            subprocess.run(['git','init','-q',str(repository)],check=True)
            def git(*args):return subprocess.check_output(['git',*args],cwd=repository).decode().strip()
            git('config','user.name','Unqualified fixture');git('config','user.email','fixture@example.invalid')
            (repository/'runtime').mkdir();(repository/'runtime/example.py').write_text('Unqualified fixture source')
            git('add','.');git('commit','-qm','Unqualified source fixture');commit=git('rev-parse','HEAD')
            output=root/'output';output.mkdir()
            entries={}
            for name,data in [('upstream/source.tar',b'fixture source'),('package-documents/fixture/copyright',b'fixture notice')]:
                item=r.Input(name,hashlib.sha256(data).hexdigest(),data=data);entries[name]=item
            source_assets=r.bundles(entries,output)
            license_assets=r.bundles({name:item for name,item in entries.items() if name.startswith('package-documents/')},output,'source-licenses')
            project=r.Project(repository,commit);snapshot=output/'project.tar';project.snapshot(snapshot)
            project_asset={'name':snapshot.name,'sha256':r.p.digest(snapshot),'bytes':snapshot.stat().st_size}
            package={'name':'fixture','version':'1','architecture':'all','archive_sha256':'a'*64,'component_record_sha256':'b'*64,'recipe_sha256':'c'*64}
            inventory={'version':1,'kind':'native-package-corresponding-sources','producer_sha256':r.p.digest(r.__file__),'source_commit':commit,'archive_export_sha256':'d'*64,'source_urls_are_additional_only':True,'private_cache_copied':False,'signed':False,'published':False,'members':[item.description() for item in entries.values()],'packages':[dict(package,source_members=list(entries))],'source_assets':source_assets,'license_assets':license_assets,'project_source':project_asset}
            path=output/'source-inventory.json';path.write_bytes(r.p.encoded(inventory))
            artifacts=[dict(item,role=role,path=str(output/item['name'])) for role,items in [('source',source_assets),('licenses',license_assets),('project-source',[project_asset])] for item in items]
            pins={'archive_export_sha256':'d'*64,'packages':[package]}
            with patch.object(r,'ROOT',repository):
                r.verify_assets(path,artifacts,pins,commit)
                inventory['packages'][0]['source_members'].pop();path.write_bytes(r.p.encoded(inventory))
                with self.assertRaisesRegex(ValueError,'must be covered'):r.verify_assets(path,artifacts,pins,commit)
    def test_large_sources_are_split_into_bounded_deterministic_flat_assets(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(r,'MAX_ASSET',20000):
            entries={str(index)+'.tar':r.Input(str(index)+'.tar',hashlib.sha256(bytes([index])*8000).hexdigest(),data=bytes([index])*8000) for index in (1,2)}
            assets=r.bundles(entries,Path(directory))
            self.assertEqual(len(assets),2)
            self.assertTrue(all(asset['bytes']<=20000 and '/' not in asset['name'] for asset in assets))
    def test_private_and_untracked_names_are_refused_before_git_source_read(self):
        for path in ('.local/signer/private.key','config/.env.local','runtime/node_modules/token','config/.gnupg/key'):
            with self.assertRaises(ValueError):r.relative(path)
