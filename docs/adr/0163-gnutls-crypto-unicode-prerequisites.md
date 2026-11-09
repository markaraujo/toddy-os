# ADR0163: GnuTLS crypto, Unicode and IDNA prerequisites

Status: Nettle/libunistring/libidn2 owned; GnuTLS/native GNOME pending, 2026-11-09.

Frozen GnuTLS3.8.13 requires the selected Nettle4.0 and recommends shared
libunistring1.4.2. Its optional libidn2 backend supplies actual IDNA2008 for
international hostnames; qualify selected2.3.8 rather than advertise an absent
feature. These concrete TLS/EDS dependencies remain within the approved source
graph; preserve accepted compiler/libc/OpenSSL/nghttp2 and existing ICU-backed
libpsl. GnuTLS lib/nettle already has NETTLE_VERSION_MAJOR>=4 branches, including
the two-argument digest API. No architecture or frozen-foundation replacement.

Nettle/Hogweed build shared against owned GMP6.3.0; omit static installation and
optional OpenSSL benchmark glue. Full original make check passed122programs;
one upstream x86-ibt test skips when its compiler/platform/CET conditions are not
available. Never count that as IBT/hardware acceptance.691ELFs retained. Own C
consumer initially used the v3 digest signature; correct only its call to v4,
compile consumer-only2 and preserve all original library/test/stage bytes. Actual
installed SHA256 known answer, public standard P256 generator, zero-scalar/off-
curve refusal/recovery and two lifecycle cycles/SDK/APT passed. Install/post0/0
changed99root paths; no GnuTLS/TLS proof follows from this alone.

libunistring shared build passed638original programs;36skips remain:33Windows-only,
two select/pselect programs requiring a route absent from the isolated namespace,
one traditional Arabic locale not installed. No original test rerun or expanded
locale/network matrix.1905ELFs retained. Own consumer initially assumed
u8_normalize rejects malformed UTF8/EILSEQ. Its implementation explicitly uses
u8_mbtouc_unsafe; malformed-input validation is a separate u8_check API (doc/unistr).
Correct that consumer assumption, never weaken a library input-validation gate:
validate before normalization and never pass malformed data to the unchecked
normalizer. Corrected consumer-only2 preserves all library/stage/original results.
Actual installed UTF8 validation, NFC combining marks, Portuguese lowercase,
overlong-input refusal by the validator, prior-state preservation, two lifecycle
cycles and dynamic/header SDK version0x010402/APT passed. Install/post0/0 changed65
paths. No claim that u8_normalize validates malformed input. GnuTLS
lib/str-unicode.c independently calls u8_check and returns INVALID_UTF8_STRING
before transformations unless a caller explicitly asks to ignore errors; the
next actual consumer must check that public API with default flags0.

libidn2 2.3.8 uses the owned shared Unicode library. All15original programs passed,
78ELFs retained, no skips. Installed actual UTF8/punycode roundtrip, nontransitional
sharp-s mapping, invalid UTF8 and leading-hyphen refusals, two recovery cycles,
SDK/APT passed. Install/post0/0 changed69paths. This is codec/IDNA evidence, not DNS,
remote network or native desktop acceptance. Both Unicode and IDNA exact upstream
legal notices are retained in owned native packages.

Prepare GnuTLS with supported C/runtime/tools/PKCS11 options, no optional C++
bindings, DANE, TPM, leancrypto, Brotli, docs or extended interop/Valgrind matrix.
Keep default NORMAL policy and the book's pkcs11: default trust selection; unified
anchors/provider still need their separate controlled integration. Run the
standard original suite with private loopback and no external route. Preserve all
skips and actual critical protocol/replay outcomes, not elapsed-time success.
Own native consumer checks actual SHA256/AES-GCM tamper refusal/recovery, default
UTF8 password API rejection, NFC state, IDNA2008 and TLS1.3/invalid priority parsing.
This does not replace original handshake/certificate checks, system-root trust,
remote provider, GNOME UI or physical validation. One guest writer and full-root
promotion verification remain mandatory.

[Nettle](../evidence/B02-nettle-install.json), [Unicode](../evidence/B02-libunistring-install.json),
[IDNA](../evidence/B02-libidn2-install.json).
