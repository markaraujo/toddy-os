"""Rebase only stale BLFS patch context onto frozen Lua's added ios platform."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(recipe):
    assert os.getuid()==101 and Path('/build/project/src/Makefile.rej').is_file()
    assert not Path('/build/project-2').exists()
    original=Path('/src/toddy-supplemental/lua-5.4.8-shared_library-1.patch').read_bytes()
    old=b' PLATS= guess aix bsd c89 freebsd generic linux linux-readline macosx mingw posix solaris\n'
    new=old.replace(b'generic linux',b'generic ios linux')
    assert original.count(old)==1
    source=Path('/src/src/Makefile').read_bytes()
    assert b'\n'+new[1:] in source
    adjusted=original.replace(old,new)
    patch=Path('/build/lua-shared-context-2.patch');patch.write_bytes(adjusted)
    assert adjusted.replace(new,old)==original
    recipe_path=Path('/build/lua-context-2.sh')
    assert recipe.count('/src/toddy-supplemental/lua-5.4.8-shared_library-1.patch')==1
    recipe_path.write_text(recipe.replace('/build/project','/build/project-2').replace(
        '/src/toddy-supplemental/lua-5.4.8-shared_library-1.patch',str(patch)))
    Path('/build/patch-context-2.json').write_text(json.dumps({
        'scope':'One unchanged context line gains ios to match frozen5.4.8 Makefile; all BLFS patch additions/deletions unchanged',
        'original_sha256':hashlib.sha256(original).hexdigest(),
        'adjusted_sha256':hashlib.sha256(adjusted).hexdigest(),
        'old_context':old.decode(),'new_context':new.decode(),
        'recovery':'Original failed partial project retained; fresh project-2 for first actual compilation, no frozen version change'
    },indent=2)+'\n')
    subprocess.run(['bash',str(recipe_path)],check=True)
