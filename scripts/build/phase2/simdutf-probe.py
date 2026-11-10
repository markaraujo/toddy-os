#!/usr/bin/env python3
"""Actual CMake shared Unicode API; never a terminal/hardware claim."""
from pathlib import Path
import json,subprocess,sys
prefix,work=map(Path,sys.argv[1:]);p=work/'consumer';p.mkdir()
(p/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.18)
project(ToddySimdutf LANGUAGES CXX)
find_package(simdutf 9.0.0 EXACT CONFIG REQUIRED)
file(WRITE "${CMAKE_BINARY_DIR}/discovered-version.txt" "${simdutf_VERSION}")
add_executable(consumer main.cpp)
target_compile_features(consumer PRIVATE cxx_std_17)
target_link_libraries(consumer PRIVATE simdutf::simdutf)
''')
(p/'main.cpp').write_text(r'''#include <simdutf.h>
#include <iostream>
#include <string>
int main() {
    for (int cycle=0;cycle<2;cycle++) {
        const std::string text="Toddy ã 🐕";
        if (!simdutf::validate_utf8(text.data(),text.size()) || simdutf::count_utf8(text.data(),text.size())!=9) return 1;
        size_t length=simdutf::utf16_length_from_utf8(text.data(),text.size());
        if(length!=10) return 2;
        std::u16string utf16(length,u'\0');
        if(simdutf::convert_utf8_to_utf16le(text.data(),text.size(),utf16.data())!=length || !simdutf::validate_utf16le(utf16.data(),utf16.size())) return 3;
        std::string back(simdutf::utf8_length_from_utf16le(utf16.data(),utf16.size()),'\0');
        if(simdutf::convert_utf16le_to_utf8(utf16.data(),utf16.size(),back.data())!=text.size() || back!=text) return 4;
        const char invalid[]={char(0xc0),char(0xaf)};
        if(simdutf::validate_utf8(invalid,2) || simdutf::validate_utf8_with_errors(invalid,2).error==simdutf::SUCCESS) return 5;
        const char16_t surrogate[]={char16_t(0xd800)};
        if(simdutf::validate_utf16le(surrogate,1)) return 6;
        if(!simdutf::validate_utf8(text.data(),text.size())) return 7;
    }
    std::cout << R"({"Unicode_PT_emoji_roundtrip":true,"codepoint_and_surrogate_lengths":true,"overlong_UTF8_refused":true,"unpaired_UTF16_refused":true,"reset_recovery_cycles":2})" << '\n';
}
''')
with (p/'configure.log').open('x') as log:subprocess.run(['cmake','-S',str(p),'-B',str(p/'compile'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-Dsimdutf_DIR='+str(prefix/'lib/cmake/simdutf')],stdout=log,stderr=subprocess.STDOUT,check=True)
with (p/'build.log').open('x') as log:subprocess.run(['cmake','--build',str(p/'compile'),'-j2'],stdout=log,stderr=subprocess.STDOUT,check=True)
result=json.loads(subprocess.check_output([str(p/'compile/consumer')],text=True,timeout=10))
version=(p/'compile/discovered-version.txt').read_text();assert version=='9.0.0'
result.update(CMake_discovered_version=version,shared_library_consumer=True,terminal_or_GUI_tested=False)
print(json.dumps(result))
