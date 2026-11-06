# Error and correction log

Record: date, story, symptom, evidence, root cause, correction, verification, remaining risk.

## Bootstrap — GitHub authentication

- Symptom: GitHub CLI rejected an expired/invalid credential.
- Cause: previously stored account authentication was no longer valid.
- Correction: owner completed the GitHub device authorization flow.
- Verification: authenticated account query returned markaraujo and private repository creation succeeded.
- Secrets: no device code, token or password belongs in this repository.

No OS build failures exist yet. Do not turn planning risks into invented test failures.

## 2026-11-05 — H01 QEMU drive serial syntax

- Symptom: the first QEMU process exited 1 before boot; SSH was refused.
- Cause: QEMU 8.2.2 rejects serial as a qcow2 block-format option in -drive.
- Correction: use separate if=none block drives and virtio-blk-pci devices
  with serial assigned to the device; retain explicit qcow2 formats.
- Verification: inspect the corrected guest startup and lsblk serial evidence
  in H01. The failed process did not write a successful checkpoint.
- Recovery: remove only the exited toddy-builder container and restart with
  scripts/host/vm.py start; persistent disk files are preserved.
