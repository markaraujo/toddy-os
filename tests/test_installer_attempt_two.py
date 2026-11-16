"""Frozen exported-interface configure regression; no native plugin build/VM use."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts/build'),str(ROOT/'scripts/build/phase2')]
import installer_native as native
import installer_package as package


class InstallerAttemptTwoTests(unittest.TestCase):
    def test_attempt_two_preserves_first_compile_namespace_and_frozen_dependencies(self):
        self.assertEqual(native.SOURCE.name,'toddy-installer-0.2.0-2')
        self.assertEqual(native.WORK.name,'toddy-installer-2')
        self.assertEqual(native.STAGE.name,'phase2-toddy-installer-2')
        self.assertEqual(native.PREPARED.name,'toddy-installer-prepared-2.json')
        self.assertEqual(native.JOB,'toddy-installer-build-2')
        self.assertEqual(native.STEP,'b12-toddy-installer-2')
        self.assertEqual(native.VERSION,'0.2.0-1+toddy1')
        for dependency in ('kcoreaddons (= 6.29.0-1+toddy1)','yaml-cpp (= 0.9.0-1+toddy1)','qtsvg (= 6.11.2-1+toddy1)'):
            self.assertIn(dependency,package.DEPENDENCIES)
        self.assertIn('live_session.py',package.INSTALLER_MODULES)
        self.assertIn('generated_resources.py',package.INSTALLER_MODULES)

    @unittest.skipUnless(shutil.which('cmake') and shutil.which('c++'),'Host CMake/C++ configuration fixture unavailable')
    def test_actual_cmake_generation_resolves_exported_kf_target_and_catches_its_omission(self):
        # Synthetic config packages reproduce the observed actual exported link
        # graph. We configure only an empty host fixture; never build a plugin.
        finds=[line for line in (ROOT/'runtime/installer/calamares/CMakeLists.txt').read_text().splitlines() if line.startswith('find_package(')]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);prefix=root/'prefix';prefix.mkdir()
            def config(name,version,text):
                directory=prefix/name;directory.mkdir()
                (directory/(name+'Config.cmake')).write_text(text)
                (directory/(name+'ConfigVersion.cmake')).write_text('set(PACKAGE_VERSION "'+version+'")\nif(PACKAGE_FIND_VERSION VERSION_EQUAL PACKAGE_VERSION)\nset(PACKAGE_VERSION_EXACT TRUE)\nset(PACKAGE_VERSION_COMPATIBLE TRUE)\nendif()\n')
            config('KF6CoreAddons','6.29.0','add_library(KF6::CoreAddons INTERFACE IMPORTED)\n')
            config('Qt6','6.11.2','\n'.join('add_library(Qt6::'+name+' INTERFACE IMPORTED)' for name in ('Core','Network','Gui','Widgets','Svg'))+'\n')
            config('Calamares','3.4.3','''add_library(yamlcpp::yamlcpp INTERFACE IMPORTED)
add_library(Calamares::calamares INTERFACE IMPORTED)
set_property(TARGET Calamares::calamares PROPERTY INTERFACE_LINK_LIBRARIES "yamlcpp::yamlcpp;Qt6::Core;Qt6::Network;KF6::CoreAddons")
add_library(Calamares::calamaresui INTERFACE IMPORTED)
set_property(TARGET Calamares::calamaresui PROPERTY INTERFACE_LINK_LIBRARIES "Calamares::calamares;Qt6::Core;Qt6::Gui;Qt6::Widgets;Qt6::Svg")
''')
            source=root/'source';source.mkdir();(source/'fixture.cpp').write_text('void exported_interface_fixture() {}\n')
            def run(lines,name):
                (source/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(ExportFixture LANGUAGES CXX)\n'+'\n'.join(lines)+'\nadd_library(consumer MODULE fixture.cpp)\ntarget_link_libraries(consumer PRIVATE Calamares::calamares Calamares::calamaresui Qt6::Core Qt6::Widgets)\n')
                return subprocess.run(['cmake','-S',str(source),'-B',str(root/name),'-DCMAKE_PREFIX_PATH='+str(prefix)],capture_output=True,text=True,timeout=60)
            correct=run(finds,'correct')
            self.assertEqual(correct.returncode,0,correct.stdout+correct.stderr)
            missing=run([line for line in finds if 'KF6CoreAddons' not in line],'missing')
            self.assertNotEqual(missing.returncode,0)
            self.assertIn('KF6::CoreAddons',missing.stderr)


if __name__=='__main__':unittest.main()
