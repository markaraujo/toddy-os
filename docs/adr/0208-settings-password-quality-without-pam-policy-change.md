# ADR-0208: Settings password quality without changing active PAM policy

Status: accepted · Date: 2026-11-10

## Context and frozen inputs

GNOME Control Center50.4 needs libpwquality. Frozen BLFS13.1 selects
Cracklib2.10.3 and libpwquality1.4.5. The former recommends the exact versioned
cracklib-words distribution; its README-WORDS identifies prior Cracklib/Crack and/or
public-domain lists and warns that other lists may have restrictive terms.
Freeze compressed/expanded hashes and retain that exact provenance text. Do not
substitute arbitrary downloaded password corpora.

## Decision

Build shared Cracklib/tools and its full recommended dictionary as UID101 with
read-only source inputs. Keep the19,163,351-byte raw wordlist in build inputs;
install only packed runtime indices, not an unused raw duplicate. Include a fixed
product word instead of a builder hostname. Retain the original endian/dictionary
checks and qualify actual default dictionary use/refusal/recovery separately.
Optional Cracklib Python bindings are unselected.

Build libpwquality shared C SDK/tools and PAM module with owned patched PAM1.7.2.
Omit optional Python bindings using the frozen book-supported switch: Settings
uses the C SDK. Preserve stock pwquality.conf as a native conffile. Packaging the
module does not activate it: verify no existing active PAM file refers to it,
snapshot active PAM configuration, and require exact unchanged files afterwards.
Do not rewrite system-password, enable new PAM policy, modify accounts or exercise
owner passwords. Test only public synthetic fixtures, under UID101/NoNewPrivs,
private device mounts and no external route. Do not record fixture values as
credentials or infer weak-input acceptance from a CLI exit alone.

## Security/ABI review and limits

The upstream1.4.5 source exposes separate settings allocation/free, bounded CLI
input and explicit error returns for check/configuration failures; probe the actual
owned library/tool and malformed-setting/weak/empty-input recovery. This is a
narrow consumer/ABI review, not a memory-safety audit. The public upstream advisory
API returned an empty array during this slice; its local raw response and digest
are retained. An empty public list does not prove absence of vulnerabilities.
[Upstream security overview](https://github.com/libpwquality/libpwquality/security)
and [release1.4.5](https://github.com/libpwquality/libpwquality/releases/tag/libpwquality-1.4.5)
provide primary provenance, not blanket security acceptance. Refresh release
security review at the final image gate; never silently upgrade the foundation.

No original libpwquality test suite exists in this source/book; say so explicitly.
PAM module authentication integration remains unqualified while inactive. Actual
Settings password dialogs, localization, session privilege and complete desktop
acceptance remain separate runtime work. Essential existing PAM/login evidence
is reused only while its inputs/policy are unchanged.

## Verified duplicate custody — 2026-11-10

The closed native promotion usr duplicate was retired only after archive,
installed payload and original workstage verification; installed root changed0.
[Promotion custody](../evidence/B02-cracklib-promotion-custody.json) reclaimed
10752000B. A separate [decoded dictionary custody](../evidence/B02-cracklib-word-custody.json)
retired only original-words after streaming the retained authenticated xz and
matching the exact19163351expanded bytes/SHA256. Installed root changed0 and
19165184B reclaimed. Source notices, compressed source, compiler, tests, workstage
and native archive remain. Qualification now independently streams that retained
xz when the decoded duplicate is absent. Recover to a fresh bounded location and
verify expanded length/hash; never replay an install or prior custody operation.
