# ADR-0246: Isolated experimental archive signer and independent public pins

- Status: Implemented signer preparation; native repository/full-flow qualification pending
- Date: 2026-11-16
- Scope: Owner-authorized Phase2 experimental package/release delivery

The experimental project archive uses the committed public certificate
`config/phase2/archive-public-key.gpg` and independent public lock
`config/phase2/archive-public-trust.json`. The primary Ed25519 fingerprint is
`453CD646B5F61C586812690F1AF1606035781DB1`; public certificate SHA256 is
`41c8ca50efdcb996d902dd5d5adaf4215354fc184b1636bef3e9a859ea961c77`.
The public lock records creation and expiry. The certificate expires after one
year; individual repository/catalog validity must remain finite and narrower.

Host GnuPG2.4.8 generated the signing identity in a separate private0700 ignored
project directory. Existing personal/global keyrings were untouched. Private
material stays outside guest inputs, images, release roots, logs and Git. The
installed personal assistant receives public verification material only. Native
GnuPG2.5.24 remains frozen; no native dependency version was changed.

Preparation checked the exact public-only packet parser, a real detached
signature and rejection after message tampering. This establishes signer/tool
readiness only. The unsigned exporter, actual signed APT repository/native
install tests, native-components preview qualification and subsequent exact
native-full-flow publication gate remain required. No placeholder qualification
report or signing success grants package installation or story acceptance.

Publishers obtain expected fingerprint/certificate pins from this independent
committed lock before inspecting a candidate root. Root-owned catalog/Signed-By
configuration and explicit owner review/Polkit remain the production boundary.
This identity signs experimental archive metadata; existing foundation evidence,
release scope labels and physical-machine limitations remain authoritative.

Recovery requires retaining the private signer through the owner's existing
private workstation backup process. A lost/expired signer requires an explicit
reviewed key rotation and updated public artifacts; generating a replacement
under the same name cannot reproduce or silently replace this identity.
