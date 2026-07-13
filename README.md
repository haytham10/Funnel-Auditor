# Funnel Auditor

The outreach machine. Turns a manually-sourced Instagram lead into a walked
funnel, a logged Notion row, and an approved cold-email draft — with the two
things that must stay human (IG sourcing, hitting send) left exactly where
they are.

## Why the split is what it is

| Stage | Who does it | Why |
|---|---|---|
| Sourcing (IG browsing, eyeballing candidates) | **Human** | IG automation = banned account. Already proven the hard way. |
| Funnel walk: crawl, screenshots, page text, link checks, stale dates, email harvest | **Machine** (`main.py walk`) | This was the hour of manual screenshotting and clicking per lead. |
| Floors (audience/activity/niche), lane call, sting test, opening angle | **Claude** (`/process-lead`) | Judgment work, but fed by the evidence packet instead of manual paste. |
| Notion logging | **Claude** | Deterministic once the walk is done. |
| Email drafting | **Claude** (email-draft skill) | The voice rules are already encoded; the silent gate loop runs before you see anything. |
| Approving + sending | **Human** | Deliverability, ethics, and the fact that it's your name on it. System stops at Gmail drafts. |
| Replies, follow-up cadence, send queue | **Claude** (`/pipeline-tick`) | Reading Gmail + Notion state and drafting due touches is mechanical. |

## Daily flow

1. **You**: browse IG like a human, spot candidate coaches, grab name +
   link-in-bio + follower count (the 20 seconds you already spend).
2. **Hand the leads over**, either way:
   - one at a time in chat — "process this lead: Jane Doe, @janedoecoach,
     linktr.ee/janedoe, 4.2K followers" (`/process-lead`), or
   - log them straight into Notion while sourcing (Contact Name + Site URL
     minimum), then say "batch audit" — `/batch-audit` pulls the fresh
     Researching rows and works them all, ending in one batch brief with
     draft variants per lead.
3. **You**: approve variants → Gmail drafts appear; send from Gmail; say
   "log this" → Notion updated per the Email OS rules.
4. **Each morning**: `/pipeline-tick` (or let the scheduled Routine run it)
   gives you replies, due follow-ups with drafts, and today's send queue.

All of this runs in Claude Code on the web — sessions of this repo carry the
skills and connectors; no API key involved.

## The machine walk

```bash
pip install -r requirements.txt
playwright install chromium        # local only; managed sessions have it

python main.py walk linktr.ee/janedoe --name "Jane Doe" --handle @janedoecoach --followers 4200
```

Produces `evidence/jane-doe/`:

- `packet.md` — the paste-ready walk packet: Gate 0 floor signals, harvested
  contact emails, machine-flagged leak candidates (mapped to the 5-stop
  walk's tiers), page-by-page checks, and an explicit list of what a crawl
  cannot see.
- `evidence.json` — everything, structured.
- `pages/*.txt` — full visible text per page (where the copy leaks hide).
- `screenshots/` — desktop + mobile, full page, every page.

What it detects per page: email-capture forms (+ ESP), tracking pixels,
dead internal links (with bot-wall false-positive handling), checkout
platform + order bump/upsell presence, load speed, prices with context,
contact emails (mailto + text), and stale/past dates sitting next to
launch-implying copy — the Pam pattern, the finding type behind most warm
replies to date.

It also handles Stan-store-style JS storefronts by clicking product cards to
discover the product pages a static crawl can't see, and follows buy/enroll
links one hop into checkouts.

Every flag is labeled a **candidate**: the sting test and vitamin filter stay
with the judgment layer. The packet's "not visible from this crawl" section
lists exactly what still needs the human click-through (DM flows, logins,
comment-gated freebies, ghost test).

## The skills

- `process-lead` — orchestrator: intake → walk → floors → Notion →
  opener-finder → email draft → Gmail draft on approval.
- `batch-audit` — batch front-end: fetches fresh Researching rows from
  Notion after a sourcing session and runs the process-lead flow on each
  (≤15 per run), delivering one batch brief + all drafts for approval.
- `pipeline-tick` — daily ops: reply detection (Gmail → Notion sync), due
  follow-ups drafted, dormant revivals, send queue sorted sub-12K first,
  hygiene flags.
- `haytham-opener-finder`, `haytham-email-draft`, `haytham-funnel-auditor` —
  the methodology skills (walk, voice, deep audit), vendored so every session
  in this repo carries them.

## Guardrails

- No Instagram automation of any kind, ever.
- No email is ever sent by the system — Gmail drafts only.
- No invented findings — a clean funnel is Lane 2, not an opener.
- Notion is the single source of truth; the Bible/Email OS rules for status
  transitions (incl. Touch 4 → Dormant, never Lost) are encoded in the skills.
