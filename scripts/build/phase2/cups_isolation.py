"""Add only public loopback names to the exact CUPS private build profile."""
from pathlib import Path
import hashlib,subprocess,sys

# Previous aa78a5f3 baseline differs only by the inactive-for-CUPS Firefox tools branch.
BASE_SHA='5c0e75e5774d54ae734c3a9587dc511431c0357a1ce47e62b01a18a223039410'

def profile(source):
 assert hashlib.sha256(source).hexdigest()==BASE_SHA
 text=source.decode();marker=r'''printf '127.0.0.1 localhost\n::1 localhost\n' > "$root/etc/hosts"'''
 assert text.count(marker)==1
 extra='''
# Private public-name fixture only; no target /etc or external DNS/network access.
[[ "$TODDY_INPUT" == /mnt/lfs/sources/phase2/inputs/cups-2.4.19 ]]
printf '127.0.0.1 localhost toddy-builder\n::1 localhost toddy-builder\n' > "$root/etc/hosts"
chmod 644 "$root/etc/hosts"
'''
 return text.replace(marker,marker+'\n'+extra)

if __name__=='__main__':
 assert sys.argv[1]=='/mnt/lfs/sources/phase2/inputs/cups-2.4.19'
 path=Path('/opt/toddy-build/scripts/build/phase2/isolated.sh')
 result=subprocess.run(['bash','-s','--',*sys.argv[1:]],input=profile(path.read_bytes()).encode())
 raise SystemExit(result.returncode)
