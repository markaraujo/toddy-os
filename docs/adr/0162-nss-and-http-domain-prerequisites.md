# ADR0162: Qualified NSS and HTTP domain prerequisites

Status: NSS/libpsl owned; TLS/provider/GNOME integration pending, 2026-11-09.

The concrete EDS3.60.2 CMakeLists.txt requires NSS and libsoup3. Libsoup3.6.6
requires libpsl and glib-networking, in addition to already owned XML/nghttp2.
Preserve accepted nghttp2 1.71.0 security overlay rather than rebuilding the book's
1.70.0 baseline. Source/ABI prerequisites are refined from current frozen code,
without changing the approved desktop architecture or installing Evolution UI.

Use frozen NSS3.126 with owned NSPR4.40, SQLite3.53.4 and zlib1.3.2. Its required
BLFS standalone patch applied four files but rejected only final manifest hunk
context, where this source inserted HAVE_ALL_TARGET and prepare_build. Derive the
same patch with only that hunk's adjacent context corrected; same five build/
install file changes, no runtime source change or fuzzy application. Freeze both
patch identities and exact expected outputs in nss-patches.lock.json. Before
completing the existing partial input, verify all4845archive files, four expected
patched files and exact two patch-tool sideeffects. Finish only the manifest's
DIRS addition once; preserve rejected text in durable receipt. Never replay either
whole patch or source preparation on that reconciled input.

NSS frozen source doc/rst/releases/nss_3_126.rst records parameter validation,
DER/PBE/OCSP bounds and integer-overflow hardening. This is source review of the
selected version, not a current comprehensive advisory audit or blanket security
claim. Frozen BLFS postlfs/nss.html says the full network suite may hang. Select
five actual bounded original crypto/DER/container/API programs instead:2271cases
passed, three upstream disabled util cases remain unexecuted. All745compiled ELF
artifacts retained. Actual SHA256 known answer/random/AES-GCM roundtrip/tampered
tag refusal/recovery and two initialization/shutdown cycles passed. TLS protocol,
full PK11 matrix, remote network and default trust-store integration stay separate.

The book's stage glob also selects two original test modules when tests are built.
Preserve the immutable qualified stage; remove only libpkcs11testmodule.so and
libnssckbi-testlib.so from a verified production copy before promotion. No tests,
private databases or real credentials are shipped. Keep upstream bundled roots
until a separately qualified p11-kit/make-ca provider transaction, never silently
switch or claim unified trust-store acceptance.

Initial install0/post1 exposed the postcheck's bare packaging chroot lacking
/dev/urandom, which NSS lib/freebl/unix_urandom.c uses. Verify294owned entries and
archive unchanged, then supply ONLY null/zero/random/urandom through a tmpfs/dev
in a private mount namespace. No disk devices, persistent mounts or global
security change. Verify-only2 passed0/0 with zero root changes; installed crypto,
private SQL database creation, malformed DER certificate refusal/unchanged empty
listing, cleanup, SDK/APT passed. Original build/tests/stage/package were reused.

For libpsl0.23.3 choose upstream Meson runtime=libicu, reusing qualified ICU78.3
and its Unicode/IDNA support. Frozen basicnet/libpsl.html explicitly lists ICU as
an available backend; Meson supports it directly. No extra libidn2 or separate
Unicode runtime is introduced for this consumer. Builtin suffix data comes from
the exact source archive; no build network/download. Eight originals passed:
five suffix/cookie/registrable programs plus three finite corpus drivers, not a
fuzz campaign. Own initial result-count assertion expected only five; reconcile
metadata only after checking all eight registered successful records, without
compiler/stage/consumer/test replay.32ELFs retained. Installed builtin/runtime
wildcard/exception, public-suffix cookie refusal, actual ICU Unicode lowercase,
invalid converter refusal and two recovery cycles/SDK/APT passed. Install/post
0/0 changed21paths. Actual browser/HTTP/TLS/GNOME remain pending.

[NSS evidence](../evidence/B02-nss-install.json), [libpsl evidence](../evidence/B02-libpsl-install.json).
