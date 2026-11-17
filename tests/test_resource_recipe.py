"""Candidate attribution/closed recipe fixtures; never run a native generator."""
import hashlib
import importlib.util
from pathlib import Path
import stat
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('resource_recipe',ROOT/'scripts/build/phase2/resource_recipe.py')
recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)
from runtime.installer.native_finalizer import payload_module


class ResourceRecipeTests(unittest.TestCase):
    def manifest(self):
        return {'ownership':{'entries':{'/usr/share/owned':{'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':'a'*64}},
                    'fresh_directories':{'home':{'mode':stat.S_IFDIR|0o755,'uid':0,'gid':0,'directory':True}}},
                'components':[{'name':'fixture'}]}
    def policy(self):
        return {'accounts':{'passwd':'root:x:0:0:root:/root:/bin/bash\n','group':'root:x:0:\nwheel:x:97:\n'}}
    def test_runtime_allows_only_exact_declared_empty_directory_closure(self):
        directory=lambda mode=0o755,uid=0,gid=0:{'mode':stat.S_IFDIR|mode,'uid':uid,'gid':gid,'directory':True}
        actual={'/run':directory(),'/run/cups':directory(),'/run/cups/certs':directory(0o511,9,19),'/run/dbus':directory(),'/run/krb5kdc':directory()}
        manifest=self.manifest();manifest['ownership']['entries'].update(actual)
        recipe.empty_declared_runtime(actual,manifest)
        manifest['ownership']['fresh_directories']['run']=manifest['ownership']['entries'].pop('/run')
        recipe.empty_declared_runtime(actual,manifest)
        for path,row in (('/run/cups/certs/key',{'mode':stat.S_IFREG|0o600,'uid':9,'gid':19,'sha256':'a'*64}),('/run/socket',{'mode':stat.S_IFLNK|0o777,'uid':0,'gid':0,'symlink':'/tmp/socket'}),('/run/unknown',directory())):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):recipe.empty_declared_runtime(dict(actual,**{path:row}),manifest)
        changed={**actual,'/run/cups/certs':directory(0o755,9,19)}
        with self.assertRaises(ValueError):recipe.empty_declared_runtime(changed,manifest)
        changed={**actual,'/run/cups/certs':directory(0o511,0,0)}
        with self.assertRaises(ValueError):recipe.empty_declared_runtime(changed,manifest)
        missing=dict(actual);del missing['/run/cups']
        with self.assertRaises(ValueError):recipe.empty_declared_runtime(missing,manifest)

    def test_directory_recovery_rejects_any_prior_account_cache_or_tool_effect(self):
        manifest=self.manifest();before={**manifest['ownership']['entries'],
            '/home':manifest['ownership']['fresh_directories']['home']}
        recipe.recovery_directory_baseline(before,manifest,self.policy())
        for extra in ({'/etc/ld.so.cache':{'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':'b'*64}},
                recipe.account_entries(self.policy()),
                {'/root/private':{'mode':stat.S_IFREG|0o600,'uid':0,'gid':0,'sha256':'b'*64}}):
            with self.assertRaises(ValueError):recipe.recovery_directory_baseline({**before,**extra},manifest,self.policy())
        with self.assertRaises(ValueError):recipe.recovery_directory_baseline(manifest['ownership']['entries'],manifest,self.policy())

    def test_account_recovery_requires_all_exact_accounts_links_and_no_cache(self):
        manifest=self.manifest();policy=self.policy()
        before={**manifest['ownership']['entries'],**recipe.account_entries(policy),
            '/home':manifest['ownership']['fresh_directories']['home'],
            **{path:{'mode':stat.S_IFLNK|0o777,'uid':0,'gid':0,'symlink':target} for path,target in recipe.LINKS.items()}}
        recipe.recovery_directory_baseline(before,manifest,policy,accounts=True)
        for path in recipe.account_entries(policy):
            changed=dict(before);changed[path]={**changed[path],'sha256':'f'*64}
            with self.assertRaises(ValueError):recipe.recovery_directory_baseline(changed,manifest,policy,accounts=True)
        changed={**before,'/etc/ld.so.cache':{'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':'a'*64}}
        with self.assertRaises(ValueError):recipe.recovery_directory_baseline(changed,manifest,policy,accounts=True)
        changed=dict(before);del changed['/etc/systemd/system/default.target']
        with self.assertRaises(ValueError):recipe.recovery_directory_baseline(changed,manifest,policy,accounts=True)

    def test_unknown_or_changed_owned_file_is_never_generated_override(self):
        manifest=self.manifest();actual={**manifest['ownership']['entries'],'/root/key':{'mode':stat.S_IFREG|0o600,'uid':0,'gid':0,'sha256':'b'*64}}
        actual['/usr/share/owned']={**actual['/usr/share/owned'],'sha256':'c'*64}
        generated,blocked=recipe.candidate_entries(actual,manifest,self.policy())
        self.assertEqual(generated,{})
        self.assertEqual({row['path'] for row in blocked},{'/root/key','/usr/share/owned'})
    def test_literal_fresh_accounts_and_known_database_have_exact_origins(self):
        manifest=self.manifest();actual={**manifest['ownership']['entries'],**recipe.account_entries(self.policy()),
            '/home':manifest['ownership']['fresh_directories']['home'],
            '/var/lib/dpkg/info/fixture.list':{'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':'b'*64},
            '/lost+found':{'mode':stat.S_IFDIR|0o700,'uid':0,'gid':0,'directory':True}}
        generated,blocked=recipe.candidate_entries(actual,manifest,self.policy())
        self.assertEqual(blocked,[])
        self.assertEqual(generated['/etc/shadow']['origin'],'fresh-system-accounts')
        self.assertEqual(generated['/var/lib/dpkg/info/fixture.list']['origin'],'native-dpkg-database')
        self.assertEqual(generated['/lost+found']['origin'],'fresh-filesystem')
    def test_native_dpkg_info_format_requires_exact_frozen_bytes_and_metadata(self):
        path='/var/lib/dpkg/info/format';row={'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':hashlib.sha256(b'1\n').hexdigest()}
        self.assertEqual(row['sha256'],recipe.DB_INFO_FORMAT_SHA)
        generated,blocked=recipe.candidate_entries({path:row},self.manifest(),self.policy())
        self.assertEqual(generated[path]['origin'],'native-dpkg-database')
        self.assertFalse(any(item['path']==path for item in blocked))
        for changed in ({**row,'sha256':hashlib.sha256(b'2\n').hexdigest()},{**row,'mode':stat.S_IFREG|0o600},{**row,'uid':9},{'mode':stat.S_IFLNK|0o777,'uid':0,'gid':0,'symlink':'other'}):
            with self.subTest(row=changed):
                generated,blocked=recipe.candidate_entries({path:changed},self.manifest(),self.policy())
                self.assertNotIn(path,generated);self.assertTrue(any(item['path']==path for item in blocked))

    def test_other_package_database_script_cannot_gain_provenance(self):
        manifest=self.manifest();actual={**manifest['ownership']['entries'],
            '/var/lib/dpkg/info/fixture.postinst':{'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':'b'*64}}
        generated,blocked=recipe.candidate_entries(actual,manifest,self.policy())
        self.assertFalse(generated);self.assertEqual(len(blocked),1)
    def test_closed_plan_pins_complete_namespace_and_fixed_native_argv(self):
        p=payload_module();entries={'/usr/share/glib-2.0/schemas/fixture.xml':{'sha256':'a'*64},
            '/usr/share/glib-2.0/schemas/gschemas.compiled':{'sha256':'b'*64},'/usr/bin/glib-compile-schemas':{'sha256':'c'*64}}
        output='/usr/share/glib-2.0/schemas/gschemas.compiled';namespace=p.cache_namespace(output,entries)
        binding={'output_sha256':'b'*64,'tool':{'path':'/usr/bin/glib-compile-schemas','sha256':'c'*64},
            'input_namespace_sha256':hashlib.sha256(p.encoded(namespace)).hexdigest(),'inputs':{'/usr/share/glib-2.0/schemas/fixture.xml':'a'*64}}
        manifest={'ownership':{'entries':entries},'generated':{'owned_cache_bindings':{output:binding}}}
        self.assertEqual(recipe.resource_plan(manifest)[0]['argv'],['/usr/bin/glib-compile-schemas','--strict','/usr/share/glib-2.0/schemas'])
        entries['/usr/share/glib-2.0/schemas/new.xml']={'sha256':'d'*64}
        with self.assertRaisesRegex(ValueError,'union'):recipe.resource_plan(manifest)
