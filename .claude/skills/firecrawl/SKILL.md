---
name: firecrawl
description: Reference for the Firecrawl MCP tools already connected in this environment (firecrawl_scrape, firecrawl_crawl, firecrawl_map, firecrawl_search) — which one to reach for when process-lead's Step 1 (the primary machine walk) or haytham-opener-finder's standalone Step A needs to crawl a lead's site, capture screenshots, or search for activity-floor material. Not an install guide — there's no CLI to install and no API key to manage here, the MCP server is already connected.
---

# Firecrawl — MCP tool reference for this repo

Firecrawl is the **primary fetcher** for the machine walk (`process-lead`
Step 1, added Jul 12, 2026) — cheaper, faster, and better at bot walls/
JS-rendered pages than the local Playwright browser it replaced as the
default. The Python analysis layer (`audit/evidence.py`, `checks/*.py`,
`gates.py`, `vision_gate.py`) is unchanged either way — it never cared
which layer did the fetching, only that it gets HTML strings and
screenshot files. Playwright (`python main.py walk`) stays available as an
explicit fallback (see process-lead Step 1) for the one thing Firecrawl's
stateless scrape can't do: live click-discovery on JS-only buttons.

`haytham-opener-finder`'s standalone Step A (Haytham pastes a link
directly, no `process-lead` run first) also uses Firecrawl, for the
lighter, packet-free ad-hoc walk — that usage predates and is separate
from process-lead's Step 1.

## What's available

The Firecrawl MCP server is already connected in this environment — no
install, no API key, no browser auth flow. Reach for these tools directly:

- `firecrawl_scrape` — extract clean content from a single known URL, and
  (via `formats: ["screenshot"]`, `screenshotOptions: {fullPage: true}`,
  and the top-level `mobile: true` flag for the mobile viewport) capture
  the desktop/mobile screenshots process-lead's vision-pass gate requires.
  Use for the Site URL and any other linked page (sales page, freebie
  link, checkout) once you have the URL. `waitFor` (ms) helps on
  booking/checkout pages with async-loading embeds (Calendly-style).
- `firecrawl_crawl` / `firecrawl_map` — discover a page's linked sub-pages
  when the walk needs to go beyond a single URL (e.g. finding what a
  Linktree or bio-link page actually links to before scraping each one).
  In process-lead's Step 1, prefer `python main.py discover-links` on the
  HTML you already fetched instead — it applies this repo's actual
  scope/priority rules (same-site vs. noise vs. external-platform), which
  `firecrawl_map`'s generic URL discovery doesn't know about.
- `firecrawl_search` — search the web for the lead's name, niche, or
  handle. In this repo it's used strictly for the **Activity floor** (last
  visible activity within ~3 weeks) — never as a proxy for the SMYKM hook.
  Hook material has to come from real IG evidence; that's
  `haytham-hook-finder`'s job, not a search result.

## When this applies

- **`process-lead` Step 1** — the primary path for every automated lead
  (batch or single). Fetch via `firecrawl_scrape`, hand the HTML to
  `python main.py discover-links`/`discover-checkout` for the next URLs to
  fetch, then `python main.py ingest` to build the evidence packet. See
  that skill's Step 1 for the full loop.
- **`haytham-opener-finder`'s standalone Step A** — the lighter, packet-free
  ad-hoc path when Haytham pastes a link directly.
- Not needed for a lead that already has a completed process-lead Step 1
  — opener-finder just consumes that packet.

## What this repo does NOT use Firecrawl for

- No CLI install, no `FIRECRAWL_API_KEY` management, no browser auth flow —
  none of that applies here; the MCP tools are already live in the session.
- No app-code integration and no workflow-deliverable skills (SEO audits,
  lead lists, design clones) — those are Firecrawl product features
  unrelated to this outreach pipeline.
- **CTA click-discovery.** Clicking JS-only buttons to find hidden
  destinations (Stan-store product cards, sales-page CTAs) needs a live,
  interactive session that a stateless scrape can't replicate. Process-lead
  falls back to `python main.py walk` (Playwright) for leads that need it
  — see that skill's known-gap note.
- **Never Instagram.** Firecrawl crawls the lead's Site URL and linked
  pages only. It must never be pointed at instagram.com — IG evidence
  stays screenshot-only, per the hard rule in `CLAUDE.md`.
