# ADR 0247: Publish package artifacts before final-origin acquisition qualification

- Status: accepted
- Date: 2026-11-16

## Context

The owner authorized Phase2 implementation and experimental release/portal work.
Native acquisition qualification pins the exact source line and signed InRelease.
A file: component proof cannot establish a later HTTPS production origin. The
existing Phase2 ISO release utility correctly requires final-ISO native/G2
technical evidence, including actual full acquisition flow. Requiring that ISO
proof before any package repository URL exists creates a bootstrap cycle.

## Decision

Publish a separately scoped experimental **package-artifact** prerelease first,
using real native archives, the independently pinned public trust, finite signed
APT metadata, reviewed corresponding source/licenses, exact checksums and actual
public download verification. The parent selects v0.2.0-preview.1 as its intended
tag; source code does not fabricate a tag, assets, receipt or reachable origin.
This artifact milestone accepts only archive/signature/legal/download custody. It
awards no B story, changes no progress weights and does not pass G2 or advertise
Setup readiness. It includes no ISO. Actual publication and owner credentials
remain coordinator-controlled.

The new package-only custody utility and optional portal block are independent
of the existing final-ISO release utility and foundation download. Public metadata
is created only after retained actual published GitHub asset records, sizes,
digests and independent downloads match reviewed local artifacts. The portal
states the incomplete desktop ISO, G2 and installed-user acquisition qualification
in all six supported locales. Missing public metadata leaves the portal unchanged.

Once the real HTTPS repository is reachable, generate candidates for that exact
origin and run actual component qualification, signed preview catalog and fresh
production helper/UI full-flow qualification. Preserve source, InRelease,
package, code and public trust pins throughout. Final catalogs/ISO may reference
that immutable package origin. A new origin or re-signed Release requires new
qualification; offline evidence is never renamed as online evidence. Repository
expiry is real; tests must finish within the signed validity window or restart
with a new honest metadata generation and qualifications.

## Consequences

The package-only release has its own source/license review, public custody and
portal deployment evidence. It is not an alternate final-release acceptance
path. Final ISO publication continues through unchanged B13/G2 gates. Do not add
assets to or replace a verified immutable package release silently; later ISO or
catalog distribution uses a separate release task/tag. No installed assistant
receives project publishing credentials, keys or permission.
