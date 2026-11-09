"""Generate real C/C++ bindings, call native Rust ABI, and refuse malformed input."""
import json
from pathlib import Path
import subprocess
import sys


def main():
    binary,directory=sys.argv[1:];root=Path(directory);root.mkdir()
    source=root/'fixture.rs'
    source.write_text('''#[repr(C)]
pub struct ToddyPoint { pub x: i32, pub y: i32 }
#[no_mangle]
pub extern "C" fn toddy_sum(point: ToddyPoint) -> i32 { point.x + point.y }
''')
    assert subprocess.check_output([binary,'--version'],text=True).strip()=='cbindgen 0.29.4'
    subprocess.run(['rustc','--edition','2021','--crate-type','cdylib','-O',str(source),'-o',str(root/'libtoddyffi.so')],check=True)
    outcomes=[]
    for language,compiler,suffix in [('c','cc','c'),('c++','c++','cc')]:
        header=root/('binding-'+suffix+'.h')
        subprocess.run([binary,'--lang',language,'--output',str(header),str(source)],check=True)
        text=header.read_text();assert 'ToddyPoint' in text and 'toddy_sum' in text
        consumer=root/('consumer.'+suffix)
        if language=='c':body='ToddyPoint p = {20, 22};'
        else:body='ToddyPoint p{20, 22};'
        consumer.write_text('#include "'+header.name+'"\nint main(void) { '+body+' return toddy_sum(p)==42 ? 0 : 1; }\n')
        executable=root/('native-'+suffix)
        subprocess.run([compiler,'-Wall','-Wextra','-Werror',str(consumer),'-L'+str(root),'-Wl,-rpath,'+str(root),'-ltoddyffi','-o',str(executable)],check=True)
        subprocess.run([str(executable)],check=True);outcomes.append({'language':language,'generate_exit':0,'compile_exit':0,'native_abi_exit':0})
    malformed=root/'invalid.rs';malformed.write_text('pub struct Invalid {')
    refused=subprocess.run([binary,'--lang','c','--output',str(root/'invalid.h'),str(malformed)],capture_output=True,text=True)
    assert refused.returncode!=0 and not (root/'invalid.h').exists() and refused.stderr
    (root/'result.json').write_text(json.dumps({'scope':'Native C/C++ generated header and Rust shared ABI42 plus malformed Rust refusal; not macro expansion/Cython/desktop acceptance','outcomes':outcomes,'malformed_exit':refused.returncode},indent=2)+'\n')

if __name__=='__main__':main()
