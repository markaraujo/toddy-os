# ADR-0071: Exclude optional Python QA through native image package operations

- Date: 2026-11-07
- Status: Private configured-image operation verified; full image integration pending
- Extends: ADR-0049 and ADR-0057

## Decision and assembly order

The prepared live-root inventory copies configured native package payload and
database state. After H11's accepted Python ownership transfer, that includes
the optional python-test-support package in the builder. The release image must
exclude both its data and its installed package identity. Deleting QA files
while retaining their Dpkg ownership would violate the package consistency gate.

Add scripts/build/h11/remove_image_qa.py as a private-image assembly component.
The gated caller supplies the verified core/QA records after the actual H11
transfer, a freshly assembled private image and a protected external journal.
The component refuses the installed target, mismatched/unpartitioned records,
unexpected removable paths, extra native file-list ownership, QA maintainer
scripts and existing journals. It verifies exact installed QA/core payload and
ownership before recording intent and invoking native Dpkg --root --purge.
No force-depends, force-overwrite or manual payload deletion is used.

After native exit 0, all QA files, roots and ownership must be absent, the
Python runtime must still match its record, every other package identity must
be unchanged and the native database audit must be clean. The installed builder
status hash must be unchanged. An interrupted/failed operation preserves its
journal, native log and partial image; rebuild a fresh image rather than
silently replaying removal or deleting residual files to force a pass.

The assembler must perform release QA removal before final cache/index/ACL
capture and full image audits. Refresh the final package inventory/database
evidence after removal. H10's intermediate live-system work and H11's final
release generation remain distinct; none of these private probes starts or
accepts either milestone. The ordinary runtime repository must also exclude
the optional QA archive, while the builder and QA archive retain all tests.

Primary package semantics are from the frozen Dpkg 1.22.22 man/dpkg.pod and
actual native invocations. The new path builds on ADR-0049's verified own
Python 3.14.10 archive partition and configured ownership transfer. An archive
exclusion alone cannot establish an installed image's database consistency.

## Native component evidence

Reproduce with:

```sh
python3 scripts/host/probe_python_qa_handoff_plan.py --image-removal
```

This repeats the real configured dependency/ownership-transfer transaction in
a disposable root before invoking image removal. Native Dpkg purged 5,396
non-directory QA entries (5,395 regression files plus its copyright notice),
retained 22 configured packages and preserved all 3,943 core files/links and
their ownership. Native Python SSL, SQLite, ctypes and unittest operations pass
after removal. All 15 Python QA private-key-marker findings disappear; the
scanner's six other findings remain unchanged and are reviewed below.

Seven new refusal cases cover the installed builder, an unrelated removable
runtime path, a QA maintainer script, unexpected database ownership, changed
QA bytes, untracked QA remnants and an existing removal journal. The untracked
remnant experiment uses a separate real image: Dpkg exits zero but the component
correctly leaves complete=false because the QA tree still contains data. This
demonstrates why package-command exit alone is not image acceptance.

The combined probe retains the prior ownership-transfer checks, for 12 recorded
negative cases total. Successful private fixtures are removed only after all
checks and report capture; unexpected failures preserve their workspace.

Raw .local/logs/h11-python-qa-image-removal-probe.json SHA-256:
581517bea07d45de4c473b667288ac41d8ba0035738a03abfb5a0ca52e8567d2.
Component SHA-256:
641d240d347d7c984546ac29f505e3b4a52a3092713fe60b3b243004d97c5fb7.
Positive native purge log SHA-256:
ac3fe42aa5db2276325c87a5260c0290c4927ae11b15f85df950e97546f794eb.
Residual-data refusal log SHA-256:
4c84832f7396ebcdcd59b08e2fd0111283dc90f9f08ee2691a24af24cad07df2.

## Additional marker findings and source-backed classification

The initial probe incorrectly expected the Python-only count of 15 across its
whole 22-dependency root. The broader scan found 21 files: 15 QA fixtures plus
six OpenSSL manuals. That attempt was not accepted; its fixture remains at
/mnt/lfs/tmp/toddy-python-qa-handoff-vxnyyfbh and raw failure SHA-256 is
00e56b6b6bd7873b5ebcade0f19d807af8562c285c0c52d2da96d4a99bedee31.
The corrected QA-specific assertion requires all 15 QA findings to disappear
and every non-QA finding to remain unchanged. It grants no credential-audit pass.

The separate read-only probe below then classified all six manual findings:

```sh
python3 scripts/host/probe_openssl_document_markers.py
```

Each file matches the own installed OpenSSL 4.0.3 package. Each POD document
matches the frozen source archive exactly; each HTML example normalizes to
that same source example. Every private-key header is accounted for. The
bodies contain explicit ellipses/placeholders, fail strict Base64 validation,
and are rejected by the actual native OpenSSL pkey parser (exit 1). No key
contents are emitted. These are unusable format illustrations, not credential
material. The official [PEM manual](https://docs.openssl.org/4.0/man3/PEM_read_bio_PrivateKey/)
and [glossary](https://docs.openssl.org/4.0/man7/openssl-glossary/) explain these formats;
the frozen local source and native package hashes define this qualification.

Raw .local/logs/h11-openssl-document-markers-<sha256>.json SHA-256:
657dd24c8f5bc5665d6bb0cc94c70e10c2bcb2f7f4a633efcb08cce50ab2c3de.
Frozen OpenSSL source archive SHA-256:
325b5c806167c13b40b1ffeadfe0248197c00eccc4cf123ec1e28d2d2fd216d9.
Own OpenSSL package archive SHA-256:
83ac3034be64eb4bdc84e84bf56c732309ef16af9539035abf16a4f9ed19ef9b.

Paths below are relative to /usr/share/doc/openssl-4.0.3/:

| Exact reviewed file | SHA-256 |
| --- | --- |
| man3/PEM_read.pod | 46c0c181b8882eae8ea608f10c2a2e0e93897101354aabb8d4077fb9b62a498e |
| html/man3/PEM_read.html | 38c3521bfaaa1e696c7da0b09cc1187163f881adacaf10d5b62571afae8162ce |
| man3/PEM_read_bio_PrivateKey.pod | fe20186815d6246d255554a66b3181a054270515100b29d2c34894d9ef108c35 |
| html/man3/PEM_read_bio_PrivateKey.html | 8f02fadb2367ff02ecf71359cf68adf79669bede4a65bc6798236408b67a07cb |
| man7/openssl-glossary.pod | 8437c819231db56ff64d831be97e9f717e0c1e84c46357ae8d6d6d377dfe7445 |
| html/man7/openssl-glossary.html | fcdb517c06a858cdcf0d481b8648337358745aae2c5ed5a29b80f409c5aa7017 |

The scanner still reports all six; no path-pattern suppression or scanner
exception was added. Final image review must retain those raw findings and
match these exact bytes/provenance before using the classification. Changed or
additional findings require fresh review. Public QA key fixtures themselves
remain excluded from the release; this documentation classification does not
authorize including them. Full image credentials, identity state, provider data,
unarmored secrets, package closure, compression and actual boot remain untested.
