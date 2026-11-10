# ADR-0214 — CUPS private build and resolver checkpoint

Status: producer parked after two failed corrections; no CUPS package acceptance.

## Frozen source and private build

CUPS2.4.19 uses the frozen source with SHA256
820984b12a67f98705785aae2dd1347fe0ac097828001d4583ff64574aed6389.
The frozen BLFS13.1-systemd `pst/cups.html` is the recipe reference. The selected
source already contains the book's IPP pointer correction; assert its presence
instead of applying an obsolete transformation. Replace only the private desktop
template's HTML viewer with the selected Firefox candidate.

Read-only source and a private writable source-layout copy live in the existing
Doxygen scratch. Preserve the original cache and fixed reserves. The full default
component build retains GnuTLS/PAM/USB, compiled lp/lpadmin policy and core Settings
dependencies. Planned unprivileged staging substitutes tester ownership only;
native promotion must separately review actual accounts, spool and configuration
ownership. CUPS filters and real printing remain unqualified.

## Actual result and bounded corrections

[Actual receipts and retained log digests](../evidence/B02-cups-producer-failed.json)
show main compilation succeeded. `make unittests` also executes programs; its
HTTP test failed resolving the sandbox hostname. Array/file completion footers
exist; other positive output without individual exit receipts is not accepted
as a completed standalone test.

Recovery2 failed its own incorrect four-footer assumption before tests/staging.
Recovery3 corrected that assumption but failed its private hosts assertion:
the extension ran before generic `/etc/hosts` initialization and was overwritten.
No new tests, stage result, native package, server activation or GUI acceptance.
Retain all three failed jobs and compiler bytes. Two failed corrections park this
producer; do not dispatch an unchanged fourth attempt.

## Narrow prevention and next branch

The generic isolation harness stays byte-identical: existing package qualifiers
pin its digest. A CUPS-only profile requires that exact digest and adds public
loopback names after generic private hosts initialization. It changes neither
target/global hosts nor external DNS/network policy. Job receipts pin the wrapper,
implementation and base harness. Three host tests include actual execution of
the effective initialization fragment; these are fixture evidence, not a guest
HTTP test pass or permission to reset retry counters.

Advance the independently qualified Kerberos metadata-only branch. Any later
CUPS reopening needs an explicit bounded extension with historical budgets,
actual postconditions and no compiler/source or already accepted test replay.
