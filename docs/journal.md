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

## 2026-07-18 — Instagram fetch split into two dedicated Apify actors
- Swapped the single `apify/instagram-scraper` for `apify/instagram-profile-scraper`
  (`--mode details`, `usernames` input) + `apify/instagram-post-scraper` (posts +
  `ig-post` single-post detail, `username` input which also takes profile/post URLs).
  Branch `claude/apify-instagram-scraper-migration-vdnypk`, pushed (no PR yet).
- Why it's a clean swap: both are Apify's own sibling actors — **identical output
  field names** (trim/`_lean` keys unchanged) and both PAY_PER_EVENT with a flagged
  `isPrimaryEvent`, so the existing cost-approval estimator works untouched. Slightly
  cheaper too: $0.0023/profile + $0.0015/post at BRONZE.
- New flags: `--skip-pinned` (post actor's native `skipPinnedPosts`, **default off**
  by Haytham's call — a pinned post is often the coach's signature/framework content,
  i.e. the SMYKM hook) and `--include-about` (profile actor's paid about-account
  add-on). Dropped the unused reels/comments/mentions/stories modes; `--mode` is now
  `posts`/`details` only.
- CLI command names (`apify ig` / `ig-post`) unchanged on purpose, so
  `haytham-hook-finder` and every other consumer needed zero change. Only
  `audit/apify.py` + `main.py` + docs/tests touched. Tests: 23/23 (added
  actor-routing + username-normalize).
- Gotcha: the profile scraper's `usernames` field wants a **bare handle**, not a URL
  (the post scraper's `username` accepts either) — added `_ig_username()` to strip a
  handle out of a profile URL on the details path only.

## 2026-07-18 — Hooks + Touch-1 drafts for the 3 Audit Ready leads (Noona, Marie, Michele)
- Ran `haytham-hook-finder` (batch) over the 3 Audit Ready rows whose `SMYKM Hook`
  was empty. Apify cap fine (2% used). All 3 hooks from fresh, cited public evidence:
  - **Noona Nafousi** (Inbox 1, Track B) — WORK: her LinkedIn "factory workers packing
    medicine / 43% from one sentence / feel as good inside as success looks outside"
    post (8 Jul). Skipped her "choosing me" grief post (too intimate) and the 8M-view
    lisp reel (numeric-contrast/sensitive).
  - **Marie Hondekyn** (Inbox 2, Track A) — WORK: her coined "Selection Method" —
    "I don't teach you how to get chosen, I teach you how to choose" (IG @datingbymarie,
    9 Jul). Her 29K IG is @datingbymarie, NOT @infinityrelations (~1.3K).
  - **Michele Barouki** (Inbox 2, Track A) — LIFE: her 1 Jul IG post about building her
    home studio by hand. About page was too thin (generic, "cat mom of 3") so went to IG.
- Drafted all 3 Touch-1 openers (SMYKM opening A), Haytham approved copy.
- **Inbox split (his call):** Noona → Inbox 1, Marie + Michele → Inbox 2. Reasoning:
  split the two WARN-email leads (Noona catch-all, Marie inconclusive) across domains
  so a bounce doesn't hit one twice; Michele is the only clean PASS.
- Past noon Dubai → all 3 gate as next-day openers (send-day 07-19). `crm-gate send`
  PASS on all 3: Inbox 1 had 12 already scheduled for 07-19 (+Noona=13<20), Inbox 2 had
  10 (+Marie/Michele=12<20). Gmail drafts created (Noona via Gmail MCP; Marie+Michele via
  `gmail-gethaytham draft`), all linted clean. Rows set `Inbox` + Status = **Draft Ready**.
- Gotcha: `crm-gate send` requires BOTH `--sends-today` AND `--sends-next-day` even for a
  next-day opener — it won't count Gmail itself. Inbox 1 = gmail-mcp = haytham@auto-mate.one
  (confirmed). Inbox 1 already at 17 sends today (cap 20) but that doesn't constrain a
  next-day opener.
### Open follow-ups
- [ ] Haytham to schedule the 3 drafts in Gmail for 07-19, then confirm sends so the tick
  flips each to Outreach Sent (Touch #1, Last Contacted, Findings Bank #1 → USED-T1).

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
