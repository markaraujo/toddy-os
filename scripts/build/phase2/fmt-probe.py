#!/usr/bin/env python3
"""Actual staged/installed CMake shared fmt consumer; no terminal claim."""
from pathlib import Path
import json,subprocess,sys
prefix,work=map(Path,sys.argv[1:]);p=work/'consumer';p.mkdir()
(p/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.14)
project(ToddyFmt LANGUAGES CXX)
find_package(fmt 12.2.0 EXACT CONFIG REQUIRED)
file(WRITE "${CMAKE_BINARY_DIR}/discovered-version.txt" "${fmt_VERSION}")
add_executable(consumer main.cpp)
target_compile_features(consumer PRIVATE cxx_std_17)
target_link_libraries(consumer PRIVATE fmt::fmt)
''')
(p/'main.cpp').write_text(r'''#include <fmt/format.h>
#include <iostream>
#include <string>
int main() {
    if (FMT_VERSION!=120200) return 1;
    for (int cycle=0;cycle<2;cycle++) {
        if (fmt::format("{} {:.2f}", "Toddy ã",12.5)!="Toddy ã 12.50") return 2;
        if (fmt::format("{:04x}",42)!="002a") return 3;
        bool refused=false;
        try { (void)fmt::format(fmt::runtime("{:d}"),"invalid"); }
        catch (const fmt::format_error&) { refused=true; }
        if(!refused || fmt::format("{}",42)!="42") return 4;
    }
    std::cout << R"({"Unicode_decimal_hex":true,"runtime_format_error_refused":true,"reset_recovery_cycles":2})" << '\n';
}
''')
with (p/'configure.log').open('x') as log:subprocess.run(['cmake','-S',str(p),'-B',str(p/'compile'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-Dfmt_DIR='+str(prefix/'lib/cmake/fmt')],stdout=log,stderr=subprocess.STDOUT,check=True)
with (p/'build.log').open('x') as log:subprocess.run(['cmake','--build',str(p/'compile'),'-j2'],stdout=log,stderr=subprocess.STDOUT,check=True)
result=json.loads(subprocess.check_output([str(p/'compile/consumer')],text=True,timeout=10))
version=(p/'compile/discovered-version.txt').read_text();assert version=='12.2.0'
result.update(CMake_discovered_version=version,shared_library_consumer=True,terminal_or_GUI_tested=False)
print(json.dumps(result))
