# Toddy OS — Midnight navy identity

The owner requested this navy environment refresh on 2026-11-07. It replaces
beige/brown as the predominant interface/background palette while preserving the
approved v2 logo and mascot **byte for byte**, including their warm natural fur.
Original identity: illustrated adult Shih-tzu, black glasses, dry-witted expression.
Do not redraw, recolor or regenerate these protected identity files.

| Asset | Role |
| --- | --- |
| toddy-os-logo.png | Exact original mascot and wordmark, unchanged |
| toddy-os-system-icon.png | Exact original transparent mascot, unchanged |
| toddy-os-wallpaper-dark.png | Midnight navy flowing matte ribbons; clear desktop space |
| toddy-os-wallpaper-light.png | Cool mist-blue companion; no beige background |
| toddy-os-wallpaper-dark-logo.png | Branded midnight navy companion with Toddy on the right |
| toddy-os-wallpaper-light-logo.png | Branded cool light companion with Toddy on the right |
| toddy-os-boot-background.png | Quiet navy login/boot surface; real logo/controls layered by the OS |
| toddy-os-desktop-preview.png | Simulated branded GNOME desktop |
| toddy-os-assistant-preview.png | Simulated native Toddy quick entry |
| toddy-os-task-preview.png | Simulated task/progress and Stop view |
| toddy-os-installer-preview.png | Simulated installer/AI setup scene |
| palette.json | Named colors and semantic usage |
| assets.json | Measured dimensions, alpha, role and SHA-256 |
| generation-record.json | Built-in generation prompts and screenshot provenance |

## Visual direction

Midnight #081426 and navy #10233F form the environment; restrained blue highlights
and cool white text keep it calm. The warm dog remains the recognizable human
part of the identity. Use generous spacing, legible typography and understated
depth rather than neon, busy gradients or heavy animation. The light variant uses
cool #EFF5FC surfaces. Status colors and keyboard focus remain distinct.

[UI tokens](../../ui/tokens.css), [interactive scenes](../../ui/preview.html) and
[installer stories](../../ui/installer-slides.html) are repository-native design
studies, not a web runtime requirement for the OS. The real implementation uses
GTK4/Libadwaita and supported GNOME integration. Avoid forcing a custom stylesheet
onto every third-party application.

## Honest previews and personality

All screenshot-style assets are HTML/CSS simulations and carry a visible
"Design preview — not a running build" label. They are not evidence that a desktop,
model, installer or driver already works. Replace them with actual guest captures
as features become available. The proposed dock is shown expanded; exact GNOME
version/Wayland behavior and icon implementations are pending runtime validation.

Toddy sounds like an affectionate, slightly needy nerd with four short legs.
Use short lines such as "I fetch files. You fetch treats." Humor supports the
experience; it never obscures progress, errors, uncertainty, disk plans or
administrative permissions. Portuguese localization follows the same personality
in the runtime product. Product examples in this repository remain in English.

## Provenance, dimensions and originals

The three navy backgrounds and two optional branded wallpaper variants were created
using the built-in image generation tool.
Actual output is 1672 x 941 PNG, approximately 16:9: **not a 4K or vector master**.
The branded variants use the background and approved mascot as generation
references; they are generated reproductions, not pixel-identical logo composites.
The protected logo and transparent mascot source files remain unchanged. Keep the
plain backgrounds available so users can choose their preferred amount of branding.

The UI concept captures are 1320 x 680 PNG rendered in a browser at a 1440 x 1000
viewport from ui/preview.html. Their original PNG mascot is composited by HTML,
not regenerated. This keeps the identity source intact.

[Archived v2 assets](archive/v2/README.original.txt), original metadata and prompt
records preserve the previous backgrounds. The archived README is verbatim
historical text; its original relative license link is not a navigable archive
reference. Current license: [CC BY 4.0](../../LICENSES/CC-BY-4.0.txt), Marcos Araujo /
Toddy OS, with modification notices and attribution retained. No trademark rights
are granted. Background changes do not alter the published foundation ISO.
