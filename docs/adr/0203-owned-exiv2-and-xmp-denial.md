# ADR-0203 — Own Exiv2 metadata with real feature dependencies and XML denial

Status: accepted selected profile · Date: 2026-11-10 · Story: B02

Use frozen BLFS13.1-systemd general/exiv2.html0.28.8, official archive SHA256
`ea51b0609f58a9afa063b60daa1539948b62247721e154f4fff0ad3aec9f9756`.
Keep source/code/version and existing foundation unchanged. Shared metadata/CLI
profile selects PNG/JPEG/TIFF/BMFF/video/XMP and actual owned Brotli1.2.0/INIh62.
Network/HTTP transports remain upstream-default off; sample tools, external test
frameworks/fuzz targets/docs/Python bindings are unselected. Source archive legal
notices include the full Adobe XMP SDK notice. ABI libexiv2.so.28 links the pinned
native Glibc/GCC/Zlib/Expat/Brotli/INI packages; installed resolution/APT closure
passed without replacing another library ABI.

## Original results and retained failures

Initial89step compilation succeeded; own collector expected an absolute runner
but CTest registers runner.py relative to /src/tests. Preserve the failure, use
exact declared cwd/relative argv and byte-identical private test/data copies.
First real tests exposed two omitted feature paths (Brotli malformed-stream
regression and custom INI lens mapping), plus a missing readonly Canon source
reference in that private layout. Preserve all failures, the old feature cache
manifest and actual old CLI/library ELF copies. Qualify the real dependencies
(ADR0202), reconfigure the same CMake tree, compile69affected steps and use NEW
private fixtures/read-only exact Canon source alias/fresh synthetic HOME.
No repeated unchanged failing profile or source-version workaround.

Four real original test programs executed1169methods:1159non-skipped/10declared
skips. Bugfix310, lens532, TIFF1, regression326. The fifth registered version
program calls verbose_version(True) and executes ZERO unittest methods: useful
feature metadata, never a test pass. All five driver commands exit0. The ten
explicit upstream exclusions are eight release-disabled debug-structure cases,
one suite-disabled issue1821 memory-leak case, and a Mac resource-fork filesystem
case. Exact IDs/reasons are in the proof. No claim that the suite-disabled bug is
fixed, that debug/other-platform cases passed or that all XML/image vulnerabilities
are resolved. This is selected-profile functional acceptance; release security
review remains required, including the existing Expat ADR0013 limitation.

## Independent and installed parser checks

Own CLI checks corrected a source-verified no-match status: Print::printMetadata
returns1/empty output for an absent -K key after successful deletion (its comment
incorrectly says-3). Initial reset assertion failure retained. The XML positive
control passed; an external-entity document returned1/empty stdout and explicit
XMP Toolkit error201/Error in XMLValidator/failed-decode warning, no canary read.
The initial own test expected the later AdobeAdapter DOCTYPE message; readonly
diagnostic confirmed the earlier src/xmp.cpp XMLValidator::startDTD rejects DTDs
before that adapter. Require that exact real rejection, not a generic nonzero or
absence of output. Probe7 passed with all92compiledELFs/55stage files unchanged;
no original/compiler replay. Valid XML recovery also passed.

First native preflight expected one version unittest instead of zero. It rejected
before staging/archive/dpkg; actual root changes0 verified. An unchecked shell
chain had dispatched that failed preflight; subsequent qualification and fork
were combined in one Python guard. New native install2/post0/0,75changedpaths/
80entries; never replay first install. Installed UID101/private devices/no route
passed actual UTF8 PNG EXIF edit/read/delete-reset, IHDR/IDAT/IEND retained,
corrupt JPEG refusal/input unchanged/two recoveries, valid XMP/external entity201
rejection/canary retained/XMP recovery, exact installed stage bytes/pkg-config/
shared ABI/APT0. No GExiv2/LocalSearch/remote-transport/GUI or physical acceptance.

[Full measured source/failure/original/native proof](../evidence/B02-exiv2-install.json).
Package SHA256 `2c5a7cb6c66a871623f30bbc36bc018b320ed452ff0cf68c874da45a57160cea`.
Raw evidence checksum is recorded in the linked immutable bundle inventory.
Next qualify GExiv2 against this owned library. Kernel Landlock remains pending;
no full desktop or G2 acceptance is inferred.
