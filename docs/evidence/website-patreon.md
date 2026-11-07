# Patreon support campaign — 2026-11-07

The owner requested a Patreon presence on the public portal after reporting the
first post published. The creator URL uses the owner-supplied ToddyOS identity:
https://www.patreon.com/ToddyOS . The first post is linked without tracking
parameters. Browser/web verification of Patreon itself remains blocked by a
Cloudflare 403; this is not evidence of checkout, subscription or payout success.

Added a navy campaign card, official unmodified Patreon symbol, explicit external
CTA, first-post link, optional public-name acknowledgment and hero/footer links.
No prices, supporter tiers, exclusive software, deadlines or one-time payment
availability are invented. The Patreon page presents the actual configured
membership/support options. The known-broken PayPal checkout remains disabled.
No tracking scripts, Patreon embeds or payment processing run on the portal.

The official symbol's source and trademark terms are recorded under
assets/third-party/patreon/README.md. The explicit public export includes only
that symbol and its attribution. Six-language copy covers the complete new card.

Playwright checked the local export in all six languages at 320, 390, 768 and
1440 pixels: 24 combinations without right-edge or document overflow. Inspected
the Portuguese campaign screenshot at /tmp/toddy-patreon-section.png. The CTA
resolves to the approved HTTPS creator URL and translates correctly. Existing
184 checks and JavaScript syntax validation passed. No guest OS changes.
