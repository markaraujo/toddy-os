#!/usr/bin/env python3
"""Actual CMake-discovered staged/installed header SDK consumer."""
from pathlib import Path
import json,subprocess,sys
prefix,work=map(Path,sys.argv[1:]);p=work/'consumer';p.mkdir()
(p/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.14)
project(ToddyFastFloat LANGUAGES CXX)
find_package(FastFloat 8.2.10 EXACT CONFIG REQUIRED)
file(WRITE "${CMAKE_BINARY_DIR}/discovered-version.txt" "${FastFloat_VERSION}")
add_executable(consumer main.cpp)
target_compile_features(consumer PRIVATE cxx_std_17)
target_link_libraries(consumer PRIVATE FastFloat::fast_float)
''')
(p/'main.cpp').write_text(r'''#include <fast_float/fast_float.h>
#include <cmath>
#include <cstring>
#include <iostream>
#include <string>
#include <system_error>
int main() {
    for (int cycle=0;cycle<2;cycle++) {
        std::string text="-12.5e2tail";double value=0;
        auto r=fast_float::from_chars(text.data(),text.data()+text.size(),value);
        if (r.ec!=std::errc() || r.ptr!=text.data()+7 || value!=-1250) return 1;
        text="0.5";float single=0;
        auto f=fast_float::from_chars(text.data(),text.data()+text.size(),single);
        if(f.ec!=std::errc() || f.ptr!=text.data()+text.size() || single!=0.5f) return 2;
        text="invalid";value=42;
        r=fast_float::from_chars(text.data(),text.data()+text.size(),value);
        if(r.ec!=std::errc::invalid_argument || r.ptr!=text.data() || value!=42) return 3;
        text="1e99999";
        r=fast_float::from_chars(text.data(),text.data()+text.size(),value);
        if(r.ec!=std::errc::result_out_of_range) return 4;
        text="42";
        r=fast_float::from_chars(text.data(),text.data()+text.size(),value);
        if(r.ec!=std::errc() || r.ptr!=text.data()+text.size() || value!=42) return 5;
    }
    std::cout << R"({"typed_float_double":true,"trailing_input_pointer":true,"invalid_input_refused":true,"overflow_refused":true,"reset_recovery_cycles":2})" << '\n';
}
''')
with (p/'configure.log').open('x') as log:
 subprocess.run(['cmake','-S',str(p),'-B',str(p/'compile'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DFastFloat_DIR='+str(prefix/'share/cmake/FastFloat')],stdout=log,stderr=subprocess.STDOUT,check=True)
with (p/'build.log').open('x') as log:subprocess.run(['cmake','--build',str(p/'compile'),'-j2'],stdout=log,stderr=subprocess.STDOUT,check=True)
result=json.loads(subprocess.check_output([str(p/'compile/consumer')],text=True,timeout=10))
version=(p/'compile/discovered-version.txt').read_text();assert version=='8.2.10'
result.update(CMake_discovered_version=version,header_only_SDK=True,terminal_or_GUI_tested=False)
print(json.dumps(result))
