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

## 2026-11-05 — H03 sanitized PATH and target identity probe

- Symptom: runner launch raised FileNotFoundError for runuser before a recipe ran.
- Cause: the deliberately minimal /usr/bin:/bin PATH excludes /usr/sbin/runuser.
- Correction: invoke /usr/sbin/runuser explicitly. Confirmed the probe file was
  absent and preserved the interrupted running record before retry.
- Verification: success, recipe-exit-42 and postcondition-exit-42 cases all pass;
  only success has a success marker. Logs are linked in H03 evidence.
- Separate read-only probe correction: virtio disk serial was queried initially
  at an absent sysfs device/serial path. Use lsblk's SERIAL column; the failed
  guard exited before changes. Target preparation uses the verified method.

## 2026-11-05 — H04 source-directory mode after transport

- Symptom: first H04 binutils attempt exited 1 creating sources/evidence.
- Cause: transporting the source cache with tar also applied the transport
  directory's 0755 mode to /mnt/lfs/sources, replacing required 1777 mode.
- Correction: restored sticky writable mode, verified access as lfs and added
  that postcondition to target preparation. Future source transport uses tar
  --no-overwrite-dir to preserve the target directory's metadata. Added guest
  swap to fstab so reboot retains the selected memory budget.
- Verification: failed attempt recorded zero changed installed paths and no
  success marker; prior logs/failed record preserved in runner history before
  retry. Corrected H04 executes with lfs and validated target guards.

## 2026-11-05 — Security-patch applicability experiment

- Symptom: initial Glibc security-patch validation could not find a relative
  input path, then a dry run reported later NEWS hunks failing.
- Cause: patch changes its working directory with -d; use an absolute input
  path. The patch is a sequence of commits; dry run does not apply the earlier
  NEWS changes required by later commits.
- Correction: verified baseline hashes, used absolute patch paths and actually
  applied the sequence to a disposable source copy, not the build root.
- Verification: all 49 patches applied with exit 0 and no rejected hunks.
  No package version or running build changed; final regression tests pending.

## 2026-11-05 — Xz security-input publication endpoint

- Symptom: multi-command retrieval attempts ended with HTTP 403.
- Diagnosis: archive and signature downloads had succeeded; the failing
  operation was the official signing-key endpoint, not the source artifact.
- Correction: inspected downloaded sizes and compared archive SHA-256 to the
  publisher's release-asset digest. They match. Retained signature, recorded
  PGP verification as unperformed and pinned the verified source hash.
- Verification: Xz 5.8.4 hash 4ce24038fd4221e0d13bc1a2de7a4db56e90b92b3bf75321f6c14be73f65de4b.
  No authentication bypass or global trust-store change was used.
