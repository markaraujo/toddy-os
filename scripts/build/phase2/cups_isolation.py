"""Add only public loopback names to the exact CUPS private build profile."""
from pathlib import Path
import hashlib,subprocess,sys

# Exact reviewed base: browser tools active only for paired original/security candidate paths.
BASE_SHA='84aa98d4500de7309aa4737c560aebcfe598dc962fcf79057c9e94a1aae99c0b'

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
