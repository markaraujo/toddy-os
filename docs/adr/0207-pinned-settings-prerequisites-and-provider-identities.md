# ADR-0207: Pinned Settings prerequisites and provider identities

Status: accepted · Date: 2026-11-10

## Context

The selected GNOME Control Center50.4 requires Tecla and GNOME Online Accounts
(GOA) backend SDKs. Its Tecla wrap follows HEAD; release recipes must use frozen
owned packages instead. Frozen BLFS13.1 gnome/gnome-online-accounts.html explicitly
requires another distribution to obtain its own Google client credentials rather
than redistribute the book's LFS identity. Optional account providers cannot make
offline desktop use depend on keys or expose another project's shared identity.

## Decision

Use frozen Tecla50.0, librest0.10.2/Soup3 and GOA3.58.1. Keep GOA backend,
introspection and Vala enabled; follow the book's supported kerberos=false choice.
GOA Google and Microsoft365 application integrations remain unavailable until a
Toddy-owned application identity and its distribution terms are qualified. Disable
those two provider switches and pass empty application identity values during the
initial build; do not use upstream or LFS shared application IDs. This does not
qualify or enable an account, grant credentials, or require provider signup now.
Preserve other supported backend functionality. Optional Fedora/Kerberos remain
unselected, without silently replacing required Settings functionality.

Run local upstream tests without external routes and record external-service
cases unexecuted. Tecla CLI initializes Adwaita before argument parsing; qualify
version/help under native Mutter/Wayland, then bind the identical installed binary
to that evidence. Do not treat CLI execution as a keyboard preview GUI pass.

## Evidence and consequences

Tecla native CLI and installation are recorded in B02-tecla-native-cli.json and
B02-tecla-install.json. Librest original local programs and actual installed C/GI
consumers are recorded in B02-librest-stage.json and B02-librest-install.json.
Complete Settings/online-account/desktop runtime acceptance remains pending.
Provider availability must stay truthful; enabling Google/Microsoft365 later
requires explicit application identity qualification and affected runtime checks.
No owner credential is requested for the offline desktop prerequisite build.

## Linux protocol prerequisite continuation

Control Center50.4 requires mm-glib on Linux and GNOME Bluetooth UI on x86_64
Linux. Frozen ModemManager1.24.2 defaults to MBIM/QMI; keep those protocol features
and qualify the selected libmbim1.34.0/libqmi1.38.0 inputs instead of disabling
required panels to pass a build. QRTR follows the book's explicit disabled
option. Source/SDK qualification does not establish modem hardware support.
Existing scratch input/worker bindings must preserve fixed reserves and original
cache/source identities; no foundation reconstruction or physical-disk operation.
