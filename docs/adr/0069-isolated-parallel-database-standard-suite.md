# ADR-0069: Run the complete corrected database suite in a private target view

- Date: 2026-11-07
- Status: Isolation and input guards verified; complete corrected run active
- Scope: H07 test execution only; production handoff remains pending

Both diagnosed repmgr groups now pass all their original cases (ADR-0067/0068).
The original full standard attempt is still collecting later results, but its
two recorded failures prevent acceptance. Waiting for that attempt to finish
before starting a corrected complete run would serialize two long test jobs.
The measured guest has ample available memory and storage, and the tests spend
substantial time in their upstream waits. Run one complete corrected attempt in
parallel, with explicit isolation, while retaining the original diagnostic run.
Do not combine partial passing groups into a purported successful full run.

The copy reuses the hash-verified native compiled checkpoint, not host binaries:
460 checkpoint files match the root-protected seed; all 483 Tcl files match the
frozen archive, maintained env012 patch and reviewed test142/repmgr007 patches.
The real db_repsite adapter is the exact executable which passed all eleven
multi-process cases. An additional root-protected manifest records 10,208 input
files, including wrappers, headers, libraries, sources and the full-suite entry
point. No installed file is copied into a replacement package at this stage.

The private source is bind-mounted onto its original canonical path only inside
a new mount namespace. This preserves generated libtool wrapper paths without
editing wrappers or exposing the original source to private test writes.
Separate PID, IPC and network namespaces isolate test process IDs, System V IPC
objects and local replication ports. Loopback is enabled. Both proc views are
mounted for the new PID namespace; tmp, var/tmp and shared-memory paths have
private backing. Shared memory retains a fresh tmpfs rather than changing the
filesystem type. The frozen Tcl signal helpers target their recorded child PIDs;
the review found no broad killall/pkill invocation in those Tcl inputs.

The [util-linux unshare manual](https://man7.org/linux/man-pages/man1/unshare.1.html)
documents the namespace options and private mount propagation. The
[Linux PID namespace manual](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html)
describes visibility and cleanup when a namespace's init process exits.
The actual builder uses unshare 2.39.3. Native probes measured distinct namespace
identities, the canonical source mapping, private temporary directories and the
effective tmpfs filesystem. The original mount view/source and temporary marker
absence were checked outside the namespace. No new kernel or ISO boot is claimed.

## Corrected isolation and actual execution

An initial copy at db-standard-yc87i9pi isolated dev/shm by binding an ext4
directory. A subsequent mount audit caught that mismatch against the original
tmpfs. The test process group was deliberately stopped, without stopping the
original driver. Captured test exit -9, driver exit 1 and all 10,208 input hashes
unchanged; its partial output remains unaccepted and preserved. This was an
environment correction, not a test assertion waiver or observation-timeout retry.

The replacement preflight initially treated findmnt's two stacked tmpfs rows as
one scalar and refused before standard execution. It now checks the effective
filesystem with native stat -f, which resolves the top mount rather than confusing
stacked mount records. Native Python probes use -B to avoid installed bytecode
writes. All namespace setup and probe code is versioned under scripts/build/h07.

The corrected full run started at 01:25:22 UTC in
/mnt/lfs/sources/recovery/db-standard-nfv62s4o, guest driver PID 1107192.
CuTest exited zero; log SHA-256
51763da1955dcca28f53b8bc863cec7f834179ddd994beda4b55f1cc4ab025d2.
The unchanged complete run_std then began and reached Env012 with zero FAIL
lines at 01:26 UTC. The original attempt remained active in Rep079 with its same
two known failures. Neither standard suite is accepted from this observation.

Input manifest SHA-256:
336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9.
Driver SHA-256:
e606c595c43fb024f44a0af2610990d04b0a0f3cc7d0d85488ddd2cbebb5b981.
Isolation shell SHA-256:
cb90e3143b3ae49dbf9f5274cada9ee7b8f9ecc79ba9ae8034203efe80d1c103.
Isolation probe SHA-256:
1db63b29fee0fb87b7efb0770a78797e13eafbccfeedcbfc9bdcf90b82fb7185.

Raw launch .local/logs/h07-parallel-standard-start.json SHA-256:
bd592199ad5073757cf5315ad1c928e2e4d27e01b6dfee0dffa80f0521ca5d70.
Raw observation .local/logs/h07-parallel-standard-progress.json SHA-256:
79b9014d0ff537ad4b42c6ba99c82559d7df57397a3df44b6ba270f4077c8e47.
The latter includes the interrupted initial attempt and exact reason. Its failed
preflight report is separately retained with SHA-256
329e2499e92cdfcd9fd1230ad7ed77b6fb2feff54e7d1baa2d64101c16c2b3df.
At that observation the target had 135,789,473,792 available bytes and the host
355,178,975,232, exceeding the recorded reserve. No additional VM was allocated.

## Durable result and acceptance boundary

berkeley-db-isolated-driver.py verifies all input hashes before and after the
actual subprocess. It captures the exit code and full reports, requires the same
strict Tcl complete-suite sentinel/no-FAIL conditions as the existing recipe,
and protects successful source/report evidence from the test user. A 48-hour
outer timeout is a failure bound, not an estimated duration; each test retains
its upstream timing and assertions. No driver branch installs or accepts a
package. Missing terminal output or a live PID remains unfinished work.

Actual guest negative checks rejected an outside fixture path and a wrong input
manifest digest before starting a native test subprocess. Raw report
.local/logs/h07-isolated-driver-rejections.json SHA-256:
3b9f855597ef06d6c75adc84ce1ecde6bc43ebdb7df040af52daad2f27a73e74.
Local regressions also reject changed native/namespace inputs and a redirected
source with identical bytes. These guards do not replace the running native suite.

The earlier session-specific serial-retry supervisor (host PID 942158) was
disarmed while it was still waiting, to avoid scheduling a redundant attempt.
Its state records supersession; do not restart it unchanged. The original
success-only supervisor may only reject the failed original result.

Before production handoff, inspect the original terminal result and installed
change audit, validate the corrected complete result against its protected
inputs/frozen sources, and implement/validate the production handoff under the
normal exclusive recipe lock. Production build, packaging, native transaction/
reopen/rollback checks and APT remain pending. No partial log, combined set of
isolated cases, timeout or prepared script can mark Berkeley DB or H07 complete.


## Independent completed-result verifier

scripts/build/db_standard_result.py is a read-only gate for this exercised
recovery profile. It requires both actual exits zero, no running marker/live
producer, protected reports/source, the pinned driver/isolation/entry/helper,
all execution input hashes and every native checkpoint/Tcl reference entry in
the protected input manifest. It independently reconstructs all 483 Tcl files
from frozen archives/patches. The upstream success line must occur exactly once
immediately before its final completion timestamp; the strict stdout sentinel
must be final, without unexpected output. Namespace evidence must demonstrate
four distinct private identities and tmpfs shared memory. No branch installs a
package or writes a success marker.

Actual guest probes with verifier SHA-256
0ea93792ddb952197810867dc8c95a935e287f85e0d3907bc5642637c24e0cc1
rejected the still-active corrected run, the interrupted first run and an
outside source path. Raw .local/logs/h07-db-standard-result-rejections.json
SHA-256: 5a2ba8210c0b4b865a62aa481b05ad142b6ecbe066fc45119a9cfbe6e79cb070.
Two local regression methods exercise truncated/failed/duplicate summaries and
incomplete exit/input/producer profiles; all 152 local checks pass. A positive
complete native result has not yet been available and is not claimed here.

The Tcl reference verifier now returns its compared hash map, and the native
input manifest must contain that exact map. Repeated host fixture validation
passed 483 files, idempotence and six negative cases; current raw report SHA-256
366e9fbe4b0e1499750b9975f3372cd84d131c89bf26b164a7f3bc5c86b383c5.
The h07-db-fixture-preflight.json convenience path has been replaced by this
new observation since ADR-0067. Future runs preserve both previous and new
reports with their SHA-256 in the filename; the prior cited digest is historical,
not the current convenience-path contents.

At 01:40 UTC the original run had reached recovery Recd001 (block 25/27), with
the same two failures. The corrected complete run reached Fop006.80 (block 4/27)
with no failures. Both drivers remained live and lacked terminal exit files.
Raw .local/logs/h07-db-standard-progress-<sha256>.json observation SHA-256:
60c106e5b52cca43ed3b3f9eac394a72697dd6d14d9ca133a82678f7bdd3895d.
Group position is not a time-weighted completion estimate.


## Prepared production handoff

The read-only result gate now has a separate production path, prepared but not
positively exercised: db_standard_handoff.py prepare takes the same exclusive
build lock, requires the exact original terminal failure and zero installed
changes, validates the complete corrected result, preserves original reports
in a new root-private history directory and creates a root-private nomination.
An existing nomination is never overwritten. Unknown failures, unfinished
runs, truncated output or a nonempty installed-change manifest require diagnosis.

berkeley-db-verified-production.sh can consume that nomination only as a child
of the recipe PID recorded by run_step.py, with its exclusive lock still held.
It revalidates protected original reports and the complete corrected result,
then binds the tested source to its canonical path in a private mount namespace.
Production build, staging, normal package installation and the existing native
postcheck still run against the actual target, under the normal installed-file
audit. No handoff code creates a success marker or accepts H07.

The former finish-inner script was split at the production boundary. Its
complete standard-suite commands and production commands are byte-for-byte
preserved in the two resulting script bodies. Both ordinary fresh and recovery
recipes still execute the complete suite before production. This avoids
maintaining a different production configuration for the isolated-result path.

Actual guest rejection probes refused prepare while the original runner held
the lock and consume outside the production dispatcher. No nomination or stage
was created. Raw .local/logs/h07-db-handoff-rejections-<sha256>.json SHA-256:
3bf58b99ad3121f69ad7c7271b11a43ea72d914a80e0744fa377c9aa2475f40e.
Two local regression methods reject changed/unknown/incomplete original results
and replacement of an existing nomination. The actual positive handoff,
production compilation, package installation and postcheck remain pending.
