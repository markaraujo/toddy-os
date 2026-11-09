"""Compile current owned hwdb sources in a private unprivileged root."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(expected):
    assert os.getuid()==101
    w=Path('/build');root=w/'hwdb-root';root.mkdir();folder=root/'usr/lib/udev/hwdb.d';folder.mkdir(parents=True)
    inputs={p.name:sha(p) for p in Path('/usr/lib/udev/hwdb.d').glob('*.hwdb')};assert inputs==expected
    for name,digest in inputs.items():
        source=Path('/usr/lib/udev/hwdb.d')/name;assert not source.is_symlink();shutil.copyfile(source,folder/name);assert sha(folder/name)==digest
    with (w/'compile.log').open('xb') as log:
        subprocess.run(['systemd-hwdb','--root='+str(root),'--usr','--strict','update'],stdout=log,stderr=subprocess.STDOUT,check=True)
    cache=root/'usr/lib/udev/hwdb.bin';assert cache.is_file() and cache.stat().st_size>1024
    probe=w/'consumer.c';probe.write_text('''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <systemd/sd-hwdb.h>
int main(int argc,char **argv){assert(argc==2);sd_hwdb *db=NULL;const char *value=NULL;assert(sd_hwdb_new_from_path(argv[1],&db)==0);assert(sd_hwdb_get(db,"acpi:GSM:","ID_VENDOR_FROM_DATABASE",&value)==0);assert(strcmp(value,"LG Electronics")==0);assert(sd_hwdb_get(db,"acpi:__TODDY_INVALID_PNP__:","ID_VENDOR_FROM_DATABASE",&value)<0);sd_hwdb_unref(db);puts("native hardware database LG vendor and unknown-ID refusal; no device operation");return 0;}
''')
    subprocess.run(['cc','-Wall','-Wextra','-Werror',str(probe),'-lsystemd','-o',str(w/'consumer')],check=True)
    with (w/'consumer.log').open('xb') as log:subprocess.run([str(w/'consumer'),str(cache)],stdout=log,stderr=subprocess.STDOUT,check=True)
    out=w/'stage/usr/lib/udev';out.mkdir(parents=True);shutil.copyfile(cache,out/'hwdb.bin');(out/'hwdb.bin').chmod(0o644)
    (w/'test-results.json').write_text(json.dumps({'scope':'Actual current owned hardware database source compilation and native lookup/refusal, no hardware acceptance','input_sha256':inputs,'cache_sha256':sha(cache),'native_consumer_exit':0,'compiler':'Accepted same-version systemd-hwdb261.2, no source/library rebuild','profile':'Complete40existing native stock inputs, no host/sysfs/device access or /etc override'},indent=2)+'\n')
