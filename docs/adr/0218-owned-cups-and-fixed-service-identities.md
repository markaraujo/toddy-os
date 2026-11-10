# ADR-0218 — Owned CUPS and fixed factory service identities

Status: native local CUPS SDK/payload accepted; printing and graphical integration pending.

## Exact corrected build and native package

[Actual native installation](../evidence/B02-cups-install.json) recipe/postcheck0/0
changed927paths and installed964payload entries. Archive SHA256
01aa732dba3a9f3afa2c65b221d940808ec965a41b171a8cdcd6f1b6b5cf5e52.
The qualifier binds the frozen CUPS2.4.19 prepared-input digest, source alias and
fingerprint, exact two corrected job command digests, prefix/configuration and
staging suffix, current resume helper, original failed resource observation,
corrected reserve observation,250ELF/846stage maps, restored Makefile and retained
logs. No compiler, original tests, source extraction or stage replay.

Dependencies are the observed owned Glibc/GCC/ACL/GnuTLS/PAM/USB/Xcrypt/Zlib/DBus/
Systemd/Shadow packages. No frozen foundation upgrade. Full component payload
retained with etc/var/run/usr layout and local client socket configuration.
Configuration files, including client.conf, are native conffiles.

## Reviewed service ownership and identity setup

Frozen BLFS13.1-systemd `pst/cups.html` specifies lp UID9/group9 and lpadmin GID19.
The selected scheduler/conf/notifier Makefiles specify fourteen exact non-root
ownership paths: server configuration/ppd/ssl, cache/RSS, spool/tmp and runtime
certificates. Runtime root/log directories retain normal root ownership; no
setuid/setgid is introduced. Package ownership exceptions are exact package/path/
UID/GID/mode tuples, with three focused tests refusing wrong identity/mode or an
unreviewed service-owned executable.

Actual installed target has no systemd-sysusers binary. Use the existing owned
Shadow tools and book identities in the full-root native recipe. Validate names
and reverse numeric IDs before any write. Create lpadmin19 only if absent, then
locked system user lp9:9, home/var/spool/cups, shell/bin/false, without home/mail
spool/log initialization or owner group membership. Native defaults already set
CREATE_MAIL_SPOOL=no. Package units are installed but neither enabled nor started.

The existing no-maintainer-script package contract is preserved. Factory account
setup is performed by the audited native recipe and persists in the base image;
the archive alone is not qualified for acquisition into an arbitrary external
root missing these identity preconditions. No optional catalogue entry or generic
account-hook framework is introduced. Owner credentials and assistant policy are
independent of this fixed non-login service identity.

## First account failure and actual bounded recovery

The first native recipe passed validation and created only lpadmin19, then
useradd refused the supplied `-K CREATE_MAIL_SPOOL=no`: this option accepts
login.defs keys, whereas the already-correct value is in etc/default/useradd.
Actual recipe1/postcheck-null changed exactly four group/gshadow paths. Read-only
inspection confirmed lp name/UID9 absent, group19 empty, no promotion/archive.
The original receipt and failure remain retained, never rewritten as success.

One source-backed correction removed the unsupported option and requires the
existing default=no. Unique accounts2/native-install2 guard the exact previous
failure, four diff keys, current absent lp9/empty group19 and absent stage/archive
before continuation. Groupadd was not repeated. Installed identity is locked,
non-login; no owner or other user was added to administrative membership.

## Native headroom, safety and actual validation

[Librsvg custody](../evidence/B02-librsvg-promotion-custody.json) qualified its
exact archive/record/closed-promotion/installed payload and retained workstage,
then retired only the promotion usr replica. Reclaimed30,089,216bytes with full
root snapshots identical, all source/compiler/workstage/archive/DEBIAN retained.
Never replay it. This made normal root promotion fit its measured conservative
gate; no scratch triple-promotion gate or reserve was weakened.

Installed UID101/NNP/capabilities0/private-device/no-route local IPP Unicode/add/
find/delete/absent-attribute/two recoveries passed. CLI version/serverroot/serverbin/
datadir matched corrected paths. Private configuration access was denied, followed
by successful CLI recovery. Exact stage bytes,14owned service paths, locked
identity, empty administrative membership, conffiles, ABI/PC/APT and disabled
units were checked. Full-root transaction and original failed attempt retained.

No printer/job/driver/device/remote SNMP, daemon/server/network/TLS connection,
Settings GUI, complete GNOME session or physical-machine acceptance. CUPS filters
and actual printing remain separate qualification work. B02 is still in progress.
Next Settings prerequisite is frozen UDisks2.11.2 with libblockdev3.5.0 and their
required closure, preserving core panels and measuring resources before building.
