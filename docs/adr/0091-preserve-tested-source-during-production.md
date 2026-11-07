# ADR-0091: Preserve tested source while compiling production output

- Date: 2026-11-07
- Status: Native private production/source-preservation verification passed
- Extends: ADR-0069, ADR-0086 and ADR-0087

## Problem and decision

The prepared production handoff bind-mounted the tested source writable, then
configured and compiled inside its build-production directory. That would add
files to the tree recorded by full-source custody and make later receipt
verification fail. A mount namespace alone does not prevent writes to the
underlying files. No actual qualified production handoff has occurred yet.

Use berkeley-db-production-view.sh to bind the canonical source read-only and
mount a separate, root-private production output directory over build-production
inside that namespace. Verify both inode mappings and effective read-only/
writable mount flags before invoking the command. The underlying tested tree,
raw reports and source-custody inventory remain intact. The normal dispatcher
still owns actual package staging/installation auditing, and complete-suite
nomination remains mandatory before the real production recipe invokes this view.

Retain caller stdin on a separate descriptor before the helper's namespace
heredoc; the normal handoff supplies its child script through stdin. The native
probe exercises that exact boundary, attempts a non-truncating write-open of
LICENSE and requires EROFS, then writes/fsyncs/reads its separate output area.
No source bytes need to be changed to test rejection.

Split the same production recipe into configure/build/install stages while
retaining its default complete invocation and frozen configuration. Keep test
APIs/Tcl/DBM/compat185 disabled in production, as ADR-0032 requires. Extract the
existing transaction/reopen/abort check into a shared inner script without
changing its C assertions. The real installed check still requires configured
native package status; private staging checks do not bypass that guard or claim
an installed package.

Alternatives rejected: accepting a changed custody tree would discard evidence;
recopying the full tested source unnecessarily duplicates inputs and changes
identity; moving compiler outputs into a separately writable directory preserves
both tested-source identity and the canonical relative paths used by configure.
Source references remain the frozen maintained DB production/test separation
in ADR-0032 and the measured namespace/custody semantics in ADR-0069/0086.

## Verification scope

The independent probe uses the already verified fresh native source from
ADR-0089, not the live full-suite tree. It has its own private staging parent,
uses -j2, records intent/PID/log/exit for each step and snapshots every physical
source entry and regular-file byte before/after. It builds/stages the actual
production profile and runs the shared native transaction/reopen/rollback check
against its private header/library/tool paths. No package installer is invoked.
Full-suite acceptance, real package installation and APT remain separate gates.

## Actual results

Generation /mnt/lfs/sources/recovery/db-production-nlsr4aoj completed with driver
4116994 terminal exit zero. Isolation, configure, build, private install and
postcheck each exited zero without timeout. Native Berkeley DB 5.3.28 passed
commit, aborted-update rollback, separate-process reopen and persisted-value
checks using the staged production library. The shared check body is byte-for-byte
identical to the previously embedded installed check; only its location changed.

All 10,606 physical source entries, ownership/modes/inodes/links and regular-file
bytes matched before and after. Write-open of the canonical source returned
EROFS; separate output writes and caller stdin passed. Native package status
remained unchanged and the shared stage/berkeley-db path stayed absent. Actual
outside-source, outside-output and redirected-output invocations all refused
before executing their command. The real production nomination gate is unchanged.

| Evidence | SHA-256 |
| --- | --- |
| Terminal collected report | fcd9eec3fb1bd8dd106577278b6e406f9db4599d97b75942c2c02ef49f21d6b7 |
| Native result | 3bb71fcb31431196a580900a30999b73689b9819cb26866f5d136b5aac82d5db |
| Independent stage/log and guard recheck | ba0835fc7ab83f383869de5018e9f865a146e46dd0de374b7593c93a530f0d3c |
| Equal before/after source snapshot | 4e40c9cf68260c1700801f46a7cfb13ce61e668d9412939b87b11b323081653e |
| Native read-only/stdin probe | d2e26f2a91e1f125384c4150425893f64a14da576e88012a3b0878edb8e3d220 |
| Native production build log | aeedd31f6735c879daa83fcf4287f253eaa958bad9cde53d0dbce26a33955507 |
| Native production postcheck | 89e52378d3f3a340a88cf6db9d4e7a1aca8a5aa5e02685abaa7913ed36f1c2b9 |
| Staged production shared library | 945ad70683f03cd27630336ac003beba9c5c87e64e4251764c23231658bad42c |

173 local checks pass. These private build/staging results do not accept the
complete standard run, install a package, earn H07 credit or permit APT yet.
The still-live full-suite source and its raw reports were never mounted by this
experiment. The same read-only view is now prepared in the real handoff recipe,
which remains unreachable until its independent complete-suite gate passes.
