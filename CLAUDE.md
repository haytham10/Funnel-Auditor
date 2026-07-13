# Funnel Auditor — outreach automation system

This repo is the machine layer of Haytham's cold-outreach system, plus the
Claude skills that orchestrate it. Two tracks run in parallel:

- **UAE track (active — all new leads go here).** UAE-based solo coaches
  and course creators with real funnels. Sourced web-natively, worked
  through the UAE Lead CRM, priced in AED, with one deliberately new step:
  **price discovery before any priced offer.**
- **Parenting track (live threads only).** The original
  parenting/faith-based pipeline: 125 cold-touched leads, ~9% reply rate
  by lead (above benchmark), zero closes. No new leads get sourced into
  it; existing warm threads get worked to a conclusion via
  `pipeline-tick`. Its IG sourcing channel is dead (account permanently
  banned Jun 22, 2026).

Why the UAE track exists, in one line: the parenting pipeline proved the
opener mechanic and nothing after it — only 2 of 11 repliers ever surfaced
a real priced objection, and nobody was ever asked what they would pay. So
this track holds the mechanic constant, swaps the market, and makes price
discovery a load-bearing, code-enforced step. The method files live in
`docs/uae-track/` (CRM spec, offer, targeting, outreach method) — the
files are the method; **Notion is the source of truth for live state.**
When you need to know what is actually happening, query the CRM, not the
docs.

## The UAE pipeline in one line

`source-leads` (Day 1: 5 web channels → CRM as Sourced; Day 2: mechanical
Gate 0/1 → Qualifying) → `/batch-audit` (one lead-processor agent per
lead, ~3 parallel, cap 15) → per lead: machine walk (Firecrawl-primary
fetch, Playwright fallback) → **mandatory vision pass** → UAE Gate 0
floors → opener-finder (lane + finding + innocent explanation; `Finding
Verified` checked only on a visually-confirmed Lane 1 finding) → CRM
write → email address → **held** (no Gmail draft yet) → Haytham runs
`haytham-hook-finder` (real public evidence: LinkedIn, podcasts, YouTube,
About page) → Haytham asks for the draft → Gmail DRAFT (SMYKM opening A
or B) → Haytham sends by hand → reply → turn-two artifact →
**price discovery question** (answer logged VERBATIM + anchor set) →
priced offer (735 AED Track A / 2,575 AED Track B, gated by
`crm-gate offer`) → close. `uae-tick` runs the daily loop.

Haytham's manual jobs: picking the sprint day, running
`haytham-hook-finder` per lead, reviewing and sending drafts from Gmail,
recording the turn-two artifact, and confirming sends for logging.

## Hard rules (non-negotiable)

- **Never automate anything against Instagram** — the rule outlives the
  banned account. And never log in to, act as, or automate anything
  through Haytham's own accounts on ANY platform (LinkedIn included).
  Read-only public fetching via Firecrawl is the ceiling.
- **Never send an email.** The system ends at Gmail drafts. Sending is
  human.
- **Never invent findings.** No verified finding → no opener. Lane 2/3
  exists. Machine check flags are candidates only — a flag that fails the
  vision pass is dead and stays dead. `Finding Verified` gets checked only
  on a visually-confirmed Lane 1 finding; it is the send gate, and
  checking it to make a lead sendable corrupts the track's data.
- **No send without `Finding Verified`, and never more than 15 cold sends
  a day** (target band 12-15; one inbox, one domain, no backup). Enforced:
  `python main.py crm-gate send <row.json> --sends-today N`. The
  bottleneck is findings, not sends — 12-15 sends/day means 12-15 funnel
  walks/day.
- **Price discovery before any priced offer, never after a stall.** A
  lead cannot reach Offer Sent without a VERBATIM `Price Discovery
  Answer` and a `Discovery Anchor`. Enforced: `python main.py crm-gate
  offer <row.json>`. No PASS, no money email.
- **The price never moves.** $200 = 735 AED (Track A), $700 = 2,575 AED
  (Track B). The AED figures are the same price quoted natively, not a
  discount. A low anchor from a lead is market data, not permission to
  discount — objections get bonuses or restructured terms (GSO v2).
- **Copy rules, every generated email:** no em-dashes, ever. No operator
  jargon ("funnel", "conversion", "audit", "sequence"). Proper
  capitalization. No sign-off or name at the end. No weak closers ("no
  pressure / no rush / whenever timing's right") anywhere, including
  silence-breakers.
- **Two CRMs, never crossed.** UAE leads live ONLY in the UAE Lead CRM;
  the parenting DB is live-threads-only. Never write a UAE lead into the
  parenting DB or vice versa.
- Notion is the source of truth for pipeline state, not chat memory.
- A Gmail draft is not a send. Status / Touch # / Last Contacted / Email
  Thread Log move only after Haytham confirms an email actually left.
- **No draft before a hook decision.** `haytham-email-draft` and
  `process-lead` hard-block on a `SMYKM hook:` line that still reads "not
  run yet" — no Gmail draft until `haytham-hook-finder` resolves the line
  (a real hook, or a confirmed "no hook found").
- **Before any Notion page update that uses search-and-replace
  (`update_content`), fetch the page first** to confirm the current
  literal content format — Notion's enhanced-markdown escaping (`\$`,
  auto-linked domains) breaks naive search-and-replace. Escaped or
  non-plain formatting → rewrite the full body (`replace_content`)
  instead.
- **A dispatched subagent gets one resume, not two.** A status-only reply
  with no new work product means take the task over directly — see
  `.claude/skills/batch-audit/SKILL.md` Step 2.

## Key pieces

- `main.py discover-links` / `discover-checkout` / `screenshot-name` /
  `ingest` — the Firecrawl-primary fetch path: Claude fetches via
  Firecrawl MCP tools, these commands classify links (scope/priority) and
  build the evidence packet. Python owns all scope/analysis logic
  regardless of which layer fetched the page.
- `main.py walk <url>` — the Playwright crawl fallback for leads Firecrawl
  can't handle (persistent bot walls, JS-button click-discovery).
- `main.py vision …` — the vision-pass completeness gate. "Read every
  screenshot" is a computed fact, not a claim.
- `main.py crm-gate offer|send` — the UAE transition gates (see
  `audit/crm_gate.py`): offer = verbatim discovery answer + anchor before
  any priced offer; send = Finding Verified + address + daily cap. Skills
  dump the fresh Notion row to JSON, run the gate, and quote its literal
  output line. Same trust model as the vision gate.
- `audit/` — checks, extraction, Gate 0 floors (`gates.py`, UAE:
  audience 1,500 / activity 30 days / funnel present / UAE-based), packet
  builder; all fetch-layer-agnostic. `crawler.py` still holds the
  Playwright fallback + the link/checkout classification logic both fetch
  paths share.
- `.claude/skills/source-leads` — the sourcing sprint: Day 1 volume
  sourcing over 5 web channels, Day 2 mechanical qualifying.
- `.claude/skills/process-lead` — the per-lead contract: walk → vision
  pass → floors → opener → **held** at the Gmail draft until
  `haytham-hook-finder` resolves the hook.
- `.claude/skills/batch-audit` + `.claude/agents/lead-processor.md` —
  batch orchestrator over the Walk Queue (~3 parallel, cap 15) and the
  per-lead subagent with its structured return block.
- `.claude/skills/haytham-opener-finder` — Gate 0/1, the 5-stop walk
  (widened for webinar funnels, call-booking flows, cohort launches),
  filters, lanes, CRM page body format. Stops at the finding + innocent
  explanation — does not find the SMYKM hook.
- `.claude/skills/haytham-hook-finder` — separate, manually-triggered:
  real public evidence (LinkedIn, podcasts, YouTube, About page) → the
  SMYKM hook line, cited, never fabricated. Gates the draft.
- `.claude/skills/haytham-email-draft` — voice, mechanics, gate, logging,
  both tracks. UAE layer (AED framing + the price discovery email type)
  in `references/uae-track.md`.
- `.claude/skills/uae-tick` — the UAE daily loop: replies, verbatim
  discovery-answer logging, due touches, gated send queue, weekly
  scoreboard.
- `.claude/skills/pipeline-tick` — the parenting track's daily loop, live
  threads only.
- `.claude/skills/haytham-funnel-auditor` — deep audit (Loom/call prep).
- `.claude/skills/firecrawl` — MCP tool reference for the fetch layer.

## The CRMs

- **UAE Lead CRM (active):** data source
  `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`, database ID (REST)
  `5a9fc583160046d1a64c4e65cc804229`. Views, schema, lifecycle, SQL:
  `docs/uae-track/01-crm-operating-spec.md`.
- **Parenting Lead Pipeline (live threads only, never new leads):** data
  source `collection://c6209e29-55ef-4781-b735-73b2a254e34f`, database ID
  (REST) `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`.

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
