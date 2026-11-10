# ADR-0216 — CUPS local stage and required prefix correction

Status: legacy-layout local stage accepted; native installation blocked.

## Source-backed diagnostic selection

[Independent classification](../evidence/B02-cups-SNMP-classification.json)
binds the exact original `testsnmp.c` hash to the retained actual output. With
argc1 its argument loop does not run, the host remains null, and usage exits1.
Socket creation occurs inside that argument loop. The original default-community
positive result and usage exit remain retained; no remote SNMP test passed.

Four collector tests exercise the real collector function from the recipe.
They preserve all ten original rows, select exactly nine successful local
programs and refuse a failed/missing/duplicate local program or a different
diagnostic outcome. SNMP remains explicitly unqualified. This is focused local
SDK coverage; full graphical-bus/server/network/driver printing tests are pending.

## Bounded first staging and consumer

After the independent owned MIT native installation, one logged staging-only
extension ran with the historical two corrections and failed finish4 retained.
It pinned the complete ten-row result digest, exact SNMP source, original ELF/log
snapshots and the four collector guards. No successful original test or main
compiler ran again. [Actual stage5](../evidence/B02-cups-legacy-layout-stage.json)
PID71476 exit0 installed into the private stage, linked/ran the first local IPP
consumer and collected evidence:273ELFs/846regular stage files,14,178,342bytes.
All273 compiler ELF hashes and11result/log hashes remained unchanged. The raw
SNMP usage1 is present alongside the nine local successes in the aggregate.

## Concrete layout blocker found before native promotion

The recipe incorrectly added `--prefix=/usr`. The frozen BLFS13.1-systemd
`pst/cups.html` omits that override. The selected generated configure sets
`ac_default_prefix=/`; its versioned `cups-directories.m4` maps that root prefix
to `/etc` and `/var` and the execution prefix to `/usr`.

Actual legacy Makedefs instead embed sysconfdir `/usr/etc`, localstatedir
`/usr/var`, SERVERROOT `/usr/etc/cups` and spool `/usr/var/spool/cups`. The stage
roots are usr/run. A local IPP consumer does not validate these service paths.
Do not promote this stage or relocate its files to disguise compiled defaults.

The canonical future recipe now explicitly uses `--prefix=/`, matching the
frozen default. This changed input requires a corrected affected build and local
tests; the correction has not yet been built. Preserve all legacy compiler,
stage, source, raw failures and successful results as distinct historical inputs.
No native CUPS package, scheduler activation, printing or GUI acceptance exists.

## Resource-aware next slice

Legacy tree allocation is84,209,664bytes and stage16,998,400bytes. Existing scratch
free611,934,208bytes leaves75,063,296bytes above the fixed512MiB reserve, so a second
complete source-layout copy plus compiler/stage cannot fit. Do not lower reserves
or remove the original compiler/stage.

Adapt the already qualified kernel metadata-COW preparation/isolation approach to
an exact CUPS-only work path: same authenticated read-only source as lower input,
private upper/work, metadata ownership promotion and only the merged source tree
exposed to UID101. Qualify source write denial, private copy-up, unchanged source
bytes/metadata, capabilities/NoNewPrivs and restart custody before compilation.
This reuses the proven build-isolation mechanism for the concrete source-layout
space blocker; it is not a change to desktop architecture. CUPS-specific COW
support and its corrected build remain pending, not accepted by analogy.

Keep the exact generic harness digest unchanged for prior qualifiers. Preserve
one guest writer, target16GiB/host/scratch gates, full-root native transactions
and deterministic resource monitoring. Native installation will also need lp
UID9/GID9 and lpadmin GID19 ownership review; actual names/IDs were inspected:
lp group9 exists, lp user9 and lpadmin group19 are absent. Do not grant any user
administrative group membership or activate a print service from SDK acceptance.
