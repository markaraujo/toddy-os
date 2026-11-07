# ADR-0070: Activate APT's selected filter and observe acquisition workers

- Date: 2026-11-07
- Status: Configuration corrected; native observer preflight passed; APT acceptance pending
- Amends: ADR-0034 and ADR-0065

## Finding and source

The prepared APT recipe required HAVE_SECCOMP but did not set the runtime
APT::Sandbox::Seccomp option. Frozen APT 3.0.4 methods/aptmethod.h LoadSeccomp
returns without loading a filter when that option is absent; its default is
false. Compiled library support alone therefore did not implement ADR-0034's
selected runtime profile. This was found before APT was built or accepted.

The inspected archive apt_3.0.4.tar.xz still has frozen SHA-256
e853aec49afbe520ebcd4dbcbc98e1c55262c6bf1c119cf43e6aec69752443c6.
The extracted files were compared byte-for-byte with that archive:

| File | SHA-256 |
| --- | --- |
| methods/aptmethod.h | b657e37e83c55c937ad33740a9f0a8203d52f62ee8a641daddcd3f0ca228a30f |
| methods/http.cc | c843155a3f6a4bb21fdf73f358d4964681f8c42a81bc6e047befb488da4c8c89 |
| apt-pkg/contrib/fileutl.cc | 7ba9b43c23e7059ddfe356ab3d84bd0634ba0ac71cef80c664044c17beb61168 |
| debian/NEWS | 6955b6348413fb502c6fa604a5f9f932cc1af205c07eec9d58f2b9eb6efdbdce |

The native HTTP method requests BASE, NETWORK and DIRECTORY filter groups.
Configuration drops privileges before loading that filter. DropPrivileges sets
no_new_privs and changes the real/effective/saved IDs and supplementary groups.
The frozen NEWS explains the historical opt-in default. The upstream maintainer
also describes that default and compatibility constraints in
[Debian bug 1146723](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1146723;msg=7).
That report concerns another APT version; it is context, not proof of a failure
or an approved syscall exception in this frozen target.

## Decision

Set APT::Sandbox::Seccomp "true" in the Toddy vendor configuration and the
disposable repository test configuration. Require apt-config to report it after
installation. Keep the existing required compile-time feature checks, _apt
identity and root-fallback warning rejection.

Observe actual HTTPS acquisition during the existing signed repository install.
apt-worker-probe.py starts the real command, follows only its process descendants,
matches the resolved native HTTPS executable and records kernel process start
times, four UID/GID values, supplementary groups, effective capabilities,
no_new_privs, seccomp mode and filter count. Acceptance requires command exit 0
and an observed worker with the expected non-root IDs, no extra groups, zero
effective capabilities, no_new_privs=1 and seccomp mode 2. Its filter count must
exceed the observer's inherited count; an unrelated inherited filter cannot
substitute for the acquisition method loading its own filter.

The loopback TLS fixture delays only .deb responses by one second so the real
worker remains observable. It preserves exact response bytes, signing, TLS
validation and the existing five-second request timeout. The ordinary warning
guard still wraps the observed command. This measures a worker during a real
transfer; it does not claim exhaustive syscall-policy verification or coverage
of every acquisition method. Repeat the actual acquisition check in the final
image, whose accounts and kernel differ from the build environment.

Alternatives rejected: treating HAVE_SECCOMP as runtime evidence leaves the
identified gap; silently leaving the runtime disabled contradicts ADR-0034;
counting any process with seccomp mode 2 would accept inherited filters. No
frozen source upgrade, broad syscall exception or host security change is made.
If actual APT reports SIGSYS, preserve the fixture and diagnose the exact syscall
against the frozen source before making a focused, documented correction.

## Native evidence and limits

Reproduce the observer preflight with:

```sh
python3 scripts/host/probe_apt_worker_observer.py
```

The probe compiles a disposable native C process with the target compiler and
libseccomp. It really drops IDs/groups, installs a kernel filter and verifies
that getppid is denied with EPERM. It is not an APT implementation or an APT
acceptance substitute. Eight cases passed: two valid filter/identity cases and
six refusals covering root, no filter, an extra root group, filtered root,
nonzero command exit and an inherited filter without an additional worker
filter. Measured positive IDs/groups are 101, effective capabilities 0,
no_new_privs 1 and filter counts 1 over baseline 0, or 2 over baseline 1.

Raw .local/logs/h07-apt-worker-observer-<sha256>.json SHA-256:
40305e040709b367d83f7261430047d2ea813253ba2f20118c1acb278f713058.
Native fixture: /mnt/lfs/tmp/toddy-apt-worker-k9v6zdws.
Observer SHA-256:
3f11da80a5491e1e77d0ccdd1c0b815f2ab18abec55ec81a1c0a51c35a3614a2.
Native probe C source SHA-256:
c45c924d7a3a21eb5f68544901811b553beaad82c640f69fca2cc9151463388a.

The exact revised embedded HTTPS server also passed a native Python/OpenSSL
preflight: verified payload bytes after 1.005 seconds, rejected an unknown CA
(code 18) and wrong IP name (code 64), then stopped its server. Raw
.local/logs/h07-apt-https-observation-preflight-<sha256>.json SHA-256:
abb674ae5c21b9e30298452c83ec37fa7d1956c8e2b8b1b183047ddf23fccbc7.
Embedded server SHA-256:
e3ac7d9c5acf2feaa59243857cee42ba9248ce6a6549b5b7f43fddcad91314ee.

All 154 local checks pass, including the existing warning-guard regression.
No installed target files or active Berkeley DB inputs changed. Native APT
build, signatures/HTTPS operations, actual APT worker observation and final-image
retest remain pending. These prepared checks do not accept APT, H07 or G1.
