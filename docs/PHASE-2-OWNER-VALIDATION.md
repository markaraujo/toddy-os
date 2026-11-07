# Phase 2 — Short owner validation guide

Prepared checklist, not recorded results. Use only a delivered experimental image
with its exact version/hash, recovery instructions and declared supported features.
Basic developer boot/install, authorization, credentials, cancellation/replay and
recovery gates remain mandatory before delivery. Owner use expands coverage;
it does not replace missing essential developer tests.

Run the rows relevant to the delivered slice once. If something fails, stop that
path and report it; do not spend hours repeating it or installing on a physical
disk to diagnose a VM failure. No paid API or personal credentials are required.
Use a blank disposable VM disk for installation and fictional data for agent tests.

| Delivery | Try | Expected | Recovery / report |
| --- | --- | --- | --- |
| Desktop/offline install | Disconnect network, install to blank VM disk; detach ISO, boot twice; create/reopen a file | Usable desktop, persistent file, setup entry explains absent agent | Restore supplied VM checkpoint; record failing screen/boot stage |
| Later agent setup | Connect network; review/download supported agent components through setup | Verified native packages; setup resumes without reinstalling OS; no silent model download | Retain desktop; leave failed choice pending and report sanitized error |
| Entry and text | Open launcher/shortcut and submit a harmless system-summary request after setup | Provider/setup status truthful; task result corresponds to actual observation | Reopen ordinary app if shortcut fails; report exact request and version |
| Stop/reconnect | Cancel a harmless task and close/reopen the UI | Existing task visible; no duplicate execution or invented rollback | Leave uncertain task unresolved; do not manually replay a mutation |
| Personalization | Change tone/language, try an invalid config, restore previous revision | New tasks use valid revision; invalid edit preserves working profile | Use last-known-good/reset; do not upload private profile files |
| Memory, when delivered | Save one fictional preference, inspect/edit/delete it | Correct profile sees it; deleted preference no longer used | Disable memory; report the sequence without private transcripts |
| Options | Skip AI; inspect one supported optional app/pack | Choices and actual install state agree; unsupported choices unavailable | Keep choice deferred; use documented package rollback |
| Voice/plugins, when delivered | Try supported EN/PT push-to-talk or the included harmless local plugin | Text remains usable; Stop and missing-device messages work | Disable optional component; report device/model IDs and symptom |
| Appearance | Inspect light/dark, focus, larger text and reduced motion | Readable controls; coherent art; no animation obstructs warnings | Use upstream appearance/static fallback and report cropped/unreadable area |

A suggested first session covers desktop and setup only; optional rows wait until
that feature is delivered. This is not a promised duration or mandatory repeated
hardware/provider matrix. Never test deletion, driver replacement or arbitrary
root commands on personal data as a quick acceptance exercise.

Report: image/tag/hash; VM or actual hardware (never conflate them); relevant smoke
ID; steps; expected/observed; passed/failed/deferred/not-run; elapsed time if
measured; sanitized screenshot/error. Remove keys, user paths, email and private
contents. Use SECURITY.md for suspected vulnerabilities rather than posting
sensitive evidence publicly. Broader hardware, suspend/multimonitor, model quality,
long sessions and accessibility coverage remain the owner-use backlog in
[validation](PHASE-2-VALIDATION.md).
