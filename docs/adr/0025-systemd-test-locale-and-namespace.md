# ADR-0025: Test Systemd in UTF-8 and retain the chroot namespace exception

- Status: Locale correction verified; complete retry/native installation pending
- Date: 2026-11-06
- Scope: Frozen LFS 13.1-systemd section 8.77, Systemd 261.2

## Evidence and decision

The initial full suite ran all 1862 tests: 1824 OK/33 SKIP/five FAIL. No package
was staged or installed. Four failures are byte/terminal-width assumptions in
POSIX locale: test-format-table and check-help-systemd/systemd-creds/systemctl.
The format test expected UTF-8 ellipses, but POSIX rendered ASCII dots; help
width checks counted UTF-8 bytes incorrectly. All four unmodified tests passed
in a focused LC_ALL=en_US.UTF-8 retry. Preserve the initial full raw reports,
repeat the entire suite in that installed locale, and classify every result.

The remaining initial failure is the book-known chroot test-namespace. Actual
failure is test_process_is_owned_by_uid, test-namespace.c:391, EPERM with SIGABRT.
The strict classifier permits only this exact identity/location/cause after a
complete 1862-unique-test run; unknown failures, timeouts and incomplete reports
stop installation. Keep raw nonzero exit and explicit all_pass=false. Other
book-mentioned failures are not preapproved or silently excluded.

H12 must rerun this test under the native kernel/booted OS before G1. It is not
a demonstrated native-system success. Do not weaken host/guest global security
to make chroot namespace assumptions pass. Preserve all 33 skip reasons and
audit required native functionality separately; unsupported optional hardware
features are not claimed installed from a skipped test.

## Alternatives and consequences

Deleting tests or changing expected ellipses would conceal the environment
error. Repeating unchanged POSIX tests would add no information. A UTF-8 suite
plus strict known-chroot classification follows the measured source behavior
and the frozen book qualification, with actual booted namespace validation
still required before acceptance of G1.

## Sources

Frozen LFS 13.1-systemd section 8.77 and actual Systemd test-format-table.c,
test-namespace.c, help-check output and preserved full Meson JSON/text reports.
