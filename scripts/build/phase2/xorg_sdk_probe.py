"""Headless native consumers; synthetic protocol fixtures, never a display claim."""
import json
import os
from pathlib import Path
import subprocess
import sys

C_SOURCE = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <X11/Xlib.h>
#include <X11/Xresource.h>
#include <X11/Xauth.h>
#include <X11/Xdmcp.h>
#include <xcb/xcb.h>
int main(void) {
    XrmInitialize();
    assert(XStringToKeysym("Return") == 0xff0d);
    assert(strcmp(XKeysymToString(0xff0d), "Return") == 0);
    XrmDatabase db = XrmGetStringDatabase("toddy.color: navy\n");
    assert(db);
    char *type = NULL; XrmValue value;
    assert(XrmGetResource(db,"toddy.color","Toddy.Color",&type,&value));
    assert(strcmp(value.addr,"navy") == 0); XrmDestroyDatabase(db);
    FILE *file = tmpfile(); assert(file);
    Xauth fixture = {.family=FamilyLocal, .address_length=5, .address="toddy",
        .number_length=1, .number="7", .name_length=7, .name="fixture",
        .data_length=9, .data="synthetic"};
    assert(XauWriteAuth(file,&fixture)); rewind(file);
    Xauth *read = XauReadAuth(file); assert(read);
    assert(read->family == FamilyLocal && read->data_length == 9);
    assert(memcmp(read->data,"synthetic",9) == 0);
    XauDisposeAuth(read); fclose(file);
    ARRAY8 bytes = {0}; assert(XdmcpAllocARRAY8(&bytes,7));
    assert(bytes.length==7 && bytes.data); memset(bytes.data,42,7);
    XdmcpDisposeARRAY8(&bytes);
    char *host=NULL; int display=-1, screen=-1;
    assert(xcb_parse_display(":7.1",&host,&display,&screen));
    assert(display==7 && screen==1); free(host);
    puts("keysym resource synthetic-auth allocation display-parser: OK");
    return 0;
}
'''

KEYMAP = '''xkb_keymap {
xkb_keycodes { minimum=8; maximum=255; <AC01>=38; };
xkb_types { type "ONE_LEVEL" { modifiers=None; map[None]=Level1; level_name[Level1]="Any"; }; };
xkb_compatibility { interpret Any+AnyOf(all) { action=NoAction(); }; };
xkb_symbols { key <AC01> { type="ONE_LEVEL", [ a ] }; };
};
'''


def main():
    prefix, destination = sys.argv[1:3]
    root = Path(destination); root.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               PKG_CONFIG_PATH=prefix+'/lib/pkgconfig:'+prefix+'/share/pkgconfig',
               LD_LIBRARY_PATH=prefix+'/lib')
    source=root/'consumer.c'; source.write_text(C_SOURCE)
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','x11','xau','xdmcp','xcb'],env=env,text=True).split()
    command=['cc','-Wall','-Wextra','-Werror',str(source),'-I'+prefix+'/include',
             '-L'+prefix+'/lib','-Wl,-rpath-link,'+prefix+'/lib',*flags,'-o',str(root/'consumer')]
    compiler_only = sys.argv[3:] == ['--compiler-only']
    if not compiler_only:
        subprocess.run(command,env=env,check=True)
        subprocess.run([str(root/'consumer')],env=env,check=True)
    executable=prefix+'/bin/xkbcomp'
    version=subprocess.run([executable,'-version'],env=env,text=True,capture_output=True,check=True)
    assert '1.5.0' in version.stdout+version.stderr
    checks=[]
    for label,body,expected in [('valid',KEYMAP,0),('invalid','not a keyboard map',1)]:
        command=[executable,'-w0','-xkb','-','-']
        result=subprocess.run(command,input=body,text=True,capture_output=True,env=env)
        (root/(label+'.stdout')).write_text(result.stdout)
        (root/(label+'.stderr')).write_text(result.stderr)
        assert result.returncode==expected,(label,result.returncode,result.stderr)
        if label=='valid':
            assert 'xkb_keymap' in result.stdout and 'AC01' in result.stdout
        checks.append({'name':label,'actual_exit':result.returncode,'expected_exit':expected})
    result={'uid':os.getuid(),'scope':'Headless protocol APIs and real xkbcomp positive/negative compilation; synthetic auth, no display or login',
            'c_api_exit':None if compiler_only else 0,'xkbcomp_version':'1.5.0','xkbcomp':checks}
    (root/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
