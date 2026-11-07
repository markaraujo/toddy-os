#!/usr/bin/env python3
"""Stage LFS 13.1-derived base configuration without changing a running system."""
import argparse
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[3]
FILES={
 'etc/os-release': 'NAME="Toddy OS"\nID=toddy\nPRETTY_NAME="Toddy OS (experimental)"\nVERSION="0.1 Experimental"\nVERSION_ID="0.1"\nVARIANT="Experimental"\nVARIANT_ID=experimental\n',
 'etc/hostname': 'toddy\n',
 'etc/hosts': '127.0.0.1 localhost\n127.0.1.1 toddy\n::1 localhost ip6-localhost ip6-loopback\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\n',
 'etc/locale.conf': 'LANG=en_US.UTF-8\n',
 'etc/vconsole.conf': 'KEYMAP=us\nFONT=Lat2-Terminus16\n',
 'etc/shells': '# Available source-built shells through merged-/usr aliases.\n/bin/sh\n/usr/bin/sh\n/bin/bash\n/usr/bin/bash\n/bin/csh\n/usr/bin/csh\n/bin/tcsh\n/usr/bin/tcsh\n',
 'etc/adjtime': '0.0 0 0.0\n0\nUTC\n',
 'etc/fstab': '# Disposable build-target profile; live media and installer provide their own filesystem profile.\nLABEL=TODDY_LFS / ext4 defaults 1 1\n# TODDY_ESP is mounted explicitly during bootloader operations (LFS 10.2).\nLABEL=TODDY_SWAP none swap defaults 0 0\n',
 'etc/systemd/network/10-toddy-dhcp.network': '[Match]\nName=en* eth*\n\n[Network]\nDHCP=ipv4\n\n[DHCPv4]\nUseDomains=true\n',
 'etc/profile': '''# LFS 13.1-systemd section 9.7 computer instructions (MIT).
export PATH=/usr/bin:/usr/sbin
for i in $(locale); do
  unset "${i%=*}"
done
if [ "$TERM" = linux ]; then
  export LANG=C.UTF-8
else
  . /etc/locale.conf
  for i in $(locale); do
    key=${i%=*}
    if [ "${!key+x}" = x ]; then export "$key";fi
  done
fi
''',
 'usr/lib/tmpfiles.d/toddy-base.conf': '# DBus socket parent; static messagebus account is created in LFS 7.6.\nd /run/dbus 0755 messagebus messagebus -\n',
 'usr/lib/systemd/system-preset/50-toddy-base.preset': '# DBus socket activation is supplied by its package-owned vendor wants link.\n# Offline setup also masks wait-online: networkd Also= overrides preset disable (ADR-0060).\nenable systemd-networkd.service\nenable systemd-resolved.service\nenable systemd-timesyncd.service\ndisable systemd-networkd-wait-online.service\n',
}
LINKS={'etc/localtime':'../usr/share/zoneinfo/UTC',
       'etc/resolv.conf':'/run/systemd/resolve/stub-resolv.conf'}


def stage_configuration(destination):
    if destination.exists() or destination.is_symlink():
        raise ValueError('Preserve existing configuration stage before retry')
    destination.mkdir(parents=True)
    for relative,text in FILES.items():
        path=destination/relative;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text);path.chmod(0o644)
    policy=destination/'usr/share/toddy/base-config/default-links.json'
    policy.parent.mkdir(parents=True,exist_ok=True)
    policy.write_text(json.dumps(LINKS,indent=2)+'\n')
    (destination/'boot/efi').mkdir(parents=True)
    documents=destination/'usr/share/doc/toddy-base-config';documents.mkdir(parents=True)
    shutil.copyfile(ROOT/'LICENSES/LFS-MIT.txt',documents/'copyright')
    shutil.copyfile(ROOT/'config/books.lock.json',documents/'book-sources.json')
    (documents/'profile.json').write_text(json.dumps({
        'profile':'disposable-build-target',
        'book':'LFS 13.1-systemd chapter 9',
        'defaults':{'hostname':'toddy','locale':'en_US.UTF-8','console':'us','timezone':'UTC'},
        'boot_validation':'pending actual native boot',
        'release_obligations':['Live assembly replaces build-target fstab.',
                               'Installer writes selected disk UUIDs and user locale/timezone.',
                               'No password, signing key or provider credential is package payload.',
                               'Original project licensing remains subject to D10.']},indent=2)+'\n')
    return sorted(FILES)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    files=stage_configuration(args.destination)
    print(json.dumps({'configuration_files':len(files),'generated_link_defaults':len(LINKS),'installed':False,'destination':str(args.destination)}))

if __name__=='__main__':main()
