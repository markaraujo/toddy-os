# H07 remaining work: volume rather than package percentage

Snapshot: 2026-11-06 21:39 UTC. Native Dpkg reports 124 configured packages
against the current 126-package H07 plan. This 98.4% package count is not a
measurement of completed effort, test cases or remaining wall-clock time.

| Remaining work | Concrete volume / acceptance |
| --- | --- |
| Berkeley DB | Finish the complete standard suite; build/install the production variant and pass real transaction/reopen checks |
| APT | Build one package, run its upstream tests and exercise a real signed repository, upgrades, conffiles, tampering, HTTPS trust/name failures and recovery |
| Python command | Apply the prepared native Python command alias through owned/versioned package metadata |
| Bootstrap quarantine | Move 931 specifically reviewed unowned bootstrap paths into recorded recovery storage |
| Package closure | Review/normalize metadata across the final 126 packages; preserve accepted compiled payloads and original archives |
| Final verification | Seven dedicated audits plus Dpkg/APT consistency and per-package closure checks |
| Recovery boundary | Save and verify one paired cold checkpoint of the two disposable VM disks |

The accepted ACL retest, Linux API headers, filesystem layout and native build
support markers already pass 0/0 and will be skipped by the final driver.
Berkeley DB, APT, Python alias, bootstrap cleanup and metadata closure markers
remain absent. The final review reuses existing compiled artifacts; it is not
a new compilation of all 124 accepted packages.

## Why the single remaining database package is substantial

The live standard-suite dispatch log currently says Running partition tests.
That is the eighteenth entry of the initial group sequence. The compiled
feature profile plans 24 initial groups, followed by general recovery, six
join tests and the final access-method matrix. Initial groups after partition
cover compression, three replication-manager groups, replication and security.
The Recd011/Recd012 names recently observed are subcases inside partition;
they do not mean that the later general recovery section is already complete.

The verified source lists 135 general access test templates and nine configured
access methods: btree, rbtree, recno, frecno, rrecno, queue, queueext, hash and
heap. The final matrix therefore schedules 135 * 9 = 1215 dispatch entries.
That section has not started. Some combinations return early as inapplicable;
these are planned entries, not 1215 independently timed full tests or assertions.
No duration estimate is derived from multiplying that number by one slow case.

The numbered general sequence runs from Test001 through Test142, with 135
listed entries: 075, 080, 104, 105, 106, 108 and 118 are absent from the frozen
dispatch list. These omissions are upstream list structure, not tests removed
by this project. Test044 is the forty-fourth listed entry; 91 listed entries
follow it in one pass. The entry count 135 is not the highest test number.

At 21:54 UTC, the current partition variant was executing Test044 cycle 1.
Its actual source performs three cycles per invocation. Each selects a load
duration from 300 to 600 seconds, then crashes the workers and verifies recovery.
The first current cycle logged 525 seconds. Five observed workers were each
actively consuming one CPU, with increasing CPU time. The quiet parent log
during this load interval is expected. Recovery/verification time is additional;
no complete-suite ETA follows from this one case. Source list, exact remaining
entries, source hashes and process observation are retained in
.local/logs/h07-bdb-numbered-sequence.json, SHA-256
`74443532c98400b724832711a60deb0ada0d298eeded316916f7aa0e2fc8777a`.

For scale, source also declares 24 recovery templates and 99 replication
templates. Partition itself calls two partition wrappers for btree/hash over
the 24 + 135 templates: 636 wrapper-call slots in the entire group, including
unsupported combinations that the upstream wrappers skip. A portion has run;
636 is not a count of currently remaining executable tests. These nested and
conditional loops prevent a truthful global test-completion percentage from
being inferred from a heading or from the number of packages alone.

The earlier Recd011 investigation proved a finite timed case advancing and
terminating in 7m10s. That diagnoses the suspected loop; it does not establish
that the complete database suite is nearly finished. Keep the complete result
and postchecks as the acceptance boundary.

## Seven final audits

1. Native ELF/library providers and declared dependencies.
2. Installed payload hashes, links, modes and ownership conflicts.
3. Executable script interpreters and provider dependencies.
4. Unowned files versus reviewed generated/configuration exceptions.
5. Actual native compiler/build workflow.
6. Canonical Perl installation records and owned paths.
7. Compiler defaults and declared instruction-set requirements.

Raw snapshot: .local/logs/h07-remaining-volume.json, SHA-256
`affa369df5d3f7d1eb5302c9c0fe89ca6c4c4edd45410b35821d3202c3fcc29e`.
It records source hashes, exact template/method lists, actual pending markers,
the current dispatch group and the seven script names. No acceptance criteria
were removed and no running source/test input was modified for this report.
