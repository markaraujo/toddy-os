# ADR-0171: Owned GTK3 input-module cache integration

Status: selected controlled integration; native postcheck reconciliation recorded below.

## Inputs and isolated query

GTK3 owns /usr/lib/gtk-3.0/3.0.0/immodules.cache. Do not overwrite the file through
an ad-hoc --update-cache invocation after installing IBus. Freeze all twelve
installed regular module paths, exactly one current native owner and payload hash
per module, the owned query tool and old cache/archive hashes. Eleven inputs are
owned by GTK3 and one by IBus. No arbitrary external modules are loaded.

A dedicated UID101/read-only-input namespace calls the actual owned GTK query
tool with those absolute module paths and captures output only under /build.
The previous eleven module registration records must remain identical; add only
the actual IBus record. The first query succeeded with empty stderr, but the own
collector assumed a nonempty IBus locale directory. Frozen IBus source
client/gtk2/ibusim.c explicitly defines IBUS_LOCALDIR as empty. Correct the own
expectation and collect the same output bytes without re-running the query.
Keep both original job identities/results and the unchanged input/cache hashes.
This proves module metadata loading, not graphical focus or keyboard operation.

## Controlled owner revision

Keep GTK3 upstream3.24.52 and revise native package toddy1 to toddy2 by extracting
the verified old archive. Replace only the shared IM cache and source/legal
metadata. Preserve all prior runtime/header/configuration payload entries and
control dependencies. GTK4toddy6 already allows this same-upstream GTK3 revision.
Check every module input against its owner again before mutation, package through
the existing native backend and verify actual installed payload and default query.
No GTK/IBus rebuild or unchanged original test suite is required.

The IBus/UCD17/Unicode3 source notices contributing to the cache inputs are retained
alongside original GTK3 source notices. No user settings, optional app catalog or
unrelated cache is changed. The old archive/record/cache and new transaction receipt
are retained. Future module installation/removal must update this owned shared
resource under a controlled transaction; arbitrary module lifecycle is not
qualified by this one installed module set. Do not create a GTK3/IBus dependency
cycle merely to describe cache inputs; ownership/input evidence is explicit.

## Native result and own postcheck diagnosis

The native transaction installed toddy2 successfully, changed13paths and owns1882
entries. Initial postcheck failed an exact stdout comparison: frozen GTK source
gtk/queryimmodules.c prints argv[0] in its generated comment. The isolated query
uses /usr/bin/gtk-query-immodules-3.0, while the own native checker used its basename.
Use the identical absolute tool invocation. A new read-only verify-only transaction
must establish that the original basename output differs solely in that exact
comment and that the installed package/archive/cache remain unchanged; never
reinstall or regenerate the successful cache transaction to fix this check.
Actual verification result is recorded in the evidence. Graphical GTK/GNOME input,
compositor focus and hardware keyboard acceptance remain pending.

### Actual verification

Verify-only2 recipe/post0/0, ZERO installed-root changes. The original basename
query exit0/stderr empty differs from the installed cache solely in the documented
argv0 comment. All1882 owned payload entries, archive and cache hashes remained
unchanged. The corrected absolute query as UID101 matches the installed cache
byte-for-byte, all twelve owned modules load, eleven prior registration records
remain identical, and969old nonlegal payload entries are unchanged. Native SDK,
APT consistency and complete contributing source notices pass. No cache generation,
package installation or unchanged original suite was repeated. No active writer.
[Evidence](../evidence/B02-gtk3-ibus-cache.json).
