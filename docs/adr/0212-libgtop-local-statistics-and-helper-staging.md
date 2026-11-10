# ADR-0212 — Libgtop local statistics and helper staging

Status: accepted for B02's scoped native library/API package.

## Context and scope

Control Center50.4 requires libgtop-2.0. Use frozen BLFS13.1-systemd
libgtop2.41.3, shared library/GI and authenticated original helper payload. Build
on a new private inode7269 within the existing Doxygen scratch; original cache
fingerprint remains unchanged. An additional own scratch recipe is recorded
without replacing the initially prepared source/recipe. Require a filesystem
separate from /usr and the512MiB scratch reserve. Target16GiB remains fixed.

Actual [build/stage](../evidence/B02-libgtop-stage.json):99ELFs/139regular stage
files. The book/source has no upstream test suite; do not call an empty make check
a passing suite. An own public-header typo failed after compile/stage; consumer-
only correction uses glibtop.h plus glibtop/open.h. Direct local C memory,
uptime and own-process identity checks passed, including absent-PID refusal and
two recoveries. Missing /sys is an intentional private-profile warning, not a
kernel-version or physical-resource claim. No server or elevated identity used.

## Concrete staging privilege failure and correction

The generated install hook contains test -n DESTDIR || chown ... && chmod4755.
Shell precedence evaluates this as (test || chown) && chmod. Nonempty DESTDIR
skips chown but still sets4755. Actual uninstalled helper owner101/mode4755 was
detected by the mandatory stage guard, never executed or installed that way.

For fresh builds, group the two postinstall commands in the generated Makefile.
Keep upstream C/source unchanged. For the already complete private stage, change
only the authenticated owner101 helper mode4755 to0755; inode/content and every
compiler/stage byte remain unchanged. Reuse the already successful API log.
Metadata-only3 passed. A separate fixture applied the exact fresh recipe to a
copy of the actual generated Makefile: intercepted commands reproduced old
chmod, verified no commands for corrected DESTDIR, and preserved both original
commands for empty DESTDIR. It never performed real chown/chmod or modified the
original Makefile. Fixture evidence is distinct from actual staged mode/native
package evidence. No global security setting or installed privilege was relaxed.

## Actual native package and limits

[Native install](../evidence/B02-libgtop-install.json) recipe/post0/0,
159changed paths. Installed helpers root:root0755, no setuid/setgid or activation.
Actual UID101/NoNewPrivs/private-proc/private-device/no-route direct C API,
missing-PID refusal/two recoveries, GI namespace/memory-function availability,
all runtime ELF resolution, exact payload/version, shared Info registration and
APT passed. Shared /usr/share/info/dir is generated natively; do not compare it
to the isolated package's own index. GI metadata availability is not a GI
statistics call. The generated GIR contains a raw EOT constant accepted by the
native typelib tool but rejected by strict XML1.0 parsing; preserve that limitation.

Remote daemon/helper protocol, cross-user privileged process access, Control
Center UI, actual desktop boot/idle measurements and physical-machine behavior
remain unqualified. The assistant's authorized administration remains owned by
the independently audited/revocable executor; this library is not its authority.

[Mesa duplicate custody](../evidence/B02-mesa-promotion-custody.json) reclaimed
44417024B from only the closed native promotion usr copy, after exact archive,
record, installed payload and original workstage checks. Installed root changed0,
original workstage fingerprint unchanged, source/compiler/archive/DEBIAN retained.
The compiler was not rehashed by this custody action. No trim, old cleanup replay,
reserve reduction or foundation rebuild was used.
