# ADR-0175: Owned libndp prerequisite for NetworkManager

Status: bounded native library acceptance; NetworkManager integration pending.

NetworkManager1.58.1's actual Meson source requires libndp unconditionally. Use
libndp1.9 from frozen BLFS13.1-systemd basicnet/libndp.html; do not upgrade the
foundation or add an unrelated network framework. The book's upstream URL is
HTTP; its HTTPS endpoint failed hostname certificate verification (curl60).
No archive or partial file existed after failure. Fetch the exact version from
the trusted BLFS OSU conglomeration mirror with TLS verification intact. Frozen
MD5 `9d486750569e7025e5d0afdcc509b93c` matched; freeze source SHA256
`a8ab214e01dc3a9b615276905395637f391298c84d77651f0cbf0b1082dd2dd4`
before any extraction/use. No publisher signature is claimed.

Use the book's supported shared-library profile in the existing read-only-input,
unprivileged/no-route isolation. The source/book provide no test suite. Record
make check0 as build plumbing, not an original test pass. Preserve4compiled ELFs
and6regular staged files. Own actual C API checks exercise all five supported NDP
message types, wildcard creation refusal, payload-length clamping/restoration and
two lifecycle cycles without sending packets. Do not pass arbitrary out-of-range
enum values: the source checks the documented wildcard, not every integer value.
This bounded SDK consumer is not malformed-wire-packet/parser qualification.

Native install/post0/0 changed18paths and owns22entries. Actual installed library
resolution, SDK version, UID101 C consumer, ndptool help and package audits passed.
Retain complete source LGPL2.1 COPYING and per-file conditions. No capabilities or
service privileges were added; raw-socket authorization and real NDP traffic are
not qualified. Continue NetworkManager/GDM/GNOME integration; no native desktop
acceptance is inferred. Never rebuild/reinstall the accepted dependency merely
to continue that chain. [Evidence](../evidence/B02-libndp-install.json).
