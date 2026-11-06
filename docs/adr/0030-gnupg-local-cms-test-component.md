# ADR-0030: Enable local Gpgsm to preserve the complete GnuPG suite

- Status: Configuration correction prepared; complete rebuild/retry pending
- Date: 2026-11-06
- Scope: Authenticated frozen GnuPG 2.5.24 native build

The initial local signing profile disabled Gpgsm. Its complete check reaches
65 OpenPGP successes/one skip, then fails CMS setup because the disabled binary
is absent. tests/Makefile.am unconditionally includes cms, and
 tests/cms/gpgsm-defs.scm invokes that tool during setup. The runner stopped
with exit 2, zero installed changes; no package was staged. This is a build
profile defect, not an accepted CMS regression or external-access requirement.

Enable Gpgsm with the already accepted Libksba/Libgcrypt/Libassuan dependencies.
Keep LDAP, Dirmngr, smartcards/Scdaemon, G13, Keyboxd, TPM2d and WKS disabled.
Upstream CMS fixtures explicitly use disable-crl-checks and a faked internal
historical time for their public demo certificates, so the suite supports local
CMS without introducing external keyservers. These test-only settings do not
alter system time or global trust and must not become production defaults.
No claim of online revocation/keyserver support follows.

Verify every original archived source byte, preserve the entire first build and
check log, configure/build in a fresh build directory and run unchanged complete
make check, including CMS and later test groups. Do not delete/exclude CMS or
ignore its error. Native installation and detached signing/tamper contracts
remain gated on the new result. This corrects ADR-0026's original profile without
changing source versions or weakening acceptance criteria.

Sources: actual authenticated source tests/Makefile.am,
 tests/cms/gpgsm-defs.scm, full initial check log and dispatcher failure record.
