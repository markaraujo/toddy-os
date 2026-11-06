# ADR-0026: Freeze authenticated native signing tools

- Status: Verified/frozen sources; native build and signing contracts pending
- Date: 2026-11-06
- Scope: H07 native repository/signature tooling, supplemental BLFS recipes

## Selection and source evidence

Select Libgpg-error 1.61, Libgcrypt 1.12.4, Libassuan 3.0.2, Libksba 1.8.1,
nPth 1.8 and GnuPG 2.5.24. All six release archives pass gpgv verification with
both officially published release fingerprints:

- Werner Koch: 6DAA6E64A76D2840571B4902528897B826403ADA
- Niibe Yutaka: AC8E115BF73E2D8D47FA9908E98E9B2D19C6C8BD

The scoped public keyring was fetched from the official HTTPS site; fingerprints
were checked against its release-key page. No workstation/global keyring trust
was altered. Every source SHA-256/size/canonical URL, actual download URL and
signing identity is frozen in supplemental-sources.lock.json. Full gpgv status
and stderr logs remain outside Git under
.local/upstream-verification/native-signing-candidates/.

The primary gnupg.org hostname repeatedly timed out; listed mirrors served
older source indexes. The same official web server is responsive as
https://ftp.gnupg.org with its website /ftp/gcrypt/ path. Preserve canonical URLs
and actual transport aliases, not a guessed FTP-root path. Neither an HTTP
error page nor an unavailable candidate was marked verified. Both signatures
remain the authenticity requirement independently of the transport workaround.

The original BLFS candidates are GnuPG 2.5.21/Libgcrypt 1.12.2/Libksba 1.8.0.
Review of authenticated NEWS files justifies choosing the newer releases before
this supplemental freeze: GnuPG fixes revoke-import double-free, certificate
parser debug printf and DNS/card OOB cases; Libgcrypt adds RSA/PSS/OAEP/KEM
length/canonical checks, fixes cSHAKE padding and other validation defects;
Libksba fixes a CMS parser infinite loop. No already installed/frozen package
is silently upgraded. No claim of universal vulnerability freedom follows.

## Build profile and acceptance

Use the frozen BLFS autotools recipes and complete applicable upstream suites.
Build GnuPG's local OpenPGP signer/verifier/agent profile; explicitly disable
LDAP, Dirmngr, S/MIME Gpgsm, smartcard support/Scdaemon, G13, Keyboxd,
TPM2d and web-key-service tools. This avoids
claiming unsupported external keyservers/card/S/MIME capabilities and additional
unbuilt network dependencies. No tests are removed; retain configured feature
and skip reports. Agent/pinentry loopback must work in real batch signing tests.
Later desktop features needing a broader GnuPG profile require a separately
validated native package update with the same frozen source, not hidden tools.

Require native hash/library probes, real temporary-key detached signing and
verification, tampered-message rejection and scoped-public-key APT repository
contracts. Keep temporary/repository private keys outside Git/ISO/logs; do not
print them. A test signature is not an accepted signed repository or release.
No global security weakening or foreign binary package is an alternative.

## Sources

- Frozen BLFS 13.1-systemd library/GnuPG recipe pages and authenticated archive
  NEWS/configure sources, read directly.
- [Official release selection](https://www.gnupg.org/download/),
  [release fingerprints](https://www.gnupg.org/signature_key.html) and
  [official public keys](https://ftp.gnupg.org/signature_key.asc).
- [Responsive official source server](https://ftp.gnupg.org/ftp/gcrypt/) and
  [upstream-listed mirrors](https://gnupg.org/download/mirrors.html).
