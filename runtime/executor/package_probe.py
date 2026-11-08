"""Disposable signed native APT input for the new executor wrapper only.

Reuses the accepted H07 fixture approach, not its full signature/HTTPS matrix.
All writes stay in the root namespace's synthetic/etc and/var, or private/build.
"""
import json
import os
from pathlib import Path
import subprocess

BASE=Path('/build/package-proof')
ENV={**os.environ,'GNUPGHOME':str(BASE/'keys'),'LANG':'C.UTF-8','LC_ALL':'C'}


def command(argv,*,capture=False,cwd=None):
    with (BASE/'fixture.log').open('ab') as log:
        result=subprocess.run(argv,env=ENV,stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture else log,stderr=log,check=True,timeout=30,cwd=cwd)
        return result.stdout if capture else None


def publish(version):
    stage=BASE/('stage-'+version);(stage/'DEBIAN').mkdir(parents=True);(stage/'etc').mkdir()
    (stage/'DEBIAN/control').write_text('Package: toddy-managed-probe\nVersion: '+version+'\nArchitecture: all\nMaintainer: Toddy OS <repo@example.invalid>\nDescription: Disposable executor package proof\n')
    (stage/'DEBIAN/conffiles').write_text('/etc/toddy-managed-probe.conf\n')
    if version=='1':
        # Real native maintainer-script boundary, not a mocked cancellation timer.
        (stage/'DEBIAN/postinst').write_text('#!/bin/sh\nset -eu\nprintf started > /etc/toddy-package-inflight\nsleep 1\n')
        (stage/'DEBIAN/postinst').chmod(0o755)
    for directory in (stage,stage/'DEBIAN',stage/'etc'):directory.chmod(0o755)
    for file in (stage/'DEBIAN/control',stage/'DEBIAN/conffiles'):file.chmod(0o644)
    (stage/'etc/toddy-managed-probe.conf').write_text('default-'+version+'\n')
    (stage/'etc/toddy-managed-probe.conf').chmod(0o644)
    command(['dpkg-deb','--build',str(stage),str(BASE/'repo'/('toddy-managed-probe_'+version+'_all.deb'))])
    # Only the current version is indexed; old archive remains a private cache.
    archive=BASE/'repo'/('toddy-managed-probe_'+version+'_all.deb')
    archive.chmod(0o644)
    (BASE/'repo/Packages').write_bytes(command(['apt-ftparchive','packages',archive.name],capture=True,cwd=BASE/'repo'))
    (BASE/'repo/Packages').chmod(0o644)
    (BASE/'repo/Release').write_bytes(command(['apt-ftparchive','release','.'],capture=True,cwd=BASE/'repo'))
    (BASE/'repo/Release').chmod(0o644)
    command(['gpg','--batch','--yes','--clearsign','--output',str(BASE/'repo/InRelease'),str(BASE/'repo/Release')])
    (BASE/'repo/InRelease').chmod(0o644)
    command(['apt-get','update','-o','APT::Update::Error-Mode=any'])
    command(['apt-get','--assume-yes','--download-only','install','toddy-managed-probe='+version])
    # file: acquisition optimizes by retaining the repository pathname. Seed the
    # canonical archive cache after signed-index/prefetch verification, matching
    # the production HTTPS acquisition boundary before offline native mutation.
    import hashlib
    cached=Path('/var/cache/apt/archives')/archive.name
    if not cached.exists():
        with cached.open('xb') as output:output.write(archive.read_bytes())
        cached.chmod(0o644)
    assert hashlib.sha256(cached.read_bytes()).digest()==hashlib.sha256(archive.read_bytes()).digest()



def prepare():
    BASE.mkdir(mode=0o755);BASE.chmod(0o755);(BASE/'keys').mkdir(mode=0o700);(BASE/'repo').mkdir(mode=0o755);(BASE/'repo').chmod(0o755)
    command(['gpg','--batch','--pinentry-mode','loopback','--passphrase','','--quick-generate-key',
             'Toddy disposable executor <executor@example.invalid>','ed25519','sign','0'])
    (BASE/'repository.gpg').write_bytes(command(['gpg','--batch','--export'],capture=True));(BASE/'repository.gpg').chmod(0o644)
    for path in ['/etc/apt/apt.conf.d','/etc/apt/sources.list.d','/etc/apt/preferences.d','/var/lib/dpkg','/var/lib/apt/lists/partial',
                 '/var/cache/apt/archives/partial','/var/log/apt']:
        Path(path).mkdir(parents=True,exist_ok=True)
    for path in ['/var/lib/apt','/var/lib/apt/lists','/var/cache','/var/cache/apt','/var/cache/apt/archives']:Path(path).chmod(0o755)
    Path('/var/lib/dpkg/status').touch()
    for path in ['/var/lib/apt/lists/partial','/var/cache/apt/archives/partial']:os.chown(path,42,42)
    Path('/etc/apt/apt.conf').write_text('APT::Architecture "amd64";\nAPT::Architectures { "amd64"; };\nAcquire::Languages "none";\nAPT::Sandbox::User "_apt";\n')
    Path('/etc/apt/sources.list').write_text('deb [signed-by='+str(BASE/'repository.gpg')+'] file:'+str(BASE/'repo')+' ./\n')
    publish('1')
    # Synthetic fixed-name diagnostics only, never a production payload logger.
    with (BASE/'fixture.log').open('ab') as log:
        for argv in [['dpkg-query','--show','--showformat=${binary:Package}\\t${db:Status-Status}\\t${Version}\\n','toddy-managed-probe'],['dpkg','--audit']]:
            subprocess.run(argv,env=ENV,stdout=log,stderr=log,check=False,timeout=10)



def finish():
    command(['gpgconf','--kill','gpg-agent'])
