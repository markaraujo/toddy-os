"""Stage explicit desktop network ownership without touching running services."""
from pathlib import Path
import shutil

MARKER='/etc/toddy/network/use-networkmanager'
CONFFILES=[MARKER,
    '/etc/NetworkManager/conf.d/10-toddy-desktop.conf',
    '/etc/systemd/system/NetworkManager.service.d/10-toddy-network-owner.conf',
    '/etc/systemd/system/systemd-networkd.service.d/10-toddy-network-owner.conf']


def stage(destination, repository):
    destination=Path(destination);repository=Path(repository)
    assert not destination.exists() and not destination.is_symlink(), 'Inspect existing stage; never overwrite it'
    files={
        MARKER:'NetworkManager\n',
        CONFFILES[1]:'# Toddy desktop defaults; later owner configuration may override these.\n[main]\nplugins=keyfile\ndns=systemd-resolved\n',
        CONFFILES[2]:'# Desktop ownership; marker removal selects the retained foundation networkd.\n[Unit]\nConditionPathExists='+MARKER+'\n',
        CONFFILES[3]:'# Never compete with the selected desktop DHCP owner.\n[Unit]\nConditionPathExists=!'+MARKER+'\n',
    }
    for name,content in files.items():
        p=destination/name.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(content);p.chmod(0o644)
    link=destination/'etc/systemd/system/multi-user.target.wants/NetworkManager.service'
    link.parent.mkdir(parents=True,exist_ok=True)
    link.symlink_to('/usr/lib/systemd/system/NetworkManager.service')
    doc=destination/'usr/share/doc/toddy-desktop-network';doc.mkdir(parents=True)
    shutil.copyfile(repository/'LICENSE',doc/'copyright')
    shutil.copyfile(repository/'LICENSES/CC-BY-4.0.txt',doc/'CC-BY-4.0.txt')
    (doc/'README').write_text('''Toddy desktop network ownership

The use-networkmanager marker selects the installed NetworkManager at boot.
The retained foundation networkd service has the inverse condition. NetworkManager
uses keyfile profiles and the existing systemd-resolved service. Original networkd
configuration, resolver symlink, profiles and service unit security remain intact.
No connection credentials or external connectivity probe are supplied here.

The package enables only NetworkManager.service. It does not enable its optional
wait-online unit; ordinary offline desktop boot must not require a connection.
The upstream dispatcher retains normal on-demand activation. Native daemon,
polkit, DHCP/DNS, GUI/offline/reboot and recovery checks are separately required.

Owner configuration under /etc is a conffile. Higher-priority NetworkManager
configuration remains available. To select the retained networkd recovery path,
as administrator stop NetworkManager, move /etc/toddy/network/use-networkmanager
to a retained backup path, then start systemd-networkd (or reboot). To return,
stop all networkd activation sockets together with its service before restoring
the marker. Stopping only the service allows a pending socket request to restart
it before the marker changes. For the pinned Systemd261.2 units use:

systemctl stop systemd-networkd-resolve-hook.socket systemd-networkd-varlink.socket systemd-networkd.socket systemd-networkd-varlink-metrics.socket systemd-networkd.service

Verify those five units are inactive, restore the marker, start NetworkManager,
and use nmcli device connect INTERFACE to acquire a managed DHCP connection.
Verify NetworkManager active, networkd inactive, fresh DHCP options and public DNS.
A reboot with the restored marker also selects NetworkManager. Never change
owner profiles or use a guessed interface name.
After changing manager ownership, check actual service/address/route/DNS state;
never start both managers on the interface or interpret a timeout as recovery.
NetworkManager's ordinary networking-off setting leaves networkd unselected.

No hostname, owner home, Wi-Fi profile, credential, global host security setting,
physical disk or foundation package payload is changed by these configuration files.
Original configuration generator is MIT; this README is CC BY4.0.
''')
    for p in destination.rglob('*'):
        if not p.is_symlink():p.chmod(0o755 if p.is_dir() else 0o644)
    return CONFFILES.copy()
