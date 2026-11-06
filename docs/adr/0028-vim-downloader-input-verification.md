# ADR-0028: Verify live Vim downloader inputs before execution

- Status: Frozen inputs and guard prepared; actual native preflight/suite pending
- Date: 2026-11-06
- Scope: Unmodified Vim 9.2.1201 full upstream suite including GLVS

## Decision and measured inputs

Retain every upstream test and assertion. The GLVS suite downloads and installs
four third-party scripts, so verified Vim source alone cannot authenticate all
executed inputs. Freeze their actual source IDs, official HTTPS URLs, byte sizes
and observed SHA-256 in vim-glvs-inputs.lock.json and supplemental sources:

| Upstream script | Source ID | Download |
| --- | ---: | --- |
| AnsiEsc, script 4979 | 26454 | AnsiEsc.vmb |
| mrswin, script 514 | 3276 | mrswin.vim.bz2 |
| Decho, script 120 | 9388 | Decho.vba.gz |
| dumpx, script 5632 | 25749 | dumpx.tar.xz |

Actual pages and original download bytes are retained outside Git under
.local/upstream-verification/vim-glvs/. Source IDs are fixed upstream versions;
no publisher digest/signature is claimed. Inspect archive member names before
use and reject traversal, absolute paths and special members. These files are
build-only test inputs and never enter the installed OS/runtime image. Their
notices are retained in the source cache: AnsiEsc/Decho carry Vim-derived and
bundled notices, DumpX GPLv3; mrswin's distributed header does not state a license.
Do not redistribute that build-only input as an OS component or invent a license.

Put a root-protected verification wrapper named curl at the front of the test
PATH only. Native /usr/bin/curl and installed runtime behavior remain unchanged.
The wrapper uses actual native Curl/TLS against the actual public endpoints,
validates live metadata's first selected source ID/filename against frozen
facts, then verifies exact downloaded plugin bytes before atomically exposing
any output to Vim. Changed versions, unknown script IDs, bad hashes, metadata
modelines and unsafe output paths fail closed. No test/source/expected-result
patch, synthetic endpoint, replacement plugin or cached fake response is used.
Unrelated Curl invocations retain native behavior.

The original suite's HEAD check for historical src_id=1 is allowed only as a
real HEAD request; it cannot select an unverified GET payload. Native preflight
must verify all four metadata/download pairs as tester without executing them.
The complete unchanged suite must then record verified plugin downloads for all
four source IDs; missing guard coverage fails acceptance even if make returns 0.
Each event records only public input facts/hashes/UID, never arbitrary arguments,
headers or credentials. No reusable signing/provider key is involved.

## Alternatives and consequences

Deleting the downloader test would discard coverage. Executing current mutable
plugin bytes before checking integrity would violate source freezing. A local
HTTP snapshot server could test transport/extraction, but the live verification
guard keeps the real upstream integration and leaves tests unchanged. Metadata
is untrusted data: it cannot choose a new executable version or authorize work.
If the website changes, stop and diagnose; never silently loosen pins or TLS.
Reproducers need the verified source cache and the documented public network
precondition for this suite; no general offline-public-site claim is made.

## Sources

Actual frozen runtime/autoload/getscript.vim and
src/testdir/test_plugin_glvs.vim, read from the verified Vim archive; actual
[AnsiEsc](https://www.vim.org/scripts/script.php?script_id=4979),
[mrswin](https://www.vim.org/scripts/script.php?script_id=514),
[Decho](https://www.vim.org/scripts/script.php?script_id=120) and
[DumpX](https://www.vim.org/scripts/script.php?script_id=5632) version metadata.
