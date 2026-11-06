# ADR-0036: Close native package metadata with versioned archives

- Date: 2026-11-06
- Status: Audit/upgrade tooling prepared; closure pending

The actual 101-package audit inspected 2551 ELF files. It found 135 undeclared
provider edges (repeated across files) plus one private Systemd library context.
No build-path leak or unresolved public ABI provider was reported. Exact added
package relationships are in config/native-package-metadata.json. Add final
Systemd -> Util-linux explicitly after the book-order bootstrap, and retain
Util-linux's measured Systemd/udev linkage. Version constraints must agree with
the frozen installed provider versions; a graph alone is not solver evidence.

The remaining library finding is /usr/lib/systemd/libsystemd-core-261.so needing
libsystemd-shared-261.so. Its actual systemd executable directly needs both and
has RUNPATH=/usr/lib/systemd; the native dynamic loader --list resolves both to
that directory. Preserve that explicit execution-context evidence rather than
claiming every private library is independently loadable or globally adding the
private directory to ld.so.conf. Native boot still required in H12.

Upgrade metadata as new +toddy1 versions using accepted native Dpkg, retaining
old archives/records. Re-extract the exact original payload; do not rebuild or
retime compiler/libc tests, modify installed package databases by hand, or remove
.la files only from the live tree. Register all packaged regular /etc files as
conffiles, remove obsolete staged Libtool .la archives consistently, reject
ownership conflicts before install, and preserve owner-modified configuration.
Record predecessor archive/source hashes and compare actual post-upgrade payload,
conffiles, missing/duplicate ownership and dependency audit. Generated state
(account databases, indexes, machine ID, package DB) needs explicit separate
classification; native Linux API headers/layout must receive final ownership.
DT_NEEDED closure does not cover executable scripts, dlopen, tool/data/plugin
requirements or licenses. Those must be audited independently before H07/G1.

Evidence: .local/logs/h07-elf-101.json, actual native loader command
`chroot /mnt/lfs /lib64/ld-linux-x86-64.so.2 --list /usr/lib/systemd/systemd`,
frozen LFS 13.1 package management section and ADR-0008/0035. This ADR does not
claim any metadata upgrade, full ownership or final closure has passed yet.

### Exact bootstrap-remnant audit

Read-only ownership audit found 2026 unowned regular/symlink paths, zero duplicate
owners. They include Linux API headers awaiting ownership; generated account/
service state; merged-/usr/loader aliases; and obsolete bootstrap files. Native
GCC is x86_64-pc-linux-gnu with no cross-triplet search path. Quarantine only the
exact unowned x86_64-lfs-linux-gnu subtrees/programs plus obsolete Xz library/GDB
helper and old Python files absent from the frozen 3.14.10 archive. Preserve
per-file hashes/links and same-target recovery copies; refuse if any path gains
an owner or disappears before execution. Do not glob-delete unknown files.
Native C++ threads, Perl threads, Python imports/trust and Xz version must still
pass. Other unowned paths need explicit layout/generated-state ownership review;
this cleanup alone does not close the audit.

Final filesystem-layout package records the existing merged-/usr aliases,
loader aliases and sh link, with standard empty FHS directories. It deliberately
excludes mounted API filesystems; those are runtime-generated mounts. The
separate lfs-build-support package takes ownership of the exact existing
section 6.2 config.site. Both are synthesized from frozen LFS computer
instructions, retain LFS MIT notice plus book URLs/version/archive hashes and
recipe provenance, and import no foreign binary/source archive. Source kind is
explicitly book-derived-versioned-recipe. Original project licensing decision
D10 remains open; this does not grant a license to all original Toddy code.

Frozen LFS chapter 8 cleanup explicitly removes .la files under both /usr/lib
and /usr/libexec because this base has no expected libltdl-loaded libraries.
Metadata upgrader covers both namespaces, changing archives and installed files
together. The same book section removes the obsolete cross-triplet compiler;
our exact-list quarantine preserves recovery instead. Do not apply its broad
/tmp cleanup while any build/test process is active. Preserve the build-only
tester account until source builds finish; image assembly must exclude it and
all test/source/temp data, rather than treating the build root as distributable.

Before upgrading, repeat the actual ELF audit to include accepted additions
built after the original 101-package review. Derive only unambiguous measured
missing direct-provider declarations, record the exact input report/derived
edges, and require every provider installed with its frozen version. Any missing
provider, build path, ambiguous owner or loader condition other than the exact
reviewed Systemd private context stops before upgrades. Final repeat still must
have zero unqualified findings. This is measured metadata completion, not a
license/tool/dlopen closure substitute. Re-run the unchanged complete ACL suite
after final Coreutils and require cp.run PASS; its earlier bootstrap failure is
not permanently waived once the missing capability exists.

Payload verification before upgrades checked 58815 recorded files/links, zero
missing files/duplicate owners/modified registered conffiles. Only the already
qualified shared Info index hash differs. Final upgrade postcheck must verify
all recorded hashes, links, modes and owner/group again, require no unexplained
finding and confirm Info index has no package owner. It also requires native
APT dependency check and a clean configured package database; successful archive
creation alone is insufficient.

The final unowned-file audit separately records generated Shadow accounts/locks,
ldconfig/Info/machine identity and Systemd presets pointing to actual owned unit
files. Four explicit bootstrap identity/network/filesystem configurations remain
H08 work. Every other unowned usr/etc/lib64 regular file/link must be explained
by actual package ownership after API/layout/cleanup steps; unknowns fail the
final postcheck. This is not a claim that every mutable state file belongs to a
binary package or that H08 configuration has already passed.
