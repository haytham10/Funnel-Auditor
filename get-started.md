# Funnel Auditor — Get Started (portable overview)

This file is a self-contained brief for bootstrapping **any** AI
model/harness on this project — paste it directly into a new chat/session
with another tool (Cursor, Windsurf, Goose, Aider, a plain API call, etc.)
to get it oriented without reading the rest of the repo. It translates the
Claude Code–specific mechanics (skills, subagents, hooks) into
harness-agnostic instructions.

If you're running this in Claude Code itself, don't use this file as your
instructions — read `CLAUDE.md` and the skills in `.claude/skills/`
instead; those are the authoritative, fully detailed versions. This file
is a compressed export for elsewhere.

## What this is

A cold-outreach automation system for a solo operator (Haytham) selling
funnel audits to coaches/course creators. Active track:

- **UAE track.** UAE-based solo coaches with real funnels, priced in AED.
  A deliberate step vs. earlier iterations of the pipeline: price
  discovery happens BEFORE any priced offer is sent.

The UAE Lead CRM (a Notion database) is the source of truth for live
pipeline STATE (who's at what stage). Git/code is the source of truth for
the automation logic. A running text journal (`docs/journal.md`) is the
source of truth for narrative history (decisions, gotchas) across
sessions.

## The pipeline (UAE track, one line)

source-leads → qualify-leads → batch-audit (funnel walk + vision pass +
finding) → finding-verifier (independent check) → CRM write → email
address resolved + verified → HELD at "Audit Ready" (no draft yet) →
haytham-hook-finder (finds a real, cited personal hook; independent
hook-verifier confirms it) → drafts a Gmail draft (held, not sent) →
human reviews and sends by hand → reply → turn-two = the paid 48-Hour Leak
call ask with two specific times → Call Booked → priced offer (The First
Five: 1,500 AED setup credited against the first three calls, then 600 AED
per call that happens) → close.

## The core architectural pattern: worker → independent verifier

Every stage that "certifies" something (a funnel finding, a sourced
candidate, a qualification verdict, a personal hook) is split into two
roles:

1. A **worker** that proposes the claim and cites its evidence.
2. An **independent verifier**, run in a FRESH context that never saw the
   worker's reasoning, which re-derives the claim from the raw evidence
   (screenshots, the actual page, the actual quoted source) and only THEN
   marks the claim "verified." Only the verifier is allowed to flip the
   gate that unlocks the next stage.

This is deliberate and load-bearing: a single agent "checking its own
work" is not real verification — it just re-reads its own conclusion and
agrees with itself. If you're implementing this on a harness without
native sub-agent isolation, you must simulate it — e.g. two separate API
calls with genuinely disjoint context, not a single continued
conversation.

## Hard rules (non-negotiable — enforce as code/gates, not just prompts)

- Never log in to or act as Haytham on ANY platform (Instagram, LinkedIn,
  etc.). Read-only, no-login, public scraping/search tools only.
- Never send an email. The system's terminal state is a held Gmail draft;
  sending is always a human action.
- Never invent a "finding." No independently-verified finding → no
  outreach opener.
- No send without BOTH an independently verified funnel finding AND a
  verified email address — AND never past a per-inbox daily send ceiling
  (ceilings are per sending domain/inbox, not pooled across inboxes).
- Cold sequence is exactly 3 touches (day 0, 3, 9) then stop. Touches 2
  and 3 must each add something genuinely new (a new finding, an offer, a
  disambiguating question) — never a bare "just bumping this."
- A lead must have EARNED a number before any priced offer is sent: an
  earned Status (Call Booked, Offer Sent, Won, or the legacy Leak Fix
  statuses) or the `Asked For Price` checkbox. The turn-two call ask is exempt — it
  is the rung that earns the right. (This replaced the price-discovery
  gate on 2026-07-24, after asking 100 leads' worth of coaches what they'd
  pay produced 3 answers, all refusals, and 0 numbers.)
- Price is fixed: 1,500 AED setup + 600 AED per booked call. Never discounted;
  objections get bonuses or restructured terms, not a lower number.
- Copy rules for every generated email: no em-dashes, no jargon words
  ("funnel," "conversion," "audit," "sequence"), sign off with the
  sender's real name (no auto-signature), no weak/hedging closers.

## Key building blocks (language/tool-agnostic)

- A fetch/crawl layer: primary fetch via a web-scraping API (this repo
  uses Firecrawl), with a browser-automation fallback (Playwright) for
  sites that block simple fetches or need JS-driven interaction.
- A **mandatory vision pass**: every funnel walk's screenshots must
  actually be read by a vision-capable model before a finding is trusted
  — a completeness gate, not optional.
- A local Python CLI (`main.py` + the `audit/` package) that owns all
  deterministic logic: floor/gate checks, email shape + deliverability
  verification, cost-approval gating on paid API calls, send-cap ramp
  logic, CRM-row JSON dumps. The model calls this CLI and quotes its
  literal output rather than re-deriving gate logic itself — keeps
  pass/fail decisions deterministic and auditable.
- CRM integration (this repo uses Notion via MCP) for lead state.
- Email integration (this repo uses Gmail, both via an MCP server and a
  direct API for a second inbox) for creating (never sending) drafts.
- A no-login social/profile data source (this repo uses Apify actors) for
  LinkedIn/Instagram/YouTube data a plain web fetch can't reach.
- Every paid third-party API call should be cost-estimated and gated
  behind an approval threshold before running, to avoid runaway spend.

## What another harness needs to replicate this

1. Equivalent tool access: a web-scrape/search tool, a browser-automation
   fallback, a CRM/database integration, an email-draft integration
   (never auto-send), and a social-profile lookup tool.
2. A way to run genuinely isolated sub-calls for the verifier pattern
   above (separate context, not a continued chat).
3. A router step (manual or automated) that maps a user request ("source
   leads," "walk this lead," "find the hook") to the right stage
   instructions, since there's no automatic skill-triggering outside
   Claude Code.
4. The gate CLI (or an equivalent deterministic check) kept as the
   authority on pass/fail — don't let the model free-hand the gate logic
   in natural language.

## Daily operational loop

A "tick" step each day: check for replies, sync CRM state, log any price
discovery answers verbatim, run the send gates on anything about to move,
draft due follow-ups, and hand over a capped send queue for the day.

## Source of truth hierarchy

- Live pipeline state → the CRM (Notion), not chat memory.
- Automation logic/behavior → the versioned code + instruction files.
- Cross-session narrative (why decisions were made, open follow-ups) → a
  running dated journal file, newest entry at the top.

## What's NOT in this file

This brief deliberately omits the exact gate implementations
(`audit/gates.py`, `audit/crm_gate.py`), the full copywriting
voice/framework, CRM schema/field names, and API credential setup — those
are implementation detail, not orientation. Pull them from the source repo
(`docs/uae-track/`, `.claude/skills/haytham-email-draft/`, `audit/`) once
you're actually wiring a specific harness up, rather than duplicating them
here where they'd drift out of sync.
