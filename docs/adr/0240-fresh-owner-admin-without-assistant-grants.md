# ADR-0240: Fresh OS owner administration stays separate from assistant grants

Status: source implementation; installed native qualification pending
Date: 2026-11-16
Scope: installer account identity and optional executor package activation

The fresh installed owner must be able to authenticate native package setup and
the fixed Polkit owner helper after installation. The installed root password is
locked and the frozen native administration group is `wheel` GID97 (the retained
live-account baseline). Current native B04 owner evidence verifies administrator
authentication with membership in that group. Creating only the owner's primary
group would leave first-login administration inaccessible.

Create the fresh owner with its selected primary UID/GID and supplemental wheel
membership, after verifying the exact empty native group baseline. Verify that
only the fresh owner is in wheel during installed hygiene audit. Never inherit a
live/builder administrator. Passwords still travel only through the protected
account pipe/native chpasswd stdin. No password appears in the plan or journal.

OS administrator membership is not an assistant session/standing grant. No root
executor database, live installer journal or owner provider configuration may be
inherited into the installed image; hygiene now checks the current executor
state path as well as the historical one. The installed owner must independently
authenticate each owner-policy action under the qualified revocation contract.

The optional executor package must not install a multi-user.target.wants enable
link. Remove that source-stage link to match the explicit reviewed acquisition
contract. The fixed systemd unit and systemd-only D-Bus activation remain; the
direct uncontained fallback stays `/usr/bin/false`. Acquisition creates no grant,
model, credential or automatic user-agent activation. Explicit activation and
native install/upgrade/removal postconditions remain separate qualification.

Focused account/command and stage fixtures verify these guards, not a completed
disk installation or physical-machine login. Actual blank-guest first login,
fresh-password administrator authentication and pending-choice acquisition must
pass before the installer/release is accepted.
