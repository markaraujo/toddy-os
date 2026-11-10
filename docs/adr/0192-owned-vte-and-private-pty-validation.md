# ADR-0192 — Owned VTE and real private PTY validation

Date: 2026-11-10
Status: Accepted implementation choice; native package result recorded separately

## Context and choice

B02 selects frozen BLFS13.1-systemd `gnome/vte.html` VTE0.84.1 for
GNOME Terminal3.60.0. Source SHA256
`9f73468982a339cd1eb942beb7d348a5564c9ed48473ad1690c791f8474916ec`;
book page SHA256
`700b8d471a5f2d72c6cb623a0e823e04c8abc8074222cd71ad40c46daf4fc63d`.
Keep GTK3/API2.91, accessibility, FriBidi, ICU, GnuTLS, GI/Vala and Systemd.
The GTK4 variant has no selected consumer here; demo app, Glade, documentation
and experimental terminfo are omitted through supported options. There is no
version upgrade, compiler network access or foundation replacement.

The shared library uses header-only fmt and FastFloat. Retain both authenticated
source archives' license texts and leading runtime header conditions in the VTE
package, alongside VTE's GPL/LGPL/Xterm/CC notices. Native runtime dependencies
include actual owned shared libraries, without forcing the two header SDKs into
the runtime root. Dynamic NEEDED entries are reviewed against owned versions.

## Shell behavior

Upstream `src/vte.sh.in` replaces scalar `PROMPT_COMMAND`. Apply a narrow staged
change preserving an existing scalar as the first Bash array entry and appending
the ordinary VTE callbacks. Preserve upstream array and empty-prompt handling.
Ship the exact source patch. Both profile hooks are native conffiles; do not
rewrite user dotfiles, install a shell framework or require a font. A real
interactive Bash consumer checks the prior command and visible prompt text.

## Actual validation and recovery

The isolated build produced134compiled ELF files and125staged regular files.
All18original registered programs passed, including parser/UTF8/reaper and shell
URL encoding. Original log, exit and source remain retained.

The first own consumer failed PTY creation because the compiler sandbox exposed
no terminal allocator. Add a new private `devpts` instance only for this exact
VTE input, with a private `ptmx` alias; never bind existing guest/host terminals.
Probe-only2 then reached real PTY creation/resize/UTF8 but failed text matching.
Frozen `src/pty.cc` enables `TIOCPKT`; the own reader incorrectly interpreted its
zero control prefix as a string terminator. Correct only that consumer's bounded
packet decoding and compile it in new `probe-3`. This is separate from the device
failure. Preserve both failed jobs and the original consumer binary.

Probe3 exited0 with all134compiled and125staged file hashes unchanged from
before probe2. Actual regex substitution/refusal, PTY geometry/UTF8, three normal
shell cycles, process-group identity plus SIGTERM Stop, fresh PTY recovery,
interactive owner-prompt preservation and GI version passed. These are library,
PTY and shell checks, not graphical widget/focus/GNOME Terminal acceptance.
Native installed-package verification uses a new mount/PID/network namespace
and private temporary `/dev`/devpts, UID101, and confirms namespace teardown.

Shared isolation impact is limited to the exact VTE source path; other compiler
profiles retain their existing device exposure. Run shell syntax, Python compile,
actual scoped runtime checks and repository `make check`; do not repeat unchanged
foundation/compiler/original suites. Native package proof and final GNOME gate
remain distinct and must not be inferred from this ADR.

Native install2/post0/0 changed254paths/468owned entries. Actual installed UID101
consumer, GI, APT audits, conffiles and all three source notice inventories passed.
The initial promotion selected failed initial job before recovery selection;
receipt proves recipe1/postnull/changed0 before any stage/package creation. New
install2 followed actual absence checks; there was no uncertain install replay.
[Native proof](../evidence/B02-vte-install.json); archive SHA256
`c9f8f81d46d0cf2c4945667ec6f00742ff9fa07548a61c105999944f1e92c907`.
Raw evidence SHA256
`8d9ad01d2877e4b8e1342f6b4e755aa582f0484208cad22782ec79ae3e22a43c`.
