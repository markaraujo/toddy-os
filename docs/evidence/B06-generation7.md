# B06 generation 7: live dconf mode stop

Date: 2026-11-18. Local candidate evidence only; no ISO, boot, installation or G2 acceptance.

- Installer9/version7 native install and postcheck passed with unchanged qualified Calamares C++ module. Projection6, unsigned export8 (329 packages, 918 assets), exact host transfer, two independently verified public signatures and native public signature verification passed. Inputs4 was prepared from the signed export.
- Failed generation5 root was fully archived to `.local/phase2/mvp-live-failed5-candidate-root-custody-5/`; 6,183,809,024 guest bytes were recovered after full host proof. The generation6 root then unpacked, qualified all 19 caches with zero blockers, passed independent review of 329 configured packages and 150,280 complete image entries, and passed native finalization. Its live stage created `/etc/dconf/db/ibus` through global `dconf update`, outside the permitted delta. The partial root was archived to `.local/phase2/mvp-live-stage6-candidate-root-custody-6/` with full proof before retirement, recovering 6,183,936,000 guest bytes. Its stage intent remains.
- Guest copies of exports6 and5 were removed only after all 920 files in each exactly matched their verified host copies. Their original export receipts were also copied and hash-checked on the host. Guest retirement intents and host inventories remain in private logs. Active export8 and all accepted backings remain.
- Generation7 used the same signed inputs4 and fresh fixed root. It unpacked and configured 329 packages, qualified with zero blockers, reproduced the reviewed generated and complete-image map hashes, and passed finalization. A disposable overlay showed targeted `dconf compile` created only the Toddy live database and did not mutate the retained lower root. The actual live stage stopped because `/etc/dconf/db/toddy-live` was root:root mode 0600 while its contract requires 0644. No live-profile receipt exists; its live-profile intent and partial reviewed root are retained. The candidate root is not accepted or replayable.
- A second disposable overlay confirmed that exact mode normalization to 0644 preserves the retained lower root and does not create an IBus database. Source now verifies the output is a root-owned, single-link regular file on the target device before changing its mode; a write-once failure receipt records unexpected paths or output metadata on future failures. This source correction has not been executed on a fresh live root.

The bounded stage attempt limit is reached. Before another live generation: preserve generation7's partial root with complete host proof, calculate the media admission bound and guest capacity before a new root, then use one fresh generation with the corrected source. Do not equate resource/finalizer success with a bootable ISO or B06 acceptance.

Read-only media sizing on the partial generation7 root counted 150,293 entries,
6,837,325,824 bytes of expanded snapshot bound and a 33,002,004,480-byte
compression admission. Guest free space was 20,229,652,480 bytes, short by
12,772,352,000 bytes. The next slice must close that deficit before another
root. This is a measured capacity stop, not evidence that compression failed.
