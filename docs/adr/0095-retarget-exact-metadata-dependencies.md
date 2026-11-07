# ADR-0095: Preserve exact dependencies across metadata-only revisions

- Date: 2026-11-07
- Status: Native exact-dependency recovery passed; full closure in progress

Final closure completed 35 generations, then Glibc-locales unpacked but could
not configure: its exact glibc (= 2.44-1) dependency did not match the already
accepted metadata revision 2.44-1+toddy1. Inventory also found GCC still pinned
to the earlier GCC-runtime revision after the runtime's own metadata update.
No upstream source version or ABI changed, but Dpkg correctly treats these as
different package versions. Keep the failure and incomplete package state visible.

Order metadata processing so exact-version providers precede their consumers.
Retarget only equality pins whose provider has the identical frozen version
after removing the project metadata suffix. Preserve equality, do not replace
it with >= or force dependency configuration. Reject missing providers, cycles
and a different upstream/packaging baseline before mutation. Revisit previously
completed metadata generations when their equality pins no longer match; retain
those archives/records and increment the metadata revision. Use generation-named
staging directories so a later revision never overwrites earlier staging.

Recover an unpacked own metadata revision only when the recorded incomplete
upgrade matches its version, original accepted predecessor digest and preserved
archive digest, and every installed regular/link payload matches the failed
record. Produce a new corrected revision; the earlier failed record remains
installed=false. Other partial package states refuse for diagnosis. This is a
narrow recovery of the measured own-package dependency failure, not permission
to adopt an arbitrary unconfigured package or suppress Dpkg errors.

Alternatives rejected: force-depends or relaxed version bounds would hide the
mismatch; downgrading core libraries would create unnecessary payload churn;
restarting the full closure would discard valid completed generations. The
native Dpkg status/error and installed dependency inventory are primary evidence.
Four deterministic tests cover same-baseline retargeting, upstream version
rejection, provider order and cycle/missing-provider rejection; 177 tests pass.
Native recovery and final Dpkg/APT consistency checks remain required.

## Actual native recovery

GCC 16.2.0-1+toddy2 configured with exact GCC-runtime 16.2.0-1+toddy1;
Glibc-locales 2.44-1+toddy2 configured with exact Glibc 2.44-1+toddy1.
Both progress receipts are complete. Actual installed GCC executable and locale
archive SHA-256 still match their original accepted source-built payloads.
The failed locale +toddy1 component record remains installed=false. Closure
continued to 43/126 complete generations. See H07-metadata-recovery.json; this
is not yet final whole-base dependency/audit acceptance.
