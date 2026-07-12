# Funnel Auditor — outreach automation system

This repo is the machine layer of Haytham's cold-outreach system for
parenting/faith-based coach leads, plus the Claude skills that orchestrate it.

## The pipeline in one line

Manual IG sourcing (Haytham logs the row in Notion + attaches his IG
screenshots to the page body) → `/batch-audit` (scheduled Routine or "work
the queue"; one lead-processor agent per lead, ~3 in parallel, cap 15) →
per lead: machine walk (Firecrawl-primary fetch, Playwright fallback) →
**mandatory vision pass over the screenshots** →
floors → opener-finder (lane + finding + innocent explanation, stops there
— no hook) → Notion write → email address → **held** (no Gmail draft yet)
→ Haytham runs `haytham-hook-finder` on the lead (pulls real IG evidence,
writes just the SMYKM hook line, or confirms none exists) → Haytham asks
for the draft → automatic Gmail DRAFT (SMYKM opening A with the hook, or
opening B if none was found) → Haytham reviews in Gmail and sends by hand
→ `/pipeline-tick` (replies, due follow-ups auto-drafted, send queue)
daily.

Haytham's only manual jobs: sourcing (with IG screenshots attached),
running `haytham-hook-finder` on each Audit Ready lead before it can draft
(split from opener-finder Jul 11, 2026 — a hook built from a web search
read generic; a real hook needs real IG evidence, so it's now a separate,
manually-triggered skill that gates the draft rather than running inside
the automatic chain), reviewing and sending drafts from Gmail, and
confirming sends for logging. Single pasted leads still go through
`/process-lead` directly, with the same hold.

## Hard rules (non-negotiable)

- **Never automate anything against Instagram.** No fetching instagram.com,
  no scraping, no DMs. Haytham lost an account to IG automation; sourcing is
  manual by design.
- **Never send an email.** The system ends at Gmail drafts. Sending is human.
- **Never invent findings.** No verified finding → no opener. Lane 2/3 exists.
  Machine check flags are candidates only — a flag that fails the vision
  pass (visual confirmation on the screenshot) is dead and stays dead.
- Notion is the source of truth for pipeline state, not chat memory.
- A Gmail draft is not a send. Drafts are created automatically once the
  lead is eligible; Status / Touch # / Last Contacted / Email Thread Log
  move only after Haytham confirms an email actually left.
- **No draft before a hook decision.** `haytham-email-draft` and
  `process-lead` hard-block on a `SMYKM hook:` line that still reads "not
  run yet" — every fresh lead lands there, so no Gmail draft gets created
  until Haytham runs `haytham-hook-finder` on that lead and it resolves
  the line (a real hook, or a confirmed "no hook found"). (Added Jul 11,
  2026.)
- **Before any Notion page update that uses search-and-replace
  (`update_content`), fetch the page first** to confirm the current literal
  content format — Notion's enhanced-markdown escaping (`\$`, auto-linked
  domains, etc.) breaks naive search-and-replace assumptions. If the fetch
  shows escaped or non-plain formatting, rewrite the full body
  (`replace_content`) instead. (Added Jul 10, 2026, after a failed write +
  forced recovery fetch.)
- **A dispatched subagent (lead-processor or otherwise) gets one resume, not
  two.** If it comes back with a status-only reply — no new tool calls, no
  work product since its last turn — take the task over directly instead of
  nudging it again; see `.claude/skills/batch-audit/SKILL.md` Step 2. (Added
  Jul 10, 2026, after a stalled-agent loop cost 84.5K+ tokens for zero
  output.)

## Key pieces

- `main.py discover-links` / `discover-checkout` / `screenshot-name` /
  `ingest` — the Firecrawl-primary fetch path (added Jul 12, 2026): Claude
  fetches via Firecrawl MCP tools, these commands classify links (scope/
  priority) and build the evidence packet from pre-fetched content. Python
  owns all scope/analysis logic regardless of which layer fetched the page.
- `main.py walk <url> --name --handle --followers` — the original
  Playwright crawl + evidence packet under `evidence/<slug>/` (packet.md,
  evidence.json, page text, screenshots). Kept as the documented fallback
  for leads Firecrawl can't handle (persistent bot walls, or JS-button
  click-discovery on bio-link aggregators / sales-course-booking pages —
  a stateless scrape can't click things).
- `audit/` — checks, extraction, Gate 0 floors, packet builder; all fetch-
  layer-agnostic (works identically whether fed by Playwright or Firecrawl).
  `crawler.py` still holds the Playwright fallback + the link/checkout
  classification logic both fetch paths share.
- `.claude/skills/process-lead` — the per-lead contract everything else
  runs: walk (Firecrawl-primary) → vision pass → floors → opener → **held**
  at the Gmail draft until `haytham-hook-finder` resolves the hook.
- `.claude/skills/batch-audit` — batch orchestrator: pulls Researching rows
  from Notion, spawns one `lead-processor` agent per lead (~3 parallel,
  cap 15), verifies the writes landed, delivers one batch brief listing
  which leads need `haytham-hook-finder` before they can draft. Fired by
  the lead-queue Routine or on demand.
- `.claude/agents/lead-processor.md` — the per-lead subagent and its
  structured return block.
- `.claude/skills/pipeline-tick` — daily ops loop (replies/follow-ups/queue);
  due follow-ups auto-draft to Gmail, never stacking on an unsent draft to
  the same address.
- `.claude/skills/haytham-opener-finder` — the walk: Gate 1, 5 stops, filters,
  lanes, Notion page body format. Crawls via Firecrawl when run standalone
  (not chained from process-lead's walk). Stops at the finding + innocent
  explanation — does not find the SMYKM hook.
- `.claude/skills/firecrawl` — MCP tool reference (scrape/crawl/map/search)
  for process-lead's Step 1 (primary) and opener-finder's standalone Step A.
  Already connected in-session; no install or API key needed here.
- `.claude/skills/haytham-hook-finder` — separate, manually-triggered skill:
  pulls real IG evidence for an Audit Ready lead and writes just the SMYKM
  hook line to Notion. Never part of the automatic chain.
- `.claude/skills/haytham-email-draft` — voice, mechanics, gate, logging
  rules. Drafts with SMYKM opening B (no hook) by default; opening A only
  once haytham-hook-finder has written a real hook.
- `.claude/skills/haytham-funnel-auditor` — deep audit (Loom/call prep).

Notion Lead Pipeline:
- Data source ID (MCP): `collection://c6209e29-55ef-4781-b735-73b2a254e34f`
- Database ID (REST API): `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`

## Environment notes

- Firecrawl MCP server is the primary fetcher — already connected in
  managed sessions, no setup needed.
- Chromium/Playwright is only needed for the `main.py walk` fallback path.
  Managed cloud sessions: Chromium lives at `/opt/pw-browsers/chromium`
  (the crawler auto-detects it; override with `FUNNEL_AUDITOR_CHROMIUM`).
  The MITM egress proxy resets Chromium's post-quantum TLS handshake — the
  crawler writes a Chromium enterprise policy to disable PQ/ECH
  automatically.
- Local (WSL): `pip install -r requirements.txt && playwright install chromium`
  (only needed if you expect to exercise the Playwright fallback).
