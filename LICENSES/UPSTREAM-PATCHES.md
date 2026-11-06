# Upstream patch notices

The original-code licensing decision remains D10. It does not relicense the
upstream code represented in patches or the separately distributed OS components.

- Python-3.14.10-openssl_4-1.patch retains the original five CPython backports
  and attribution, with only the test insertion context adapted (ADR-0018).
  The corresponding upstream license/history is in Python-3.14.txt, copied
  verbatim from the frozen Python 3.14.10 archive.
- coreutils-9.11-i18n-context-1.patch retains all added/removed GNU Coreutils C
  and test lines from the frozen LFS patch, with balanced context (ADR-0019).
  Coreutils source headers specify GPL version 3 or later; its complete GPL
  version 3 text is retained verbatim in GPL-3.0.txt from the verified archive.
- LFS-MIT.txt covers the adapted book command/documentation material. It does
  not replace the licenses of upstream program code.

Source hashes, immutable derived-patch URLs and parent inputs are recorded in
the source locks. Final component/license closure remains required before G1
and experimental release; these notices do not claim that audit is complete.
