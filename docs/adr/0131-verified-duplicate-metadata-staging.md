# ADR-0131: Archive custody for duplicate GCC metadata stages

- Date: 2026-11-08
- Status: Accepted; guarded retirement complete

The disposable Phase2 target has about18.4GiB free with a16GiB reserve, insufficient
scratch headroom for the next graphics build. Two old metadata-only packaging
stages each retain about1.91GB of identical GCC16.2.0 payload. Both actual stages
were compared against all1975 payload entries of the retained owned canonical
gcc16.2.0-1+toddy2 archive record: exact file/link/mode/owner/hash equality.
The archive SHA256 is213faf901ece62e0e7cf5833d1c2a2bae5c39c63a54a67435afef6aa79c0507c.

Apply the existing LLVM duplicate-stage custody pattern only to
/mnt/lfs/sources/stage/metadata-gcc and metadata-gcc-16.2.0-1+toddy2. Require the
actual guarded Phase2 target, exclusive build lock, no running native recipe,
exact installed GCC version, retained archive SHA and complete stage equality
before the first deletion. Reject mounted/escaping/changed paths. Save atomic
per-stage verified/retiring/retired receipts and a retirement sentinel. An
interrupted retirement requires inspection, not a repeated deletion command.

Retain the canonical package/archive, installed compiler, authenticated source,
compiled tests, all recovery/evidence directories and immutable foundation
backings. Only duplicate usr/etc payloads in those two staging roots may retire;
metadata/receipt remain. This is cache custody, not a foundation rebuild or native
compiler transaction. Do not rerun unchanged compiler suites. To recover staging,
verify the archive checksum and extract to a new directory; never reuse the
retired root or reinstall a successful package to recreate scratch copies.

Measure target free space afterward and verify retained archive/installed version
again. Mesa still needs its own conservative scratch preflight and actual native
graphics tests; reclaimed space alone establishes no package or GUI acceptance.

Actual guarded retirement completed: free19,809,042,432→23,630,069,760 bytes,
reclaim3,821,027,328 bytes. Both stage states retired; canonical archive SHA and
installed version unchanged. B02-gcc-metadata-stage-retirement.json retains exact
custody/recovery receipt. Sources/compiled tests/recovery/backings untouched.
