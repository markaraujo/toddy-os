# ADR-0039: Normalize build ownership and preserve reviewed privileged helpers

- Date: 2026-11-06
- Status: Measured issue; packaging correction prepared, native upgrade pending

The 101-package records show exactly four unintended tester:tester CMake entries:
/usr/share/doc/cmake/Licenses and its three files. The recipe's cp -a followed
unprivileged tests, preserving build ownership. Payload audit confirms the
installed files match those recorded identities; that consistency alone does
not make build-user ownership appropriate for a release.

Normalize tester UID/GID ownership to root in staging, before hashes/archive
creation. Prevalidate every staged entry. Never normalize a build-owned setuid/
setgid file into a privileged root file automatically: stop for diagnosis.
Preserve intended system identities/modes using the exact accepted 16-helper
policy in config/package-ownership-policy.json. In particular DBus helper is
root:18 mode 4110 and wall is root:5 mode 2755; blanket chown/chmod would damage
those choices. Other helpers are the source-installed Shadow/Inetutils/util-linux
setuid programs. An unexpected privilege, owner or changed helper mode is an
error before package installation. Future packages need explicit reviewed
exceptions rather than implicit acceptance.

Record policy hash and normalized paths with the new archive. Correct CMake
through its versioned metadata upgrade, retain original archive/record and verify
actual installed identities afterwards. This does not change the owner's full
administration requirement or implement agent policy; it makes source-installed
OS helper permissions explicit and recoverable. No host permission is changed.

Evidence: actual 101-package archived payload metadata and read-only native
SHA-256/link/mode/owner audit; CMake cp -a recipe, DBus Meson installation and
frozen LFS Shadow/Inetutils/util-linux recipes. Regression tests cover build-doc
normalization, privilege escalation refusal and exact helper preservation.
