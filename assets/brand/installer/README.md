# Installer and boot visual handoff

Repository-prepared artwork direction; no boot/installer runtime is installed.
The [existing slideshow](../../../ui/installer-slides.html) is the single review
surface for boot, installation scenes and completion. It is an HTML design study,
not a requirement to add a browser runtime or web engine to the installer.

## Continuous experience

| Stage | Art/composition | Integration owner and condition |
| --- | --- | --- |
| Boot | Existing navy boot background, exact static mascot, small opacity dots; no percentage invented from a timer | B02/B11 select a compatible supported boot presentation; preserve diagnostic/text fallback and zero artificial hold |
| Welcome | Same navy identity, native language/accessibility controls and concise greeting | B12 native Calamares branding/modules; no Ubuntu assets or modified mascot |
| Choices and review | Native readable locale/user/disk plan, optional AI/apps/third-party packs; decoration stays secondary | B12 actual capabilities and source/license review; no joke in disk confirmation |
| Installation | Four existing GNOME/Toddy scene concepts, small crossfade/translation, independent readable progress | B11 scene assets, B12 native slideshow; real status comes from installer events, not the scene timer |
| Failure/recovery | Native error, actual completed changes, next recovery action; pause decorative motion | B12/B13; no cheerful success illustration on a failed installation |
| Completion | Static mascot and short welcome; a subtle one-time reveal | B12 only after verified install; native restart choice, no forced restart or countdown |
| Installed desktop | Same navy wallpaper/catalog and assistant identity | B02/B11; no extra welcome animation delaying an ordinary login |

Existing artwork sources, dimensions, licenses and protected hashes remain in
[the asset manifest](../assets.json). Do not duplicate or modify the original
mascot. These sources are used by reference:

- `assets/brand/toddy-os-boot-background.png`
- `assets/brand/toddy-os-system-icon.png`
- `assets/brand/toddy-os-desktop-preview.png`
- `assets/brand/toddy-os-assistant-preview.png`
- `assets/brand/toddy-os-task-preview.png`
- `assets/brand/toddy-os-installer-preview.png`

The four GNOME images remain labeled concepts. Replace them with actual captures
of the locked guest and installed icons as each feature becomes available. Native
layout dimensions, crop/small-screen scaling and installer toolkit behavior are
not frozen by the browser preview. No splash engine is selected solely for art.

## Motion and copy

[motion.json](motion.json) records reusable timing, static fallback and integration
conditions. Website motion is an approximation for review; boot/native adapters
must implement supported equivalents or use the static art. No video, GPU-heavy
particles, audio, raster frame sequence or permanent background animation is
required. Never delay boot or disk operations to finish a decorative sequence.
The browser study changes scenes manually; the future native slideshow may rotate
with pause/navigation, independent of real progress. Reduced motion is static.

The existing scene narratives cover desktop, assistant entry, visible task control
and optional AI/setup. Keep their affectionate nerdy dog personality. New short
source copy for the bookends:

| Context | English | Brazilian Portuguese |
| --- | --- | --- |
| Welcome | Your new home. My new keyboard to sit on. | Sua casa nova. Meu teclado novo para deitar. |
| Completion | Welcome home. I saved you a spot beside me. | Bem-vindo a casa. Guardei um lugar do meu lado para você. |

These lines accompany native headings/status; they do not replace verified
completion or critical controls. Additional portal languages live in the existing
website catalog; native EN/PT copy remains the runtime scope.

## Merge into implementation, not a separate art project

B01 checks actual native installer/boot feasibility before toolkit-specific
exports. B11 validates sources, exact guest schemas, readability and motion/static
variants. B12 wires real progress, errors, review and verified completion to the
same presentation. The website files stay outside the native branding payload;
package only selected sources/native adapters through declared ownership.
S17-A/B and B12/B13 retain runtime acceptance. Browser review never completes them.

## Separate live installer package inputs

`scripts/build/phase2/branding_stage.py installer <repository> <new-stage>` stages
`calamares-branding-toddy` separately from the installed desktop artwork package.
Its native location is `/usr/share/calamares/branding/toddy`. Approved source
masters are copied unchanged. `scenes.json` binds two real B02 captures to their
committed evidence hashes and keeps assistant/task concepts explicitly labeled
in English and Portuguese. These captures describe the accepted B02 guest, not a
new installed candidate or completed B11/B12.

The branding descriptor and slideshow API were checked directly in the frozen
[Calamares3.4.3 release archive](https://codeberg.org/Calamares/calamares/releases/tag/v3.4.3),
SHA-256 `144cbbf6bdcebfb21685950db4f0777218519df095f62f4aa392f28348110d18`,
at `src/branding/default/branding.desc`, `show.qml` and `src/branding/README.md`.
The default staged descriptor uses one static actual desktop capture. It needs
no new QML dependency, timer, web engine, log upload or concept-success claim.

When the final native QtQuick closure is present, trusted packaging may request
`stage_installer(..., qml_enabled=True)`. This stages the original Toddy API2 QML
view, with visible provenance notice, manual keyboard/mouse scene controls and
static/paused reduced-motion defaults. It performs no HTTP/XHR fetch, reboot or
installation dispatch and derives no progress/success from its optional decorative
timer. Enabling source staging does not prove QML compilation or visual behavior.
Native Qt/display/scale/focus/high-contrast, language change and actual installer
event/error/completion checks remain required before activating or accepting it.
