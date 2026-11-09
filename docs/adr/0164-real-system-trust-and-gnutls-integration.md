# ADR-0164 — Real system trust and owned GnuTLS integration

Status: accepted for the verified scope below. Date: 2026-11-09.

## Cause and decision

The frozen GnuTLS3.8.13 standard suite exposed two concrete environment gaps:
public DNS is deliberately unavailable in the compiler namespace, and the
installed p11-kit provider had no system anchors. Preserve both original FAIL
records. Neither elapsed time nor absence of logs proves acceptance. Do not grant
external networking to compilers or inject fake DNS/trust to make tests green.

Use make-ca1.16.1 and exact Mozilla policy from the already owned NSS3.126 source,
following frozen BLFS13.1-systemd postlfs/make-ca.html. Source identities and book
hashes are in the source lock and linked evidence. Generate trust as UID101 with
zero capabilities/no-new-privileges, read-only source/usr/configuration and no
external route. Bind only two private candidate directories at the real SSL/P11
paths so the actual default provider sees proposed outputs. Existing OpenSSL
configuration/misc/private paths stay read-only; the private-key directory was
verified empty before preparation. No real owner credentials are used or copied.

The first candidate failed explicitly despite generator exit0: its OpenSSL input
used absent /dev/stdin. Add the standard self-proc stdin/out/err descriptor aliases,
without new devices or privileges. Retain failed candidate1 and prove the full
installed root unchanged before fresh candidate2. That generation, original
GnuTLS default-trust program and ISRG root verification succeeded. Its own legacy
compatibility copy subsequently failed because trust deliberately seals its
certificate directory0555. Finish only that private metadata/copy step, restore
0555 and verify preexisting candidate bytes; do not repeat generation or passing
tests. Acceptance proves152574 installed entries unchanged and zero changed paths.

## Native factory data transaction

Candidate2 contains172 policy anchors and121 TLS server roots versus118 from the
foundation bundle: three additions, no removals, exact DER identities retained.
Upgrade only ca-certificates to2026.11.09-1+toddy1 using that qualified data,
retained upstream legal notices and a full-root controlled native transaction.
Preserve both legacy bundle aliases and existing OpenSSL-owned directory modes;
exclude existing OpenSSL configurations/private paths, unused NSS database and
Java artifacts. No OpenSSL/library rebuild or silent upstream version change.

Actual install/postcheck0/0 changed717paths;721package entries owned. All9803
OpenSSL package entries remain identical. Actual installed P11 enumeration,
unchanged original GnuTLS default-trust test and OpenSSL default ISRG verification
pass, with dpkg/APT checks. Old archive/record remain available for recovery;
retaining them and documenting undo is not an executed rollback test.

This slice installs factory data. The owned P11 distribution callback remains its
previous placeholder; functional local-trust updates/recovery and NSS bundled-root
alias integration need separate controlled transactions and affected consumers.
Do not enable an updater/timer or claim these pending paths work.

## GnuTLS evidence and ownership

Reuse813 distinct original PASS records,102 SKIPs and two original FAILs. The
certificate summary says80 entries because its list repeats seven names; only73
unique drivers/records exist. Bind the exact list and PASS lines, and count917
actual distinct records. Own stage4 miscount failed before staging; stage5 corrected
only this guard, preserving original binaries/results. Native consumer proves
SHA256/AES-GCM tamper refusal/recovery, default invalid-UTF8 password rejection,
NFC state, IDNA and TLS1.3/invalid-priority handling across two lifecycle cycles.

Own first native qualifier compared filesystem enumeration order and failed with
zero changed paths before promotion. Exact917 name/result mappings were identical;
compare identities and cardinality, then perform one new unique transaction.
Owned GnuTLS install2/post0/0 changed66paths. Actual installed library/SDK/native
consumer and unchanged original default-trust test pass without private library
or trust overrides. Original TLS1.3 supported-versions/anti-replay passes remain
required. No full passing-suite replay or rebuild.

Public DNS remains unqualified and must pass in the real native network context
before B02 acceptance. Remote TLS, browser, GNOME login/UI and physical hardware
are not proved by these library/data checks. The fresh combined build recipe and
local-trust update/recovery paths still need portable integration; historical
partial jobs and their bounded finishing helpers remain explicit evidence.

[Private CA stage](../evidence/B02-ca-stage.json),
[native factory trust](../evidence/B02-ca-native-install.json),
[GnuTLS stage](../evidence/B02-gnutls-stage.json),
[owned GnuTLS](../evidence/B02-gnutls-install.json).
