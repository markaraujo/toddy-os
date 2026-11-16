# Fixed MVP live installer route

This source route selects the experimental preinstalled profile explicitly; it is
not a production authorization bypass or native acceptance result. The standard
commands/slots remain unchanged. Keep the actual final MVP ISO and its measured
SHA256; no candidate/component image can substitute for that ISO.

The sole coordinator first exports the actual prepared signed MVP installer inputs
into a protected local directory named `toddy-mvp-installer-native-inputs`, retaining
all payload archives/records/signature bytes and policy/generated/boot documents.
Supply the actual installer/assistant source records and archive cache matching
the installed ISO; snapshot construction refuses packaged/source byte mismatches.
After committing the reviewed host source, run:

```sh
python3 scripts/host/installer_input_snapshot.py --mvp \
  --native-inputs /absolute/protected/toddy-mvp-installer-native-inputs \
  --source-commit FULL_REVIEWED_COMMIT \
  --record /absolute/actual-installer-record.json \
  --record /absolute/actual-assistant-record.json \
  --archives /absolute/actual-native-archive-cache
python3 scripts/host/native_installer_live.py --mvp run \
  --iso /absolute/actual-mvp.iso --iso-sha256 ACTUAL_ISO_SHA256 \
  --options /absolute/reviewed-nonsecret-uefi-options.json
```

These commands require actual inputs; placeholders are not receipts. Options use
the existing exact installer option schema, with `boot_mode: "uefi"`. The fixed
context is `.local/phase2/native-mvp-installer-1`, with a fresh self-contained 64GiB
QEMU disk serial `TODDY-INSTALL-P2-1`. Existing global single-writer and host-space
admission checks apply. The runtime options/password/plan/cancel FD contracts and
explicit exact plan-hash confirmation remain unchanged.

Control from a separate terminal follows the existing flow, with `--mvp` on every
host invocation, e.g. `native_installer_live.py --mvp send review --request-id ...`,
then inspect the actual review before `send execute --confirm ACTUAL_PLAN_SHA256
--generated-password`. The password remains in the existing private RAM vault,
not a command argument or log. Collect all actual completion reports before
`finish`; uncertain/canceled writes retain their journals and are never replayed.

The read-only auxiliary snapshot includes the exact fixed
`mvp_installer_qualification.py` entry. The trusted boot credential selects that
entry and `/sources/stage/toddy-mvp-installer-native-inputs` for review, execute,
GUI and read-only collection. Hash-bound snapshot and controller records carry the
explicit MVP class with `g2_eligible: false`; standard mode rejects MVP inputs.
No request selects an executable or input directory.

After actual cold completion, the installed-owner controller's separate `--mvp`
route consumes the fixed disk/handoff and requires the existing two real detached
UEFI boots and owner-settings persistence companion. BIOS/recovery matrices and
full G2 acceptance remain pending; no one-boot receipt replaces those two boots.
