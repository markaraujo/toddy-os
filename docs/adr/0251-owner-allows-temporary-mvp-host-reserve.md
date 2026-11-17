# ADR-0251: Owner allows a temporary delivery host reserve

Date: 2026-11-16, America/Sao_Paulo
Status: Accepted by explicit owner response

The host had approximately108GB available, close to the existing100GiB+512MiB
reserve. The owner explicitly answered yes to reducing the temporary reserve to
60GB in order to finish the ISO and VM, preserving personal files and recovery
images. Use the more conservative60GiB+512MiB floor for this delivery's host
operations. This supersedes the100GiB host floor only for the current MVP/UI,
media transfer and install/owner-boot delivery path.

Do not delete unrelated files, replace accepted backings, bypass capacity
preflights or reduce the16GiB target reserve. Retain observed free space and
per-stage output/readback estimates. Existing standard/foundation contracts keep
their defaults. This permission neither creates an ISO nor supplies administrator
authentication for reinstalling VirtualBox. Restore the normal reserve policy
after this delivery; record any further capacity blocker rather than silently
lowering it again.
