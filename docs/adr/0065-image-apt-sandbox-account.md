# ADR-0065: Preserve APT's unprivileged identity in fresh images

- Date: 2026-11-07
- Status: Native image-account checks passed; actual APT acquisition pending
- Amends: ADR-0055 image account set

Integration review found that the fresh image account baseline contained only
the 14 LFS users and 34 groups. The prepared APT recipe creates _apt in the build
target and configures APT::Sandbox::User "_apt", but fresh image generation must
not copy the builder passwd/shadow files. It would therefore omit the sandbox
identity unless explicitly added.

Frozen APT 3.0.4 apt-pkg/acquire.cc checks getpwnam(SandboxUser) near line 626.
If the user is missing it warns that privileges cannot be dropped and clears
APT::Sandbox::User. The subsequent inaccessible-destination branches can also
select unsandboxed downloads. Account presence alone is therefore necessary,
but not sufficient, for final APT sandbox acceptance.

Add the explicit Toddy service identity _apt with reserved image UID/GID 100,
locked password, /nonexistent home and /usr/bin/false shell. Document it separately
from the unchanged frozen LFS book source in live-account-baseline.json. Require
this exact identity during account generation; missing/reassigned identity is a
refusal, not an optional fallback. Generated images now have 15 users/35 groups,
with no build tester or inherited credentials. The previous 124-package candidate
inventory has no payload UID/GID 100; final image ownership still requires audit
against the actual accepted package generation.

The image does not inherit the build target's dynamically allocated _apt ID.
Runtime download directories must be generated/chowned for the image's account;
builder cache contents are excluded. The prepared build-target recipe and active
H07 inputs are unchanged. The false shell prevents interactive use and is
consistent with the fresh foundation service-account policy; APT uses the numeric
identity obtained from NSS, not a login shell.

Alternatives rejected: copying builder account files violates fresh-identity
requirements; dropping APT::Sandbox::User weakens the selected package profile;
retaining the pure book account list triggers the identified fallback after
image assembly. Explicit service additions preserve the book baseline and the
additional native package-manager behavior.

## Evidence and limits

Frozen APT source archive SHA-256:
e853aec49afbe520ebcd4dbcbc98e1c55262c6bf1c119cf43e6aec69752443c6.
Inspected apt-pkg/acquire.cc and apt-pkg/contrib/fileutl.cc directly from the
hash-verified archive. Existing LFS source identity remains in the baseline.

The expanded native account probe passes read-only Shadow pwck/grpck with exit 0
and no diagnostics. Native Glibc getent finds _apt; native Coreutils chroot
--userspec=_apt:_apt --groups=_apt executes native id as UID/GID/groups 100.
That process writes a disposable download-partial file owned by 100:100 and
cannot read a root-owned 0600 public fixture. All account passwords remain locked,
the machine ID is empty, the canonical DBus alias is retained, and five existing
state/refusal checks still pass. Installed accounts and Dpkg status are unchanged.

The first probe attempted setpriv, which the frozen Util-linux profile explicitly
disables. Corrected the probe to use the already accepted native Coreutils chroot;
no substitute host binary or new dependency was installed. Failure report SHA-256
b36a513e11e443d148ad08d0b94626240ee6a53601220c3f2da32653fa8b5ecd,
fixture /mnt/lfs/tmp/toddy-live-accounts-cckcng8o.

Final account report .local/logs/h10-live-accounts-probe.json SHA-256:
624f8c788afc48b32b1621b982211c06ee6f93aa3b482f79c1186be893185668.
Helper SHA-256:
8005bdb151f4d90abb58114bb75252acfad0d2d0a307bf053bdace5d4c7368bb.
Baseline file SHA-256:
b4c7eeb9c064fc72fe3dba20f66c9b5bbd2bd925513b4f87155d19911bee3077.
Repeated native PTY live-console/locked-password/unprivileged-refusal checks pass
with the new baseline. Report SHA-256:
84965a0fe2e11cbc4234c86aafe73957ee7349afe3f454e1350aff301366f1ef.

These checks prove native identity lookup, privilege dropping and fixture access
boundaries. Actual APT download processes, effective UID/groups, directory
permissions, signatures/HTTPS, absence of unsandboxed fallback and release-image
behavior must still be checked after native APT installation and image assembly.
No APT acquisition, new package acceptance or boot pass is claimed here.

The prepared native APT repository test now wraps each apt-get call and rejects
its exact frozen C-locale root-fallback diagnostics with exit 125, even when the
command otherwise succeeds. Ordinary package-integrity failures retain exit 100.
A local shell control-flow test covers clean success, ordinary failure and both
fallback warnings using a command stub. That unit check verifies the acceptance
wrapper only; it does not substitute for actual native APT acquisition evidence.
