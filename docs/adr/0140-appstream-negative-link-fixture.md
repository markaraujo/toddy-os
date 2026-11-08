# ADR-0140: Preserve one frozen AppStream negative symlink fixture

- Date: 2026-11-08
- Status: Accepted; six affected checks and actual native extraction/build/installation passed
- Source: AppStream1.1.6, archive SHA256
  e298929f39729e84a70f6be6941f3e7f3fc2ee3c83cb3ea1b1b5b280a8fe3a24

The authenticated upstream archive includes the deliberate negative compose
fixture tests/samples/compose/usr/share/metainfo/
org.example.nonexistent-badlink.metainfo.xml pointing to /nonexistent.
The standard data filter refused it before extraction. Preserve the original
refusal and failed preflight job; no compilation or target installation occurred.
The compose feature remains disabled in the current core metadata bootstrap.

Preserve the original source fixture without following it or weakening general
extraction. Permit only this exact archive filename, member path, symlink type,
zero size and target. Source extraction first verifies the frozen archive digest.
Require the fixed referent to be absent on the extraction machine, apply the
ordinary regular-member path/permission checks, then restore only this original
symlink type/target. No other absolute link, hardlink, path or archive qualifies.
Subsequent writes through an external alias remain rejected by the data filter.
The production package staging verifier and other extraction rules are unchanged.
The compiler sees a private read-only source namespace with no /nonexistent.

Tests cover exact preservation, wrong archive/path/target/type refusals, existing
referent refusal, external-alias writes and existing dpkg/path safety behavior.
Keep fresh source-preparation receipt identities for corrected attempts instead
of overwriting failed logs. Require successful preparation before dispatching a
compiler job, and inspect actual source/work/exit postconditions before recovery.
Native extraction/build/test/consumer results are independent acceptance gates.

Corrected native preparation preserved the exact broken symlink. All eight
registered core AppStream drivers passed. A proof-count assertion recovery
preserved97 compiled ELF hashes and225 stage entries; actual staged/installed
metadata/refusal/GI consumers and independent ownership passed0/0. The source
fixture is not installed in the runtime payload. See the separate source-guard
and native build/install evidence; no GUI or compose qualification follows.
