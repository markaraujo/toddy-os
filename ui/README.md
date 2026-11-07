# Toddy OS navy UI studies

These are static design previews, not a working desktop, agent or installer.
Open [preview.html](preview.html) in a browser. The four scenes show minimal
GNOME-inspired desktop chrome, Toddy quick entry, visible task progress and a
humorous installer/first-run scene. Controls switch scenes and light/dark styling;
the pictured input, permissions, progress and model state are illustrations.

[tokens.css](tokens.css) is the canonical navy UI palette. Product integration
uses supported GTK4/Libadwaita styling and a small GNOME presentation surface;
these HTML/CSS studies do not introduce a web runtime into the future OS.
[preview.css](preview.css) implements the studies with local assets only.

The launcher dock is shown expanded for clarity. Exact Wayland placement,
keyboard shortcut conflicts and GNOME version behavior need runtime validation.
A label must remain on every exported concept image. Replace concepts with real
guest screenshots when corresponding features work; never use a mockup as evidence.

The exact original logo/mascot and its colors remain unchanged. Wallpaper
production assets live in assets/brand; the beige predecessors remain recoverable in Git history.
Installer copy is affectionate, nerdy Shih-tzu humor, kept out of destructive
warnings. English product examples are source copy; Portuguese localization is
part of B06/B09/B11/B12 runtime work.


## Public portal localization

The main page and surrounding preview/slideshow interface support English,
Brazilian Portuguese, Spanish, Simplified Chinese, Japanese and Russian.
`translations.js` contains the owner-approved locale strings; English remains
the canonical source. `i18n.js` works offline without a translation service or
framework. Browser language is used on a first visit, saved manual preference
takes priority later, and an explicit `?lang=` selects a shareable language.
Unsupported browser languages fall back to English. Storage failures do not block
selection; internal preview links carry the locale so navigation still works.

Example share links: `?lang=pt-BR`, `?lang=en`, `?lang=es`, `?lang=zh-Hans`,
`?lang=ja`, `?lang=ru`. The language picker uses native language names. The HTML
lang, page title, descriptions, accessible labels, interactive preview captions
and milestone titles/status/counts update together. English can be restored after
any switch without replacing task data or resetting controls.

Technical acceptance text and linked engineering documentation retain their
original English and are labeled accordingly. Simulated OS surfaces and the PNG
concept images deliberately retain English UI text; their surrounding descriptions
are localized. This is public website localization, not six-language OS support.
Real GNOME icon provenance and retained licenses are in
[assets/third-party/gnome](../assets/third-party/gnome/README.md).

## Optional public supporter acknowledgments

[config/community.json](../config/community.json) contains the owner-approved
Patreon creator URL and names approved for public acknowledgment. It drives the
current supporter galaxy automatically during publication. Do not put payment
amounts, email, account identifiers or private consent records in this file.
Names are HTML-escaped, deduplicated and never auto-published from payment data.
There are no paid ranks, ownership claims or exclusive software benefits.
The temporary hundred-name demonstration has been removed; the public wall
contains only approved names. See [data instructions](../config/README.md).

## Website-only mascot personality

The main-page hero uses the exact original mascot at rest. `mascot.js` loads two
optional transparent expression PNGs only after the first animation interaction,
then plays a short one-shot bored yawn with CSS. Mouse hover, touch/click and the
native button's keyboard activation are supported; there is no automatic loop,
telemetry, animation framework or OS-agent behavior. Overlapping interactions do
not stack. Switching to reduced motion or hiding the page resets the sequence;
reduced-motion users retain the original still image and can cycle comments.

Ten two-line comments rotate in a deterministic cycle and are localized through
the existing six-language catalog. Caption updates use text nodes. Image loading
failure retains the static original. The author LinkedIn link opens a separate
tab with noopener/noreferrer. This is portal decoration, not a new product runtime.

## Current supporter galaxy

The supporter page uses the separate happy portrait, floating text names,
continuous nod/head orientation and inline bone comets with tapered light tails.
There is no name-to-mascot connector or image switching. `supporters.js` manages
selection and motion preferences; `supporter-thanks.js` provides 100 authored
random replies in six languages. Both work locally without an AI service.
