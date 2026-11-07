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
production assets live in assets/brand; the beige predecessors are archived.
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

config/community.json contains only the owner-provided public donation URL and
names explicitly approved for public acknowledgment. Keep donor email, account
identifiers, payment amounts/history and private consent evidence out of Git.
The default has no payment destination and no invented supporter entries. The
site displays a simple optional acknowledgment section, without paid tiers,
ownership claims or exclusive software benefits. Add a verified public PayPal
URL when the owner supplies it; the renderer refuses unrelated/non-HTTPS targets.
Names are HTML-escaped, deduplicated and never auto-published from payment data.
