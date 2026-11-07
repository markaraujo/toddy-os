# Website-only Toddy yawn, captions and LinkedIn verification

Date: 2026-11-07. Scope: static public portal only; no OS/harness runtime change.

## Change and invariants

The owner requested a bored, opinionated yawn when hovering the Toddy mascot,
ten rotating comment pairs, and a creator LinkedIn link in the footer. Generated
two alpha-transparent 1254x1254 expression frames with the built-in image tool;
full prompts and provenance are in assets/brand/generation-record.json. The
protected logo and original mascot are unchanged, and the original remains idle.

One short 2.6-second sequence uses CSS and a small local script, with a 2.7-second
reset guard. It starts on mouse hover, touch/click or native keyboard activation,
never loops automatically, ignores overlapping triggers and decodes optional
frames only on first interaction. Reduced motion retains the original still
image while comments remain interactive. Decode failure keeps the static original.
Captions rotate through ten pairs and use the existing six-language text catalog.

LinkedIn URL is exactly the public profile supplied by the owner:
https://www.linkedin.com/in/marcos-augusto-castro-araujo/ . The footer label is
localized and the link uses a separate tab with noopener/noreferrer.

## Focused verification

- make dashboard, make site and make check passed; 184 existing repository checks
  took 0.185 seconds in the final parent run. node --check ui/mascot.js passed.
- Original mascot SHA-256 remains c743d555c274b317f5832ee47609332d80f40a2d370b278b25706f60eedcf45c.
- Original logo SHA-256 remains eb46f81175fca698345870eee2101664ec613ff2de4c2430ef9b4fa27f3a1a81.
- Desktop Playwright, 1440x1000: initial frame requests zero, hero button 340x340;
  hover loaded exactly two PNGs. At peak, full-yawn opacity 1 and other frames 0.
  Visual hero/peak capture inspection passed; return-to-idle opacity was 1.
- A pointer click during the active sequence kept caption index 1, confirming
  no stacked replay. The idle state returned after the bounded sequence.
- Reduced-motion context, 390x844: ten keyboard activations produced ten unique
  comment pairs; zero expression downloads and state stayed idle.
- All six locales updated captions and LinkedIn labels; no horizontal overflow.
- Touch context, 390x844: one tap advanced once to index 1 and began animation;
  hero button stayed 135x135, no horizontal overflow.
- Aborted expression requests: idle original remained visible, fallback completed
  and no uncaught script error occurred. No external framework/telemetry is added.

These are basic browser checks, not universal device/FPS certification. Generated
expression variants are not pixel-identical original-art edits. No wallpaper,
installer screenshot, base logo, model, guest or OS image was changed.

## Parallel work boundary

The owner is configuring Patreon separately and explicitly asked the agent to
focus on the landing page. The unqualified PayPal route stays disabled and no
unpublished Patreon URL is advertised as a working support destination.
