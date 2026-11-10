# ADR-0195 — Owned GNOME Terminal and corrected reference schemas

Date: 2026-11-10
Status: Accepted package/userspace slice; actual graphical acceptance pending

Frozen GNOME Terminal3.60.0 archive SHA256
`6c006523d2c21282fd62c64fc44f63546aaa216e66eb439b8129af68db11df7c`,
BLFS13.1-systemd `gnome/gnome-terminal.html` page SHA256
`88e7839f2585a1258fb78aad1be2d64fb0871e10349e41d8d101de76c870c3f9`.
Use owned GTK3/VTE2.91/libhandy, Shell search provider; optional Nautilus extension,
docs/debug omitted. No framework/font forced and no silent foundation upgrade.
Initial setup failed at missing build-only xsltproc; ADR0194 supplied that exact
SDK. Guarded build2 reused the failed configuration directory, preserving its
log and changing only the fresh-directory assertion. No prior app compile/test/
stage/install existed. Compile/original regex/stage passed;71ELFs retained.

The own private DConf consumer first expected an empty list after reset. Actual
ProfilesList overrides its parent's default with a stock UUID. Correct only that
assertion to compare the actual declared default, preserving the failed probe.

The frozen book requires five external proxy paths under `/org/gnome/system/`.
Initial preparation omitted this correction. The reference schema cache is a
separate installed file, not embedded in code. Probe3 recompiles only this cache
using a private patched external schema; ships the exact source patch and keeps
immutable source, all71compiledELFs and original regex evidence unchanged. Only
that staged cache and the patch changed;12schemas/146key type/default/range
contracts preserved. Future preparer applies the same five book edits before
build, recording before/after hashes. No parser/ABI/library replacement.
Corrected cache SHA256
`4dcfd88b0cb247d76075060923020b286fe22075992377c9fad51f55fe4debb5`.

Actual userspace probe verifies client3.60.0, the exact unknown-option diagnostic,
private Unicode/navy profile writes, malformed boolean refusal with preserved
state, persistence through two new session buses, reset to schema defaults and
unchanged system-font selection. These are ephemeral synthetic user preferences;
no desktop branding or owner's configuration is claimed installed by this test.

Initial native package installed0/346entries, post1 because its test chroot lacked
an accessible `/dev/null`. Preserve that real failure and package/archive; never
replay installation. A private mount/PID/network namespace now supplies only
null/zero/random/urandom in temporary `/dev`; no global permission/device change.
The source also unconditionally installs addon AppStream metadata while the
Nautilus extension is disabled. New controlled metadata revision2 first verifies
all346installed entries and retained archive, extracts identical staging, removes
that one unsupported addon record and retains bundled leading notices/full LGPL2.1
text alongside authenticated root GPL3/GFDL1.3. Preserve the existing per-file
license identity rather than flattening bundled conditions to one SPDX claim.

Revision2 recipe/post0/0 changed39paths/376owned entries, with339nonlegal runtime
entries identical and the unbuilt addon metadata absent. No code/library/source/
original-suite reinstall or rebuild. Actual installed UID101/no-route client,
private DConf/refusal/persistence/recovery/font checks, five reference paths,
shared VTE/libhandy and APT checks passed. This executes the target userspace in
the builder VM/private namespaces; it is not a cold-boot GNOME or physical test.
The runtime dependency set does not force xsltproc/fmt/FastFloat build SDKs.

[Source, failures, exact contracts and native proof](../evidence/B02-gnome-terminal-install.json).
Current archive SHA256
`7431df2b9fcea4f345b558fe6ea85ffc8d1295d966f8ba5f47aa9581c3a89800`;
raw evidence SHA256
`5b4662111a90090fcbcfd11c0cc35b101a4dd3c032ec83e725f37dc4d4e3a258`.
Stock shared schema-cache union, actual window/focus/shell PTY/Stop/recovery,
readability/responsiveness and integrated login/desktop remain required B02 work.
No global schema cache, account, credential or policy was changed by this slice.
