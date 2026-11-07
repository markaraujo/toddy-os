# Phase 2 — Critical-path bottleneck review

Date: 2026-11-07. Repository review; no compilation, timing benchmark or guest
acceptance performed. Qualitative priority is based on dependency reachability
and inspected code, not measured hours. This refines the existing dependency and
night-execution reviews rather than introducing another implementation phase.

## 1. Repeated whole-target hashing: concrete implementation hotspot

[snapshot in run_step.py](../scripts/build/run_step.py) walks usr/etc/var/tools/
lib64/boot and reads every regular file to compute SHA-256. main calls it before
and after each recipe. Reusing this unchanged across a growing graphics/browser/
Qt target can repeatedly read large unchanged payloads. Existing safety/provenance
is valuable; do not remove snapshots merely to make a build faster.

First B01/B02 recipe preflight records snapshot duration and bytes/files traversed,
separately from compile/install/postcheck duration. If material, add a reviewed
Phase 2 path using declared staging/package manifests for new payload integrity,
plus an explicit way to detect undeclared target writes. Keep the one-writer lock,
input hashes, exit/postcondition and ownership checks. Continue the existing full
path until an alternative proves equivalent required coverage; a staged manifest
alone cannot detect writes outside staging. Do not trust mtimes alone as content
integrity, introduce a cache without invalidation, or change accepted H recipes.
A tiny synthetic fixture can qualify modified/removed/out-of-scope-file detection
before measuring a real recipe. Final image closure remains a full check once.

## 2. Build environment versus shipped roots: avoid rebuilding the wrong image

Maintain explicit package sets, with dependency closure and immutable identities:

| Set | Contains | Must not accidentally inherit |
| --- | --- | --- |
| Development target | Accepted foundation plus required compilers/build tools and integration packages | No claim this root is the release payload |
| Offline installed base | Accepted required base, minimal GNOME/browser/recovery, branding, lightweight setup | New Rust/Qt build tools, Node/Pi/executor, models, voice/plugins merely because they were used to build/test |
| Live installer | Bootable base plus native installer and required runtime dependencies | Private signing keys, personal accounts or build workspace |
| Agent acquisition set | Verified native agent/executor closure and separately selected inference/voice/plugins | Automatic model weights, credentials or permission grants |

Qt build tools may be build-only while necessary Qt libraries belong to the live
installer; classify actual dependencies rather than deleting all Qt indiscriminately.
Preserve the accepted foundation tools as required by the current plan. Build-only
exclusion concerns new build inputs, not a silent refactoring of G1.

B01 selects source-copy/package-assembly strategy against the accepted package
inventory and backend. B12 proves the actual offline installed root and later
acquisition. B13 tests the full supported experience after acquisition and also
the default offline base. The final delivery must make all required accepted
components available through verified artifacts/catalog, without forcing all of
them into the default installed root. Packaging availability is not runtime proof.
Do not copy a dirty development root and try to remove secrets afterward as the
only closure mechanism. Record package allowlists/forbidden runtime inputs before
assembling; verify resulting installed metadata, ownership and dynamic consumers.

## 3. Shared prerequisites and expensive branches

Before a large build, distinguish shared prerequisites from branch-specific tools:

| Priority | Boundary to expose early | Why it can dominate delivery | Small useful output |
| --- | --- | --- | --- |
| P0 | Actual VM/access/resources and snapshot costs | Without usable target/access no branch runs unattended | Verified clone, resource/job limits and per-stage timing |
| P0 | GLib/GIO/introspection/PyGObject against accepted Python | Shared UI/broker/executor dependency; late incompatibility affects many stories | Owned minimal binding import/async bus fixture, not completed GTK desktop |
| P0 | Calamares/Qt module requirements and boot/install backend | A late installer blocker invalidates the end-to-end delivery route | Pinned dependency/module graph and no-write probe; native Qt prerequisites may take real time |
| P1 | Graphics/Wayland/Mesa/Mutter/GNOME and browser toolchain | Potentially expensive compilation and broad dependency closure | First session checkpoint, then first browser; save each package |
| P1 | Node/Pi compatibility with existing crypto/runtime | Gates engine/tool branches | Tiny framed worker/tool fixture and exact transitive lock |
| P1 | Offline-root assembly and later native acquisition | Wrong root composition causes late reinstall/repackage work | Explicit root/catalog sets and disposable install path |

Do not assume Mesa/GNOME/Firefox share every compiler/JavaScript version; B01
resolves actual requirements from the frozen book and selected upstream inputs.
Do not introduce LLVM/Rust/WebEngine or extra Qt modules without a consumer edge.
Model/voice and optional IDE downloads stay outside the default compilation/ISO
critical path. Their scoped release proofs still must pass before G2.

## 4. Scheduling rule with measurable benefit

The nominal story order is a risk-first default, not a duration optimum. After B01,
B02 and B03 are eligible. If the measured graph shows desktop/browser compilation
will dominate, prioritize eligible B02's first-session/packages slice and checkpoint
it; switch to eligible headless work only at a safe boundary. Record the reason and
active story so the selector preserves it. Do not change prerequisites just to
make the schedule look faster. One guest/package writer remains mandatory.

While one build runs, source/license metadata review and validated download
preparation can overlap. Do not start another mutating recipe in that guest.
Separate compilation roots could enable later safe parallelism, but configuring
a distributed builder now is not justified without measured benefit. OOM and I/O
contention can erase the gain. Use bounded jobs and reuse exact package receipts.

B01 must not wait for final desktop, microphone quality, visual polish or installed
boot to complete contract acceptance. Conversely its native minimal spikes cannot
be replaced with host-only success. If prerequisites for a probe need compilation,
record that slice, cache the resulting packages and reuse them in B02/B12 rather
than rebuild just because the owning story changed.

## 5. Three focused actions at guest start

1. Inventory the accepted clone and measure resource plus runner overhead before
   launching expensive branches. No accepted compiler/libc rebuild.
2. Freeze one consumer-linked dependency graph and package/root sets; qualify the
   shared binding and installer risks before committing to a large desktop build.
3. Schedule the measured longest eligible branch, save per-package outputs and
   record compile/install/postcheck/snapshot times. Recalculate only after actual
   duration/failure/dependency changes, not every agent turn.

No additional owner preference is needed for these routine choices after explicit
Phase 2 start authorization. Missing access/legal/paid/destructive-host authority
still needs its concrete handoff. This review does not grant that start approval.

## Verification limit

Inspected current runner snapshot/hash calls, staging package ownership machinery,
B01/B02/B12/B13 ordering and existing root/offline requirements. Repository checks
validate links/consistency; they do not establish which branch is slowest in hours.
Stop expanding speculative preparation once the above inputs exist: the next
useful evidence is the authorized target measurement, not another framework survey.
