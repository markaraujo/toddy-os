# ADR-0217 — Correct CUPS layout and bounded transient storage

Status: corrected local build/stage accepted; native package installation pending.

## Reuse existing isolation after verified promotion custody

Read-only measurement found closed native-promotion replicas that had not yet
been retired. [Actual custody](../evidence/B02-cups-prerequisite-custody.json)
qualified the exact QMI/MIT/GWeather-locations archive and record hashes,
installed versions, full promotion payloads, installed file/link bytes and
unchanged original source/compiler/workstage evidence before removal.

Only their closed promotion `usr` replicas were retired. DEBIAN, MIT run/var,
native archives, installed payloads, source inputs, compiler trees, workstage and
raw evidence remain retained. Full-root before/after snapshots were identical.
Actual reclaimed storage:39,673,856bytes in existing scratch and24,076,288bytes
on target. The custody receipt is complete; never replay it. Recovery uses the
retained matching archive into a new stage, never reinstalling accepted packages.

This measured recovery made the ordinary qualified private-copy build fit.
The proposed CUPS-specific COW adapter in ADR0216 is therefore unnecessary for
this slice and was not implemented or claimed qualified. The generic isolation
harness remains byte-identical. New worker `cups-layout-1`, inode4675, uses the
same Doxygen UUID/read-only CUPS input and preserved original cache fingerprint.
Optional exact existing-worker cold restoration is registered but cold untested.

## Correct prefix, actual first failure and narrow correction

The frozen BLFS13.1-systemd CUPS2.4.19 default root prefix is now explicit.
Generated Makedefs were checked before compilation: prefix/, exec_prefix/usr,
sysconfdir/etc, localstatedir/var, SERVERROOT/etc/cups, requests/var/spool/cups,
runtime/run/cups. This changed input required fresh affected compilation/tests;
the legacy worker, compiler, stage and all failures remain separate and intact.

Main compilation and testarray passed. The next original testfile program writes
large transient files in its execution directory. The0.1second/4MiB-margin
observer reacted after a burst had already breached the fixed512MiB reserve:
minimum504,696,832bytes, interruption true, recipe-15/job1. This first execution
did not maintain the reserve; it is not successful resource evidence. GNU make
removed the interrupted testfile target; free space later recovered without
fixture deletion to587,489,280bytes. No first stage or native installation ran.

Source inspection shows the no-argument test includes uncompressed/compressed,
random I/O, pipe, rewind, path and directory checks and reads `testfile.txt` with
477expected lines. The correction moves only its execution directory and exact
fixture bytes into the existing private1GiB tmpfs. Original program, arguments,
cases, object/link command and target remain; the private Makefile run line is
restored on success or exception. Two host fixture tests qualify preservation
and restoration, not the upstream result. No root/global temporary setting changed.

## Actual corrected resume and acceptance limits

[Corrected resume2](../evidence/B02-cups-correct-layout-stage.json) exit0 retained
the main compiler and successful array result, relinked only the target GNU make
deleted, then obtained the remaining eight local results and first corrected
stage/IPP consumer. No main compiler or successful array replay. Original logs,
raw first-result file and Makefile were retained/restored; pre-existing ELF
hashes unchanged. All nine selected local programs now have actual exit0 evidence.
Remote SNMP remains unqualified; legacy no-host usage1 remains in prior evidence.

The resume used a deterministic0.02second/8MiB-margin observer and a measured
stage allocation plus8MiB pre-stage bound. Minimum observed561,508,352bytes,
interruption false. Corrected aggregate:250ELFs/846regular stage files, actual
IPP Unicode/add/find/delete/absent-attribute/two recoveries0. Stage roots are
etc/run/usr/var, without usr/etc or usr/var. No printing, server/network/TLS
connection, scheduler activation, Settings GUI, hardware or native package claim.

## Native packaging next

Native promotion must select the corrected worker, bind exact original/resume
commands and retained source/ELF/stage/log identities, and preserve failures.
Review the frozen scheduler install rules for each service-owned directory and
configuration file. Current staging deliberately uses tester IDs only. Actual
target has lp group9, no lp user9 and no lpadmin19. Fixed locked service identities
and reviewed package ownership exceptions must be handled by the existing full-root
native transaction; never add ordinary users to an admin group or activate units
from SDK acceptance. Keep normal client config pointing at the local socket.

Target margin above16GiB is39,272,448bytes; stage allocation17,084,416bytes and
scratch free561,504,256bytes. Recheck actual headroom and native transaction gates;
scratch cannot accommodate a triple-sized promotion workspace now. Qualify another
closed target promotion replica if needed before native staging/installation.
All sources, compilers, old/new workstages and archives must remain retained.
