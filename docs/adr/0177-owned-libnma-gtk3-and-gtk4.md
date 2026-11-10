# ADR-0177: Owned GTK3/GTK4 libnma and scoped public type imports

Status: native library/selected SDK acceptance; stock schemas and GUI pending.

Reuse the frozen libnma1.10.6 official source, SHA256
`53a6fb2b190ad37c5986caed3e98bede7c3c602399ee4f93c8fc054303d76dab`.
Actual GNOME Shell50.4 dependencies.js requires NMA4 and modemManager.js imports
MobileProvidersDatabase. Build both GTK3 and GTK4 libraries, GI1.0/Vala, ISO codes
and advanced Gcr certificate support. Meson prefers the already owned Gcr4/Gck2
when its actual prototype check succeeds; installed dynamic resolution confirms
these libraries. Optional cellular provider data is omitted, not advertised as
working hardware support. No GTK/Gcr/foundation version upgrade is needed.

Initial ninja compilation completed194tasks/101ELFs. The own registry guard
incorrectly assumed no automated tests because src/tests contains16manual GTK
programs; actual src/utils registers test-utils. Preserve the initial failed job.
Run the one original test without rebuilding, then stage and run own consumers
through a new stage-only2 job on the same immutable source/work. All101previous
ELFs remained byte-identical,114regular files staged, actual original test passed.
The16manual executables were compiled, never claimed as opened or passed tests.

The GIR scanner reported syntax warnings for nma-ws headers. These are installed
C APIs: do not label all affected APIs private or claim complete GI coverage.
Both generated namespaces contain the selected public WifiDialog, CertChooser
and MobileProvidersDatabase types. Actual separate GTK3/NMA and GTK4/NMA4 imports
and ancestry checks passed, as did separate C/GTK ABI and libnm invalid-address/
recovery consumers. No widget instance/display/focus was exercised. Preserve the
scanner diagnostics and leave other binding coverage unqualified.

Initial native promotion guard failed before any root change because its generic
resume map referenced failed build1 instead of the actual passed stage2. Verify
absence of promotion/archive/installed package, add the exact stage2 receipt to the
map and retain strict source/script/artifact/original/consumer checks. New native
install2 recipe/post0/0 changed174paths and owns346entries. Actual installed GTK3/
GTK4/Gcr4/Gck2 library resolution, UID101 C consumers, default selected GI imports,
SDK versions and package audits passed. No compiler/original/stage replay.

Retain exact source named legal notices and leading source C/header conditions,
including GPL2+, LGPL2.1+ and QR generator MIT terms. Network/certificate/password
widgets remain untrusted-input consumers: no real credentials are used or exposed
by these type checks, and no certificate-validation bypass is introduced. Actual
permission UI/secret storage/invalid credential states remain native GUI gates.

Two installed nm-applet schemas need the existing controlled shared-cache owner
union before graphical acceptance. Keep current82schemas/623keys and user values
intact until that transaction is qualified; installing schema XML alone does not
prove the stock cache contains it. Continue GDM/GNOME Shell/settings integration,
then real widget navigation/focus/legibility/responsiveness and network/Stop/
persistence/recovery. [Build failures, unchanged binaries and native package proof](../evidence/B02-libnma-install.json).
