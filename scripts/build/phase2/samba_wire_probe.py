from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import sys

subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
logs=Path('/var/log/toddy/phase2')
work=Path('/mnt/lfs/sources/phase2/work/samba-1')
fixture=work/'smb-wire-5'
receipt=logs/'samba-wire-5.json'
part=receipt.with_suffix('.part')
with Path('/var/log/toddy/build/build.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='0933ee87-f0bc-4074-9491-8b4e6892121f'
    assert subprocess.check_output(['findmnt','-n','-o','ID','--mountpoint','/run/toddy-samba-client-1'],text=True).strip()=='580'
    assert all(not os.path.lexists(p) for p in (fixture,receipt,part))
    source=sys.stdin.read()
    state={'state':'planned','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           'inner_sha256':hashlib.sha256(source.encode()).hexdigest(),'fixture':str(fixture),
           'scope':'Dedicated synthetic read-only chroot with only private fixture writable, private mount/PID/network and loopback. Staged source-built Samba; no native install or global service.'}
    def save():
        with part.open('x') as stream:
            stream.write(json.dumps(state,indent=2)+'\n')
            stream.flush();os.fsync(stream.fileno())
        part.replace(receipt)
    save()
    fixture.mkdir(mode=0o755)
    (fixture/'inner.py').write_text(source)
    namespace=r'''
set -euo pipefail
mount --make-rprivate /
ip link set dev lo up
root=$(mktemp -d /run/toddy-smb-wire-root.XXXXXX)
trap 'result=$?; cd /; umount -R --lazy "$root"; rmdir "$root"; exit "$result"' EXIT
mount -t tmpfs -o size=16m,nosuid,nodev tmpfs "$root"
mkdir -p "$root"/{usr,lib64,etc,fixture,stage,candidate,proc,dev,run,tmp,var}
ln -s usr/bin "$root/bin"
ln -s usr/sbin "$root/sbin"
ln -s usr/lib "$root/lib"
ln -s ../run "$root/var/run"

readonly_bind() {
    mount --bind "$1" "$2"
    mount -o remount,bind,ro,nosuid,nodev "$2"
}
readonly_bind /mnt/lfs/usr "$root/usr"
readonly_bind /mnt/lfs/lib64 "$root/lib64"
readonly_bind /mnt/lfs/sources/phase2/work/samba-1/stage-network-1 "$root/stage"
readonly_bind /mnt/lfs/sources/phase2/work/samba-1/stage-client-2 "$root/candidate"
mount --bind /mnt/lfs/sources/phase2/work/samba-1/smb-wire-5 "$root/fixture"
printf 'root:x:0:0:root:/fixture:/bin/false\ntester:x:101:101:fixture:/fixture/client:/bin/false\nnobody:x:65534:65534:guest:/nonexistent:/bin/false\n' > "$root/etc/passwd"
printf 'root:x:0:\ntester:x:101:\nnobody:x:65534:\n' > "$root/etc/group"
printf 'passwd: files\ngroup: files\nhosts: files\n' > "$root/etc/nsswitch.conf"
printf '127.0.0.1 localhost\n::1 localhost\n' > "$root/etc/hosts"
for name in ld.so.cache ld.so.conf; do
 if test -f "/mnt/lfs/etc/$name"; then cp "/mnt/lfs/etc/$name" "$root/etc/$name"; fi
done
mount -t proc -o nosuid,nodev,noexec,ro proc "$root/proc"
for name in null zero random urandom; do
 touch "$root/dev/$name"
 mount --bind "/dev/$name" "$root/dev/$name"
done
mount -t tmpfs -o size=32m,nosuid,nodev,mode=755 tmpfs "$root/run"
mkdir "$root/run/samba"
mount -t tmpfs -o size=16m,nosuid,nodev,mode=1777 tmpfs "$root/tmp"
mount -o remount,ro "$root"
setpriv --no-new-privs --inh-caps=-all --ambient-caps=-all \
 --bounding-set=-all,+chown,+dac_override,+fowner,+setuid,+setgid,+setpcap,+sys_chroot,+sys_resource \
 chroot "$root" /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C.UTF-8 HOME=/fixture \
 /usr/bin/python3 /fixture/inner.py
'''
    state['state']='running';save()
    try:
        with (logs/'samba-wire-5.log').open('xb') as output:
            result=subprocess.run(['unshare','--mount','--net','--pid','--fork','bash','-c',namespace],stdout=output,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        state['exit']=result.returncode
        state['state']='complete' if result.returncode==0 else 'failed'
        with (logs/'samba-wire-5.log').open('rb') as stream:state['log_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
        save()
        (logs/'samba-wire-5.exit').write_text(str(result.returncode)+'\n')
    except BaseException:
        state['state']='interrupted-observation';save();raise
    print(json.dumps(state))
    raise SystemExit(result.returncode)
