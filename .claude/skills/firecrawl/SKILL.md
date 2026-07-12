---
name: firecrawl
description: Reference for the Firecrawl MCP tools already connected in this environment (firecrawl_scrape, firecrawl_crawl, firecrawl_map, firecrawl_search) — which one to reach for when haytham-opener-finder's Step A needs to crawl a lead's site or search for activity-floor material standalone (no prior process-lead Python walk). Not an install guide — there's no CLI to install and no API key to manage here, the MCP server is already connected.
---

# Firecrawl — MCP tool reference for this repo

This repo's primary crawler is the Python/Playwright walk (`main.py walk`),
used by `process-lead` (see `audit/`). Firecrawl only comes in when
`haytham-opener-finder` runs **standalone** — Haytham pastes a link
directly, with no `process-lead` run already done — and needs to crawl or
search live pages itself. Firecrawl replaced the generic web_fetch/
web_search tools there (split Jul 11, 2026) because it handles bot walls
and JS-rendered pages that a plain fetch chokes on.

## What's available

The Firecrawl MCP server is already connected in this environment — no
install, no API key, no browser auth flow. Reach for these tools directly:

- `firecrawl_scrape` — extract clean content from a single known URL. Use
  for the Site URL and any other linked page (sales page, freebie link,
  checkout) once you have the URL.
- `firecrawl_crawl` / `firecrawl_map` — discover a page's linked sub-pages
  when the walk needs to go beyond a single URL (e.g. finding what a
  Linktree or bio-link page actually links to before scraping each one).
- `firecrawl_search` — search the web for the lead's name, niche, or
  handle. In this repo it's used strictly for the **Activity floor** (last
  visible activity within ~3 weeks) — never as a proxy for the SMYKM hook.
  Hook material has to come from real IG evidence; that's
  `haytham-hook-finder`'s job, not a search result.

## When this applies vs. the Python walk

- `process-lead` chains through the Python walk already — that satisfies
  opener-finder's Step A, so don't run Firecrawl in that path; it's
  redundant with what the crawler already produced.
- Firecrawl is for opener-finder's own Step A only when it's invoked
  standalone (a link pasted directly, no `process-lead` run before it).

## What this repo does NOT use Firecrawl for

- No CLI install, no `FIRECRAWL_API_KEY` management, no browser auth flow —
  none of that applies here; the MCP tools are already live in the session.
- No app-code integration and no workflow-deliverable skills (SEO audits,
  lead lists, design clones) — those are Firecrawl product features
  unrelated to this outreach pipeline.
- **Never Instagram.** Firecrawl crawls the lead's Site URL and linked
  pages only. It must never be pointed at instagram.com — IG evidence
  stays screenshot-only, per the hard rule in `CLAUDE.md`.
