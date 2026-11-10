# ADR-0213 — Kerberos local validation and aggregate collector checkpoint

Status: build/stage aggregate recovered metadata-only; native package/install pending.

## Selected source and isolated work

Use the frozen BLFS13.1-systemd MIT Kerberos1.22.2 with all three required
upstream/security/OpenSSL4 patches. [Actual guest preparation](../evidence/B02-mitkrb-input.json)
matches the earlier host patch application. Source is on the qualified existing
Doxygen scratch through a read-only alias; root write is refused EROFS. Original
Doxygen cache fingerprint unchanged, new private worker inode12699. No target
reserve reduction or foundation rebuild. No new cold-restoration acceptance.

The recipe uses system com_err/ss, book internal-verto choice and disabled RPATH.
Its own uninstalled consumer adds only -rpath-link to find the staged transitive
support library; no undefined-symbol relaxation or embedded runtime RPATH.
Staging explicitly substitutes normal INSTALL_PROGRAM for INSTALL_SETUID, so
ksu is0755 without chownroot/setuid. This was reviewed before staging; no installed
privilege or assistant administration policy changed. Kerberized su is not an
accepted privilege mechanism, and the revocable executor remains independent.

## Actual execution and explicit failures

Main job1PID45040 compiled and passed the original selected crypto check-unix.
The shared GSS check-unix make target also depends on the complete Python realm
suite and failed before local C tests because runenv.py was absent, exit2.
The first resume dispatcher correctly refused its own wrong expected-exit1
assumption before creating a job; actual state was inspected, not replayed.

Finish2PID58431 reused compiler/crypto and ran five unchanged original GSS C
programs with their original RUN_TEST environment. It passed the original DB2
default tests and staging, then its own staged C linker failed on the transitive
support-library search. Collector3PID61513 fixed only that search; actual local
principal parsing, MEMORY-cache reopen/destroy, required-realm/absent-principal
refusals and two recoveries passed. No owner credentials, tickets or network
authentication were used. Compiler/test/stage bytes and logs remain retained.

The final aggregate assertion incorrectly expected20 report rows. Actual DB2
emits24 rows for20 unique test IDs: early cases separately report btree/hash/recno.
Case20 is skipped because the stock dictionary is small; case12 is explicitly
excluded by the frozen book. These are not passing cases. No full Kerberos realm,
Python, enterprise authentication, daemon, Settings GUI or hardware suite passed.

[Failed collector evidence](../evidence/B02-mitkrb-collector-failed.json) preserves
actual exits2/1/1, reports, successful own C output and original byte manifests.
The aggregate result file is absent; no package archive, native install or owned
Kerberos runtime is accepted. A passing C consumer does not convert the producer
exit1 to success.

## Budget and continuation

Two corrective executions failed (own linker, then aggregate row count). Park
this producer and advance eligible CUPS work within B02. The fresh collector code
now checks exact unique IDs, but has not been rerun in the guest. Reopen only with
independently qualified24-row/20-ID parsing and one logged bounded metadata-only
extension retaining historical attempts. Reuse successful logs/API output and
unchanged compiler/stage; do not repeat fetch, source preparation, compiler or tests.
The persistent local failure ledger and continuation card own the exact next action.

## Receipt namespace regression and byte-exact recovery

The recently added fresh-prerequisite selector reused the preparer's receipt
variable. Consequently, actual MIT worker state was saved over the predecessor
Libgtop success receipt rather than its own worker receipt. Installed packages,
sources and compiler bytes were not written by that receipt operation.

[Actual recovery](../evidence/B02-mitkrb-worker-receipt-repair.json) relocated the
real mounted-worker record and restored the original Libgtop success JSON from
the retained controller output. Re-encoded bytes match the pre-existing public
receipt SHA256 exactly, not a reconstructed or rerun success claim. The repair
is guarded by the exact controller digest, expected original digest, actual
worker inode12699/mount identity and unique recovery journal; never replay it.

All three affected preparers now separate native-prerequisite and worker receipt
variables. A fail-closed namespace guard checks every worker receipt write.
Four focused tests refuse acceptance-record replacement, another worker's record,
traversal and unknown ownership, and allow only the exact own receipt. This is
metadata recovery and prevention; it does not accept the parked MIT collector.


## Bounded metadata-only recovery after independent CUPS work

CUPS source/build work advanced an independent eligible branch, retaining the
historical MIT failure budget. [Independent parsing](../evidence/B02-mitkrb-parser-qualification.json)
used the exact retained actual guest DB2 log, matched its pre-existing digest,
qualified24rows/20unique IDs and refused missing/unexpected IDs. This was host
parsing evidence, not another run of the original suite.

One logged bounded metadata-only extension then ran only the final Python
collector, never shell/compiler/test/stage/API commands. [Actual metadata4](../evidence/B02-mitkrb-stage.json)
PID67706 exit0 compares all897 ELF/132stage entries with the original maps, plus
seven original log/consumer digests unchanged. Canonical compact JSON digests
match the published failed-collector maps. Its unique before/retained receipts
must not be replayed. Fixed scratch reserve is checked before publishing results.

The local build/stage aggregate is now qualified. Case20 remains skipped and book
case12 excluded. No native package/install, realm/ticket/network authentication,
service, Settings GUI or physical acceptance follows from this metadata result.
Next is controlled native packaging with exact source/patch/recipe and dependency
qualification, installed local refusal/recovery checks and full-root transaction.
