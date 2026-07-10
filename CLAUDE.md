# Funnel Auditor — outreach automation system

This repo is the machine layer of Haytham's cold-outreach system for
parenting/faith-based coach leads, plus the Claude skills that orchestrate it.

## The pipeline in one line

Manual IG sourcing (Haytham logs the row in Notion + attaches his IG
screenshots to the page body) → `/batch-audit` (scheduled Routine or "work
the queue"; one lead-processor agent per lead, ~3 in parallel, cap 15) →
per lead: machine walk → **mandatory vision pass over the screenshots** →
floors → opener-finder → Notion write → email address → automatic Gmail
DRAFT → Haytham reviews in Gmail and sends by hand → `/pipeline-tick`
(replies, due follow-ups auto-drafted, send queue) daily.

Haytham's only manual jobs: sourcing (with IG screenshots attached),
reviewing and sending drafts from Gmail, and confirming sends for logging.
Single pasted leads still go through `/process-lead` directly.

## Hard rules (non-negotiable)

- **Never automate anything against Instagram.** No fetching instagram.com,
  no scraping, no DMs. Haytham lost an account to IG automation; sourcing is
  manual by design.
- **Never send an email.** The system ends at Gmail drafts. Sending is human.
- **Never invent findings.** No verified finding → no opener. Lane 2/3 exists.
  Machine check flags are candidates only — a flag that fails the vision
  pass (visual confirmation on the screenshot) is dead and stays dead.
- Notion is the source of truth for pipeline state, not chat memory.
- A Gmail draft is not a send. Drafts are created automatically; Status /
  Touch # / Last Contacted / Email Thread Log move only after Haytham
  confirms an email actually left.

## Key pieces

- `main.py walk <url> --name --handle --followers` — crawl + evidence packet
  under `evidence/<slug>/` (packet.md, evidence.json, page text, screenshots).
- `audit/` — crawler (Playwright), checks, extraction, Gate 0 floors, packet
  builder.
- `.claude/skills/process-lead` — the per-lead contract everything else
  runs: walk → vision pass → floors → opener → automatic Gmail draft.
- `.claude/skills/batch-audit` — batch orchestrator: pulls Researching rows
  from Notion, spawns one `lead-processor` agent per lead (~3 parallel,
  cap 15), verifies the writes landed, delivers one batch brief. Fired by
  the lead-queue Routine or on demand.
- `.claude/agents/lead-processor.md` — the per-lead subagent and its
  structured return block.
- `.claude/skills/pipeline-tick` — daily ops loop (replies/follow-ups/queue);
  due follow-ups auto-draft to Gmail, never stacking on an unsent draft to
  the same address.
- `.claude/skills/haytham-opener-finder` — the walk: Gate 1, 5 stops, filters,
  lanes, Notion page body format.
- `.claude/skills/haytham-email-draft` — voice, mechanics, gate, logging rules.
- `.claude/skills/haytham-funnel-auditor` — deep audit (Loom/call prep).

Notion Lead Pipeline:
- Data source ID (MCP): `collection://c6209e29-55ef-4781-b735-73b2a254e34f`
- Database ID (REST API): `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`

## Environment notes

- Managed cloud sessions: Chromium lives at `/opt/pw-browsers/chromium` (the
  crawler auto-detects it; override with `FUNNEL_AUDITOR_CHROMIUM`). The MITM
  egress proxy resets Chromium's post-quantum TLS handshake — the crawler
  writes a Chromium enterprise policy to disable PQ/ECH automatically.
- Local (WSL): `pip install -r requirements.txt && playwright install chromium`.
