# ADR-0147: Select an explicit SpiderMonkey140 security overlay

Status: Accepted selection; source integrity/native compile/stage passed, critical tests/ABI/security qualification pending.
Date: 2026-11-09
Scope: B02 new JavaScript dependency only; no foundation rebuild or silent baseline replacement.

## Concrete blocker and decision

Frozen BLFS13.1 selects Firefox140.14.0ESR's SpiderMonkey. The actual native
compile/stage and901original JSAPI cases passed. This is not security acceptance:
Mozilla MFSA2026-92 identifies high-impact CVE-2026-92021 in JavaScript JIT fixed
in140.16; MFSA2026-99 identifies high-impact CVE-2026-100769/100776 in WebAssembly
fixed in140.17. Their linked private Bugzilla reports deny access. Do not infer
backports from inaccessible reports or ask for credentials when public corrected
source is available.

Select official Firefox140.17.0ESR source as an explicit security overlay for
this uninstalled dependency. It retains the mozjs-140 API family required by
GJS1.88.1. This is a compatibility hypothesis until native build/embedding/GJS
checks pass. Keep the original140.14 source record, work, raw tests and failures.
Record the new archive and publisher checksum separately before extraction.
Do not overwrite source locks, mutate old immutable inputs, silently alter
compiler versions or call the overlay qualified from its version alone.

The official archive/source index and SHA512SUMS were fetched over HTTPS.
The expected source SHA512 is
c569f4f1ecbadec4c24ab60af6c8ff03f6c1292e7b2446edca7cc6f5575bd8d98e3ee9efb9877eba98bdb15354a4c4260515f8c6fd9aa9d198b26722f60ae5f4.
Actual637640276B archive matched that SHA512. Its SHA256 is
4d6ed3b18b2069c55bab12d8ba95da6013ac0b036d8a031df8b9f39a25d05c33,
recorded separately as mozjs-security-14017. The candidate contains422112members.
The exact five Python3.14 patch paths were inspected and --fuzz=0 dry-run passed;
no guest source has been prepared or patched yet. This publisher
checksum/HTTPS basis is not a verified OpenPGP signature claim. Inspect the five
Python3.14 compatibility changes against the new source before reuse; do not
blindly apply the old patch or drop required changes.

## Validation and capacity

Finish the healthy original JIT and corrected main/embedding jobs once; preserve
actual results, not timeout/absent-log success. Then use a fresh source/work/job
identity for the overlay. Reuse installed compilers, ICU and cbindgen. Select
original/ABI/security regressions by actual source differences; do not repeat
unaffected foundation suites. New broad engine input changes still require
critical engine coverage and actual installed/consumer checks before promotion.

Measure capacity before guest preparation. Original source occupies4368924672B
and complete compile/stage work617218048B. The new archive/source/build must fit
above the100GiB host/16GiB target reserves with a declared budget; no unverified
cache deletion, retired custody replay or reserve reduction. One guest writer
remains mandatory. B02 and release gates remain open until proven.

## Sources

- [Mozilla MFSA2026-92](https://www.mozilla.org/en-US/security/advisories/mfsa2026-92/),
  September15,2026, JavaScript Engine:JIT entry.
- [Mozilla MFSA2026-99](https://www.mozilla.org/en-US/security/advisories/mfsa2026-99/),
  September29,2026, JavaScript:WebAssembly entries.
- [Official140.17 source](https://archive.mozilla.org/pub/firefox/releases/140.17.0esr/source/)
  and [publisher checksums](https://archive.mozilla.org/pub/firefox/releases/140.17.0esr/SHA512SUMS),
  consulted2026-11-09. Local source-index SHA256
  b3fdd7556682cef94f262860505befb9ca5d9daa5ec0bfff9cf514eee6f0bd9f.

## Observed build and source delta

[Source comparison](../evidence/B02-mozjs-security-source.json) found15changed
files within the explicitly inspected JS/public/mfbt/Rust/Cargo scope, including
11runtime files and four original JIT test paths;88510files were byte-identical.
This does not assert that uninspected Firefox components are unchanged.
[Native candidate build](../evidence/B02-mozjs-security-stage.json) compiled and
staged successfully with the existing compilers/ICU/cbindgen; actual shell
version140.17.0/arithmetic42. The6GiB capacity budget above16GiB target reserve
passed before transfer. Original baseline retained, no owned promotion.
