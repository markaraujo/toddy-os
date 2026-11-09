# ADR0161: Calendar and NSS runtime prerequisites for the frozen GNOME stack

Status: libical/NSPR owned; NSS/EDS/native GNOME pending, 2026-11-09.

The approved graph's Evolution Data Server3.60.2 requires libical4.0.5, libsecret
and NSS3.126; GNOME Shell requires EDS. These are concrete frozen dependencies,
not new optional applications. Reuse owned libsecret and ICU78.3. Frozen BLFS
13.1-systemd pages general/libical.html (SHA4db2bf83babc6ed29b10394b1025751bff2d45c988bf3cd81fe1fd2e5175726a),
general/nspr.html (SHA5cb915e8fccaedcf8a6681d645fb8ebe81b70aa073bc44a657e7bcbd92316bb9)
and postlfs/nss.html (SHAc3f1b41079594657a8486d4321910b26e620f0098d81a733dd5d1fe253a03401)
define selected versions and supported build/install corrections. Exact official
HTTPS archives and the required versioned NSS standalone patch are frozen in
sources.lock.json before guest use; no foundation replacement or silent upgrade.
NSS source automation/release/nspr-version.txt requires >=4.39; selected4.40 meets it.

Build libical shared C/C++/GLib/GI, omit Vala/Java/docs and optional fuzzer matrix.
Original65CTest programs passed. Original recur uses icalfileset_new on a fixed
source file and requires a writable lock. Keep sources read-only; run only the
unchanged executable with its supported explicit path argument to an identical
private copy. It passed; input bytes/source/194originalELFs unchanged. No source
writability relaxation, library patch or full-suite replay.

The first own C consumer incorrectly unrefed the borrowed result of
icalproperty_get_rrule. Original source regression-recur.c and generated getters
show the value remains owned by the property. Installed validation exposed heap
corruption. Supersede that consumer result; remove only the invalid unref and
compile a new consumer, leaving library/stage/original tests unchanged. Corrected
installed UTF8/UTC recurrence/refusal/state/two-cycle recovery and actual
ICalGLib4.0GI passed. Verify-only transaction checks all187owned payload entries
and archive unchanged, zero root changes; never reinstall an installed package
to repair its postcheck. Canonical fresh recipe uses the private input initially.

Build optimized NSPR4.40 with supported pthread/64bit flags and the book's two
install-rule corrections (omit private scripts/static installation). The book
explains its full combined development suite is not useful for an optimized
released NSPR. Select three independent original atomic/printf/version programs
plus actual joinable threads/locked updates/private file/error/two-cycle recovery.
All passed;87ELFs retained. An own SDK version assertion expected4.40, but
upstream nspr.pc emits major.minor.patch4.40.0. Fix only that assertion, verify91
payload entries/archive unchanged and run installed consumer/SDK/APT. Sole root
change is generated APT cache; no package/library/original test replay.

NSS full network suite is documented by the frozen book as capable of hanging;
do not launch it blindly. Select bounded original cryptographic/API programs and
actual affected consumers, keeping TLS/trust-store/remote network acceptance
explicitly separate until measured. No claim of full security audit, broad
protocol conformance, GUI functionality or physical validation follows from these
prerequisites. NSS/EDS/native desktop integration remain B02 work.

[libical](../evidence/B02-libical-install.json), [NSPR](../evidence/B02-nspr-install.json).
