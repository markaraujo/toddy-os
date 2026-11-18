"""Exact selected cache bytes may be kept without a native rewrite."""
import hashlib
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from runtime.installer.disk_plan import InstallError
from runtime.installer.native_finalizer import packaged_cache_profile,preserve_packaged_cache


class PackagedCachePreservationTests(unittest.TestCase):
    def test_only_fixed_selected_families(self):
        self.assertTrue(packaged_cache_profile('/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache','/usr/bin/gdk-pixbuf-query-loaders'))
        self.assertTrue(packaged_cache_profile('/usr/lib/gtk-3.0/3.0.0/immodules.cache','/usr/bin/gtk-query-immodules-3.0'))
        self.assertTrue(packaged_cache_profile('/usr/lib/modules/7.1.8-toddy/modules.dep','/usr/bin/kmod'))
        self.assertTrue(packaged_cache_profile('/usr/lib/udev/hwdb.bin','/usr/bin/systemd-hwdb'))
        self.assertTrue(packaged_cache_profile('/usr/share/icons/hicolor/icon-theme.cache','/usr/bin/gtk4-update-icon-cache'))
        self.assertTrue(packaged_cache_profile('/usr/share/mime/mime.cache','/usr/bin/update-mime-database'))
        self.assertTrue(packaged_cache_profile('/usr/share/icons/Adwaita/icon-theme.cache','/usr/bin/gtk4-update-icon-cache'))
        self.assertFalse(packaged_cache_profile('/usr/lib/modules/7.1.8-toddy/modules.dep','/usr/bin/other'))
        self.assertFalse(packaged_cache_profile('/usr/share/mime/mime.cache','/usr/bin/other'))

    def test_exact_owned_output_is_required_before_preservation(self):
        virtual='/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache';data=b'selected package cache\n'
        sha=hashlib.sha256(data).hexdigest()
        binding={'tool':{'path':'/usr/bin/gdk-pixbuf-query-loaders'},'output_sha256':sha}
        entries={virtual:{'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'sha256':sha}}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/virtual.lstrip('/');path.parent.mkdir(parents=True)
            path.write_bytes(data);path.chmod(0o644)
            original=Path.lstat
            def root_owned(current):
                info=original(current)
                if current==path:
                    fields=list(info);fields[4]=fields[5]=0
                    return os.stat_result(fields)
                return info
            with patch.object(Path,'lstat',root_owned):
                self.assertTrue(preserve_packaged_cache(root,virtual,binding,entries))
                path.write_bytes(b'drift')
                with self.assertRaisesRegex(InstallError,'packaged_cache_changed'):
                    preserve_packaged_cache(root,virtual,binding,entries)
                path.write_bytes(data)
                with self.assertRaisesRegex(InstallError,'contract_changed'):
                    preserve_packaged_cache(root,virtual,binding,{virtual:{**entries[virtual],'mode':stat.S_IFREG|0o600}})
                path.unlink()
                with self.assertRaisesRegex(InstallError,'packaged_cache_missing'):
                    preserve_packaged_cache(root,virtual,binding,entries)


if __name__=='__main__':unittest.main()
