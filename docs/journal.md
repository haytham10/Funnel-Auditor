# Project Journal — cross-session memory

The narrative git history and Notion don't capture: **what happened each
session** (pipeline ops AND dev), the decisions behind it, gotchas learned, and
open follow-ups. Notion holds live *state* (where each lead is); git holds *code
changes*; this file is the thread that ties sessions together so a fresh session
isn't starting cold.

**How it's used:** the `SessionStart` hook (`.claude/hooks/session_memory.py`)
injects the most recent entries here + the last few commits at the top of every
session, so context loads automatically — no fetch, no prompting.

**How to write it:** at the end of a session with anything worth remembering,
add a new `## ` block at the TOP (newest first), then commit + push. A
journal-only commit is fine on an ops-only session — the point is that it
survives the ephemeral container. Keep entries short and scannable: a few
bullets, then an `### Open follow-ups` list if any are outstanding.

Entry template:

```
## YYYY-MM-DD — <one-line title>
- what happened (ops events, sends, sourcing, ticks, or code)
- decisions made and why
- gotchas / things that surprised us
### Open follow-ups
- [ ] the next thing someone should pick up
```

---

## 2026-07-18 — Luca & Larry "findings invalid" — over-retirement corrected
- Haytham flagged, while prepping tomorrow's follow-ups, that Luca Allam and Dr
  Larry Davies findings "don't hold anymore." Re-walked both funnels live.
- Reality: the earlier same-day session **over-retired**. The primary Touch-1
  findings (the ones gating `Finding Verified`) still HOLD; only the *secondary*
  banked findings died.
  - **Larry:** the note claiming `elmwoodevents.com/leadership-and-innovation`
    "now 404s" was WRONG — page is live (200), still dated 13 May 2026, $15/$25
    checkout live. Bank #1 holds. Bank #2 (no email capture) correctly retired:
    `elmwoodfields.com/contact-us` now has a newsletter opt-in.
  - **Luca:** "finding #1 likely stale" was WRONG — a paid checkout doesn't add a
    free opt-in. Homepage CTAs still dead-end at `#contact-us`, no freebie. Bank
    #1 (No opt-in capture) holds. Banks #2/#3 correctly retired: `/masterpitch/`
    is now a real 7-module course -> `/pricing` ($299/$399/$999).
- Corrected both Findings Banks + Notes in the UAE CRM. `Finding Verified` stays
  checked on both (send gate intact).
- Gotcha: a same-day "REFUTED/stale" aside is still a claim — verify the actual
  page before acting on it. A refuted *secondary* finding does not make the
  *primary* felt leak stale.
- Touch 2 carrier decided (Haytham): **Loom offer** for both (no banked 2nd
  finding left to carry). Drafted both Touch 2 replies (same thread/subject,
  Loom offer as the single payload, no link/price), created the Gmail drafts in
  Inbox 1, and left each row at Outreach Sent with a "Touch 2 held for 07-19
  send" marker in Notes. Status stays Outreach Sent (a follow-up draft on an
  already-sent lead does NOT flip back to Draft Ready — that status is the
  first-send pre-state only).
- Both Touch 2 drafts SCHEDULED in Gmail (Haytham) for 07-19 send, Inbox 1.
  Notes markers updated to "SCHEDULED". Status stays Outreach Sent (follow-up on
  an already-sent lead never flips to Scheduled/Draft Ready — those are
  first-send pre-states). The 2 scheduled sends count against Inbox 1's 07-19
  ceiling.
### Open follow-ups
- [ ] 07-19: on confirmed departure of each scheduled send, advance the rows
  (Touch #->2, Last Contacted->07-19, Next Action->07-25, append thread log).
  uae-tick reconciles Gmail reality; the crm-gate send carrier is loom-offer,
  Inbox 1 (its 07-19 budget must have room for these 2 plus anything else due).

## 2026-07-18 — Four bug fixes + cross-session memory setup
- Fixed and merged 4 bugs to `uae-track` (PR #48, squash `9cdc428`):
  mobile-screenshot re-settle, calendar events surviving Gmail/Notion date
  shapes, the noon-Dubai send-day cutoff for openers, and the
  authoritative-skills `SessionStart` hook.
- Added THIS journal + a second `SessionStart` hook that auto-loads recent
  memory (this file's latest entries + `git log`) so new sessions boot with
  context. Decision: keep session memory in git (auto-loads at start, diffable,
  lives with CLAUDE.md) rather than Notion, which stays the source of truth for
  live pipeline *state*, not narrative.
- Gotcha: past noon Dubai, a fresh touch-1 opener now needs
  `--sends-next-day <inbox's scheduled count>` on `crm-gate send`, or it fails
  closed asking for it. `inbox counts` prints `send_day` + an `opener_note`
  when this applies.
### Open follow-ups
- [ ] If phone-readable ops notes become useful, mirror journal entries to a
  Notion page (not needed yet).
