# Funnel Auditor — outreach automation system

This repo is the machine layer of Haytham's cold-outreach system for
parenting/faith-based coach leads, plus the Claude skills that orchestrate it.

## The pipeline in one line

Manual IG sourcing → `/process-lead` (machine walk → floors → Notion →
opener-finder → email draft → Gmail DRAFT) → Haytham sends by hand →
`/pipeline-tick` (replies, due follow-ups, send queue) daily.

## Hard rules (non-negotiable)

- **Never automate anything against Instagram.** No fetching instagram.com,
  no scraping, no DMs. Haytham lost an account to IG automation; sourcing is
  manual by design.
- **Never send an email.** The system ends at Gmail drafts. Sending is human.
- **Never invent findings.** No verified finding → no opener. Lane 2/3 exists.
- Notion is the source of truth for pipeline state, not chat memory.

## Key pieces

- `main.py walk <url> --name --handle --followers` — crawl + evidence packet
  under `evidence/<slug>/` (packet.md, evidence.json, page text, screenshots).
- `audit/` — crawler (Playwright), checks, extraction, Gate 0 floors, packet
  builder.
- `.claude/skills/process-lead` — one-command lead intake orchestrator.
- `.claude/skills/pipeline-tick` — daily ops loop (replies/follow-ups/queue).
- `.claude/skills/haytham-opener-finder` — the walk: Gate 1, 5 stops, filters,
  lanes, Notion page body format.
- `.claude/skills/haytham-email-draft` — voice, mechanics, gate, logging rules.
- `.claude/skills/haytham-funnel-auditor` — deep audit (Loom/call prep).

Notion Lead Pipeline data source: `collection://c6209e29-55ef-4781-b735-73b2a254e34f`.

## Environment notes

- Managed cloud sessions: Chromium lives at `/opt/pw-browsers/chromium` (the
  crawler auto-detects it; override with `FUNNEL_AUDITOR_CHROMIUM`). The MITM
  egress proxy resets Chromium's post-quantum TLS handshake — the crawler
  writes a Chromium enterprise policy to disable PQ/ECH automatically.
- Local (WSL): `pip install -r requirements.txt && playwright install chromium`.
