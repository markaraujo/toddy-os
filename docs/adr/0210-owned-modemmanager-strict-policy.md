# ADR-0210 — Owned ModemManager with strict factory policy

Status: accepted for the scoped B02 SDK/package qualification.

## Decision

Use the frozen BLFS13.1-systemd ModemManager1.24.2 source, with default plugins,
MBIM/QMI, GI, Udev and Systemd integration. Keep strict polkit authorization,
inactive/other-session denial, and the default disabled AT-command D-Bus feature.
Only the book-supported QRTR/completion switches are disabled. No implicit
service enablement or privileged firmware operation is performed by installation.

Use ADR-0209's qualified read-only source/private worker and location-aware
staging. Actual compiler worker inode5725 is on the existing Doxygen volume;
the source fingerprint and original Doxygen cache are retained. This slice has
no new cold-restoration acceptance.

## Evidence and corrections

[Original build/stage](../evidence/B02-modemmanager-stage.json):491ELFs,
220regular stage files,29original programs/588TAP cases passed. Two serial PTY
tests and one session-bus stub test are deferred, not passing. Defaults and all
auto plugin choices are verified against actual Meson build options.

[Native installation](../evidence/B02-modemmanager-install.json) recipe0 installed
264changed paths. Its own GI test wrongly assumed a nullable APN setter; the
installed public GIR declares no nullable annotation. Corrected tests assert
TypeError, retained prior APN and two fresh object recoveries; the C consumer
separately checks actual NULL reset and Unicode properties.

The second own assertion expected an unknown-option error. Upstream cli/mmcli.c
calls g_option_context_parse with a NULL error and ignores its return, continuing
to a missing-bus error. Preserve that CLI input-reporting limitation. The final
negative test requests the modem list with an absent system bus, checks the
explicit refusal, then two fresh version recoveries. No upstream patch or claimed
unknown-option guarantee. Final verify-only3 recipe/post0/0, root changed0; no
reinstallation. Failed receipts and both source-backed corrections remain visible.

Actual installed UID101/NoNewPrivs/private-device/no-route C/GI/CLI/daemon-version,
stage payload, library resolution, strict static policy and APT checks passed.
Static policy does not prove running-session authorization. Running daemon,
hardware/modems, cellular connection, firmware operations and Settings GUI are
unqualified. The reference desktop must still work offline without any modem.

## Resource custody

Before source/install dispatch, exact closed GOA/MBIM promotion usr duplicates
were retired after archive/record/installed/original-workstage verification:
[custody](../evidence/B02-protocol-promotion-custody.json). After actual stage
allocation exceeded the fixed reserve gate, the independently verified closed
Shell promotion usr duplicate was likewise retired:
[Shell custody](../evidence/B02-shell-promotion-custody.json). All installed-root
comparisons changed0; source/compiler/workstage/archives/DEBIAN remain. This is
duplicate retirement, not source deletion, trim, reserve reduction or a rebuild.
