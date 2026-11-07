# Public community data

Edit only `community.json` to update the supporter wall. `patreon_url` is the
owner-approved creator URL. `supporters` is an array of approved public display
names, each nonempty, unique and at most 80 characters. Keep an empty array until
someone explicitly agrees to be listed. Do not store payment details, email,
Patreon IDs, messages or evidence of consent in this public file.

Example (fictional names, for illustration only):

```json
{
  "patreon_url": "https://www.patreon.com/ToddyOS",
  "supporters": ["Example display name", "Another example"]
}
```

Edit and commit only this JSON, then push to main through the authorized workflow.
GitHub Pages builds the supporter wall from the current JSON automatically.
No generated name list needs to be committed. For a local preview, run
`make dashboard site check`.
The public wall adapts from its empty state to a responsive grid without editing
HTML/CSS. Every name has equal visual weight and stays untranslated. Removal is
the same process: remove the name from the array and publish. This is static-site
build-time data, not a live Patreon API sync, and it requires no backend or keys.

`supporter_preview_count` controls the separate `supporters-preview.html` demo
(default 100; maximum 500). Its numbered fictional names are never added to the
real wall or supporter array. The demo is clearly labeled and asks search engines
not to index it. Edit only this number to try another layout size.
