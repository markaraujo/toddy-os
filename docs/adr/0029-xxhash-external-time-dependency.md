# ADR-0029: Build GNU Time for XXHash's complete tool suite

- Status: Source verified/frozen; native Time build and XXHash retry pending
- Date: 2026-11-06
- Scope: H07 XXHash 0.8.4 test dependency

XXHash's full make test failed only when the collision tool attempted to invoke
external time (exit 127). Shell timing syntax cannot satisfy this executable
dependency. No installed paths changed; initial complete output is retained,
including the suite's intentional negative checksum diagnostics.

Select Time 1.10 from frozen BLFS 13.1-systemd, rather than weakening/removing
the tool tests. Official GNU archive matches book MD5
 ded256bf7d215594fb3b51d3d9d74e15 and observed SHA-256
 e8c29fb4ab599d8478e41e8618f50db8aede9c90af27d0d2ef28ae50d5de09c3.
Its detached signature passes gpgv using the previously fetched official GNU
keyring, signer 2371185508D1317BD578E5CC8CE6491AE30D7D75 (Collin Funk).
Actual status/stderr is retained outside Git in
.local/upstream-verification/time-signature-verification.log. No global trust
change or foreign binary import is needed.

Build/check/package Time natively and verify command-exit propagation plus
resource-output formatting. Then verify all original XXHash archive source
bytes remain unchanged and repeat the complete unprivileged suite before
staging/installing. Require native XXH64/XXH3 empty-input vectors and version
metadata. A missing dependency is not an accepted algorithm failure; do not
skip tests or upgrade XXHash to bypass it.

Sources: frozen BLFS 13.1-systemd general/time.html; authenticated official
[GNU archive](https://ftp.gnu.org/gnu/time/time-1.10.tar.gz) and
[signature](https://ftp.gnu.org/gnu/time/time-1.10.tar.gz.sig); actual XXHash
Makefile/tool-test failure in the designated VM.
