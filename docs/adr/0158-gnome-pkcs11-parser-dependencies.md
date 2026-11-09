# ADR0158: frozen GNOME PKCS11/parser dependency qualification

Status: libtasn1/p11-kit owned; Gcr original fixture correction pending, 2026-11-09.

The frozen GNOME Shell50.4 source requires Gcr4/EDS unconditionally; its supported
Meson options do not provide a calendar/EDS bypass. Gcr4 requires p11-kit0.26.5;
its trust module recommends libtasn1. Select same-book libtasn1 4.21.0 via the
already frozen p11-kit parent, preserving the accepted foundation and existing
libgcrypt1.12.4/libgpg-error1.61 security overlay. No crypto-library downgrade or
foundation rebuild. Book pages and full source hashes are in sources.lock.json.

Security/ABI source review: libtasn1 frozen NEWS records fixes for
CVE-2025-13151 and earlier CVE-2024-12133. Its published ABI and native SDK are
used directly;40original programs passed without skips,111compiled ELFs retained.
A new C consumer encodes/decodes a typed INTEGER/BOOLEAN sequence using strict
DER, rejects truncation and recovers twice. The identical consumer binary loads
the installed library in plain target chroot without a /stage path or loader
override, then package/SDK/audit checks pass. This is bounded parser evidence,
not a claim that all present/future advisories or credential flows are covered.
[Owned parser evidence](../evidence/B02-libtasn1-install.json).

Frozen p11-kit NEWS records nested-attribute overflow CVE-2026-18938, recursion
CVE-2026-13757 and NULL-parameter CVE-2026-2100 fixes. Build published0.26.5 with
libffi/trust module and /etc/pki/anchors, using bundled authenticated pkcs11-json
and no downloads. Run original fixture programs and typed URI/refusal/recovery
API checks without loading real credentials. Credentials/tokens/installed root
trust are separate acceptance. Keep test stdout/fixtures private; public evidence
contains counts/source hashes and sanitized consumer outcomes only.

Upstream install does not authorize activating its server/socket or granting
assistant policy. No daemon enablement or provider/network service is added by
this library slice. Integrate make-ca and the NSS trust-provider alias only after
the actual pinned trust source/backend is qualified; do not install a broken
update-ca-certificates wrapper or advertise an unqualified root store. These are
required before full browser/network acceptance, not claims from parser tests.

p11-kit original67programs passed;1077observed TAP pass lines plus two exact
original nested skips (getprogname symlink path, optional p11tool server-access).
334ELFs retained, staged/installed URI/refusal/two-cycle recovery0, no credentials
loaded. Owned0.26.5-1+toddy1 install/post0/0; trust-store/real token/server activation
remains separate. [Proof](../evidence/B02-p11-kit-install.json).

Gcr4.4.0.1 uses accepted owned GnuPG2.5.24 and libgcrypt security overlay, GTK4/GI,
upstream optional ssh_agent=false (no OpenSSH agent/key-store runtime integration
claim), Vala/docs omitted. Full compile succeeded;38original programs passed,
askpass's public-key derivation fixture aborted at chmod of a read-only source
fixture, before invoking ssh-keygen; separate inspection confirms that tool is
also absent. Preserve the exact initial cause and both preconditions.
Preserve failure, prepare same-book OpenSSH10.5p1 as a private qualified test SDK
and a private byte-identical writable fixture overlay for that exact input,
then rerun only that original test; no fake tool, assertion removal, or suite replay.
Review actual compile/stage results before further operations.

The exact Gcr fixture failure was source-sample chmod, not tool invocation. Tar
mode0664 is safely extracted0644; initial handoff metadata guard refused before
writes, actual source bytes/mode and absent handoff/SDK verified before correction.
Scope a private byte-identical RW mount to only this sample and this exact Gcr
input. All other source paths remain RO; original source stays0644, private sample
0600. First repair passed properties but exposed two missing-keygen SKIPs, not
passes. Qualify private OpenSSH10.5p1 keygen/crypto119original cases and actual
ephemeral-key/refusal/recovery, metadata-only whitespace gate recovery; no installed
SSH package/server/network claim. After verified handoff, rerun ONLY two skipped
original cases: derive/cancel passed without skips. Reuse38other programs and
properties.203original ELFs unchanged; stage/native transport/refusal/recovery/GI0.

Gcr4.4.0.1-1+toddy1 installed,339payload entries. Initial postcheck incorrectly
expected Gck's internal library version2.4.0.1 from pkg-config; Meson emits project
version4.4.0.1. Read-only full payload/archive reconciliation and corrected
installed transport/GI/SDK/APT checks passed recipe/post0/0. Only generated APT
pkgcache changed during verification; no reinstall/build/original test replay.
Graphical prompts/keyring/real credentials remain pending. Preserve source-bound
private failure/job/unit logs and exact fixture checks.
[SDK](../evidence/B02-openssh-keygen-sdk.json),
[owned Gcr](../evidence/B02-gcr-install.json).
