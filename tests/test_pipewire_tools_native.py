"""Source/archive/stage fixtures only; no native build, upgrade or audio claim."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('pipewire_tools_native',ROOT/'scripts/build/phase2/pipewire_tools_native.py')
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)


def entries(root):
    result={}
    for path in root.rglob('*'):
        st=path.lstat();row={'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid}
        if path.is_symlink():row['symlink']=os.readlink(path)
        elif path.is_dir():row['directory']=True
        else:row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        result['/'+path.relative_to(root).as_posix()]=row
    return result


class PipewireToolTests(unittest.TestCase):
    def test_single_tag_patch_retains_all_upstream_target_and_alias_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);file=root/'src/tools/meson.build';file.parent.mkdir(parents=True)
            before=b"  pwcat_aliases = [\n"+b''.join(b"    '"+alias.encode()+b"',\n" for alias in p.ALIASES)+b"  ]\n  pw_cat = executable('pw-cat',\n    pwcat_sources,\n    install: true,\n    dependencies : [pwcat_deps, pipewire_dep, mathlib],\n  )\n"
            file.write_bytes(before);proof=p.patch_tag(root)
            after=file.read_bytes();self.assertEqual(after.replace(b"    install_tag: 'toddy-pw-cat',\n",b''),before)
            self.assertEqual(proof['before_sha256'],hashlib.sha256(before).hexdigest())
            with self.assertRaises(ValueError):p.patch_tag(root)
            file.write_bytes(before.replace(b'pw-midi2play',b'unknown-tool'))
            with self.assertRaisesRegex(ValueError,'upstream_aliases'):p.patch_tag(root)

    def test_old_payload_bytes_modes_and_links_cannot_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);binary=root/'usr/bin/pipewire';binary.parent.mkdir(parents=True);binary.write_bytes(b'old native fixture');binary.chmod(0o755)
            link=binary.with_name('old-link');link.symlink_to('pipewire');old=entries(root)
            p.verify_old(root,old,exclusive=True)
            binary.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'old_bytes'):p.verify_old(root,old)
            binary.write_bytes(b'old native fixture');binary.chmod(0o700)
            with self.assertRaisesRegex(ValueError,'metadata_changed'):p.verify_old(root,old)
            binary.chmod(0o755);link.unlink();link.symlink_to('missing')
            with self.assertRaisesRegex(ValueError,'old_link'):p.verify_old(root,old)

    def test_only_native_tool_and_exact_upstream_aliases_may_enter_new_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);binary=root/'usr/bin/pw-cat';binary.parent.mkdir(parents=True);binary.write_bytes(b'explicit synthetic ELF fixture');binary.chmod(0o755)
            for alias in p.ALIASES:binary.with_name(alias).symlink_to('pw-cat')
            self.assertEqual(len(p.tool_stage(root)['entries']),len(p.ALIASES)+3)
            extra=root/'usr/lib';extra.mkdir();(extra/'libpipewire.so').write_bytes(b'unselected rebuilt library')
            with self.assertRaisesRegex(ValueError,'unselected_native_stage'):p.tool_stage(root)

    def test_merged_stage_rejects_unreviewed_additions_and_preserves_copyright(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);directory=root/'usr/share/doc/pipewire';directory.mkdir(parents=True);(directory/'copyright').write_bytes(b'exact old notices')
            bin=root/'usr/bin';bin.mkdir();(bin/'pipewire').write_bytes(b'old fixture');old=entries(root)
            (bin/'pw-cat').write_bytes(b'new fixture')
            for alias in p.ALIASES:(bin/alias).symlink_to('pw-cat')
            (directory/'pw-cat-upgrade-source.json').write_text('{}')
            p.verify_additions(root,old);(directory/'copyright').write_bytes(b'new notices')
            with self.assertRaisesRegex(ValueError,'old_bytes_changed'):p.verify_additions(root,old)
            (directory/'copyright').write_bytes(b'exact old notices');(bin/'unreviewed').write_bytes(b'extra')
            with self.assertRaisesRegex(ValueError,'unselected_merged_stage'):p.verify_additions(root,old)

    def test_source_archive_rejects_escapes_devices_and_duplicate_members(self):
        file=tarfile.TarInfo('pipewire-1.6.8/src/tools/pw-cat.c');file.size=10
        self.assertEqual(p.source_members([file]),10)
        for name in ('/absolute','pipewire-1.6.8/../escape','other/tree'):
            with self.assertRaises(ValueError):p.source_members([tarfile.TarInfo(name)])
        with self.assertRaises(ValueError):p.source_members([file,file])
        device=tarfile.TarInfo('pipewire-1.6.8/device');device.type=tarfile.CHRTYPE
        with self.assertRaises(ValueError):p.source_members([device])

    def test_archive_control_refuses_scripts_and_uses_actual_member_sizes(self):
        def tar(rows):
            stream=io.BytesIO()
            with tarfile.open(fileobj=stream,mode='w') as archive:
                for name,data in rows:
                    info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
            return stream.getvalue()
        control=tar([('control',b'Package: pipewire\n'),('md5sums',b'fixture\n')]);data=tar([('./usr/bin/pipewire',b'actual bytes')])
        with patch.object(p.subprocess,'check_output',side_effect=[control,data]):
            self.assertEqual(p.archive_summary(Path('/fixture/old.deb')),{'regular_bytes':12,'entries':1})
        with patch.object(p.subprocess,'check_output',return_value=tar([('control',b'fixture'),('postinst',b'no execution')])):
            with self.assertRaisesRegex(ValueError,'unreviewed_control_script'):p.archive_summary(Path('/fixture/old.deb'))

    def test_build_is_narrow_ro_native_target_and_help_only(self):
        recipe=(ROOT/p.BUILD).read_text()
        self.assertIn('-Dpw-cat=enabled -Dsndfile=enabled -Dpw-cat-ffmpeg=disabled',recipe)
        self.assertIn('ninja -C /build/compile -j4 src/tools/pw-cat',recipe)
        self.assertIn('--no-rebuild --tags toddy-pw-cat',recipe)
        self.assertNotIn('ninja -C /build/compile -j4 >',recipe)
        self.assertNotIn('pipewire --',recipe)
        for name in ('pipewire_tools_build.sh','pipewire_tools_prepare.sh','pipewire_tools_install.sh','pipewire_tools_check.sh'):
            subprocess.run(['/bin/bash','-n',str(ROOT/'scripts/build/phase2'/name)],check=True)
        self.assertEqual(p.VERSION,'1.6.8-1+toddy2');self.assertIn('libsndfile (= 1.2.2-1+toddy1)',p.DEPENDS)
        self.assertEqual(p.PROVIDERS['pipewire'],p.OLD)

    def test_fake_or_rpath_ELF_fails_before_native_provider_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            file=Path(temporary)/'pw-cat';file.write_bytes(b'not ELF')
            with patch.object(p.subprocess,'check_output') as native:
                with self.assertRaisesRegex(ValueError,'native_x86_64_ELF'):p.elf_dependencies(file)
                native.assert_not_called()
            file.write_bytes(b'\x7fELF\x02\x01'+b'\0'*12+b'\x3e\0')
            with patch.object(p.subprocess,'check_output',return_value=' (RUNPATH) Library runpath: [/build/compile]'):
                with self.assertRaisesRegex(ValueError,'RPATH'):p.elf_dependencies(file)

if __name__=='__main__':unittest.main()
