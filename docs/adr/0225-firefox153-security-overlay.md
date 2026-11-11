# ADR-0225: Qualify the Firefox153 ESR security overlay before browser delivery

Status: accepted selection; source integrity verified, qualification pending
Date: 2026-11-11
Scope: B02 browser only; foundation and accepted desktop dependencies retained

The frozen BLFS13.1 browser source is Firefox153.2.0esr. Current upstream review
found later same-ESR security advisories, including MFSA2026-93 (September15),
MFSA2026-100 (September29) and MFSA2026-127 (November10). They describe high-impact
memory-safety and sandbox-boundary corrections. Some entries are platform-specific;
no recorded backport analysis clears the Linux browser's affected closure. Main
and WASM sandbox configuration flags alone do not clear this release obligation.

Under ADR0007, select the official Firefox153.7.0esr source as the browser security
candidate. Preserve the original153.2 source record, immutable source, compiler
job, logs, failures and configuration evidence. Append a separate
`firefox-security-1537` source lock entry; do not rewrite the frozen book or the
foundation's compiler/libc/package versions. This same-ESR compatibility selection
requires actual source/dependency/ABI/runtime qualification before promotion.

The candidate800,080,060byte archive matches the source entry in the publisher's
HTTPS SHA512SUMS. SHA256 is
`7f8715ee7de2cf36a156216a9b1c7f26d1653010e65793bb2fce66e12edb6ea0`.
The exact SHA512, publisher-file digest, advisory snapshot hashes and URLs are
in [the security review](../evidence/B02-firefox-security-review.json). OpenPGP
signature verification and byte-identical upstream build reproducibility remain
unclaimed. Source integrity and a newer version do not establish security/ABI/UI
acceptance.

## Current execution and next gate

The original isolated compiler is healthy, progressing and supervised. Finish it
once as a private compiler feasibility result, retaining measured costs and exact
inputs. Its output cannot be promoted as the delivered browser or used with owner
credentials/remote browsing. Do not mutate its producer, source, tools or guest
while its single writer is active. Keep deterministic monitoring and resource
reserves; a healthy build is excluded from the diagnosis budget.

Review the verified candidate archive read-only on the host while that compiler
runs. Inspect actual minimum Rust/Clang/NSS/NSPR requirements, selected codecs,
WASM/default toolkit options, licenses and source changes. Preserve the supported
Wayland/main/WASM sandbox design and owned native dependency ABI; any additional
affected dependency decision must be explicit before packaging.

After the original compiler has an actual terminal result, measure capacity.
Prepare a new source/work/job identity only with sufficient space and qualified
custody/retirement for any replaced private build cache. A same-ESR label does not
make old object files a valid cache. Do not copy them into a fresh tree or rely on
archive mtimes as proof of unchanged dependencies. Reuse unchanged qualified
compilers/packages/tool evidence, select affected browser checks from real input
changes and retain essential runtime sandbox/offline/recovery/native UI checks.
Never lower100GiB host/16GiB target/128MiB scratch reserves or start a second guest
writer. B02/G2 remain incomplete until the corrected installed browser is proven.

Sources: [Mozilla ESR advisory index](https://www.mozilla.org/en-US/security/known-vulnerabilities/firefox-esr/),
[MFSA2026-93](https://www.mozilla.org/en-US/security/advisories/mfsa2026-93/),
[MFSA2026-100](https://www.mozilla.org/en-US/security/advisories/mfsa2026-100/),
[MFSA2026-127](https://www.mozilla.org/en-US/security/advisories/mfsa2026-127/),
[official source](https://archive.mozilla.org/pub/firefox/releases/153.7.0esr/source/)
and [publisher checksums](https://archive.mozilla.org/pub/firefox/releases/153.7.0esr/SHA512SUMS),
observed2026-11-11. Historical SpiderMonkey overlay practice is ADR0147.
