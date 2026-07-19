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

## 2026-07-19 — CRM hygiene sweep (clean) + Christina Steinhoff reclassified; WhatsApp cold-texting is an account-safety risk
- **Hygiene sweep** (the one the 07-19 tick couldn't finish on quota) re-run clean:
  ALL mechanical checks passed — 0 future-dated Last Contacted, 0 Touch#=0 on
  Outreach Sent, 0 missed Findings Bank UNUSED->USED flips (Shankar 1&2 USED,
  Marie 1 USED both verified correct), 0 stale pre-send markers (the two rows
  that matched carried the historical phrase "hook found VIA haytham-hook-finder",
  not a pending marker), 0 stale warm threads, 0 over-a-week un-walked Qualifying.
  Nothing auto-fixed because nothing needed it.
- **Attribution splits (Step 6, also skipped last tick):** over 67 cold-touched
  leads, all 5 warm replies (Ben, Donna, Christina, William, Lisa) came from
  **Google Footprint** sourcing (~13%, 5/39). Every other channel is 0 replies
  across 28 sends (LinkedIn 0/14, Coach Directory 0/6, Event Speaker 0/3,
  Podcast 0/2, IG 0/2, Lateral 0/1). Small n, but a clean directional case to
  concentrate sourcing on Google Footprint. Finding Type of repliers: Dead/stale
  x2, Other x3. Lane: every sent lead + every reply is Lane 1 (Lane 2/3 never
  sent), so no Lane comparison possible this round.
- **Judgment flags surfaced (not auto-fixed):** 4 Lane-2 "no leak" leads
  (Yasmina Nagnoug, Nicolas Provencal, Alex Makarovski, Coach Islam) sit at
  Dormant while their own notes say "holds at Qualifying" — status/note
  disagree, confirm intended parking status. Murielle Larriere went Dormant
  after only Touch 1 (cold seq is 3) — confirm early drop vs premature Dormant.
- **Christina Steinhoff reclassified Warm->Cold.** Her 07-19 "reply" was a
  CONFIRMED autoresponder (word-for-word the 07-16 auto-reply, same 1-min
  latency). Per its instruction, Haytham texted the +971562737368 number on
  WhatsApp — **his number got spam-flagged and feature-blocked for 6h after the
  first message.** The line is an automated WhatsApp Business gate; both her
  published channels (email + phone) are automated walls, no human reachable.
  Row set back to Status Outreach Sent / Sequence Cold / Touch 3 due 2026-07-25;
  if no human reply, Dormant. Email Thread Log + Notes updated to record all of it.
- **LESSON (account-safety, treat as a rule):** do NOT cold-text leads on
  WhatsApp from Haytham's personal number. One unsolicited message to a
  non-contact got reported/blocked within 6h. Same family of mistake as the IG
  ban — different platform, same "don't put Haytham's own account at risk" rule.
  A lead that only exposes an autoresponder email + a phone number is likely a
  bot moat, not a reachable person; don't chase it through personal channels.
### Open follow-ups
- [ ] Confirm the 4 Lane-2 Dormant rows' intended status (Dormant vs Qualifying-hold).
- [ ] Confirm Murielle Larriere's early Dormant (bounce/unreachable vs premature).
- [ ] Christina Touch 3 due 2026-07-25 (Inbox 1); park Dormant if no human reply.

## 2026-07-19 — uae-tick: reconciled 25 already-departed sends, 2 bounces, 1 probable autoresponder
- Ran the daily uae-tick. Unusual shape this run: 25 emails had already left both
  inboxes before the tick started (12 Inbox 1 Touch-2 follow-ups + Noona's
  scheduled Touch 1 + Christina's Touch 2, all auto-mate.one; 10 Inbox 2
  scheduled Touch-1 openers + 2 bounces, all gethaytham.com) — none logged to
  Notion yet. Fanned out ~25 parallel subagents (one per lead, worktree-isolated)
  to do full confirmed-send reconciliation against fetched Gmail thread content:
  Touch #, Sequence, Status, Last Contacted/Next Action, Findings Bank
  UNUSED->USED-TN flip, Notes, and the Email Thread Log entry — verified each
  against the actual Gmail message before writing, not just asserted.
- **2 new bounces**, both Inbox 2, both "Address not found": Samira Alexander
  (samira@samiraalexander.com, an Apify-enrich guess that had verified PASS
  the day before) and Kalyani Seth Soni (info@sheinvests.me, already flagged
  WARN/catch-all at verify time — the risk materialized). Both reverted to
  Qualifying, no touch counted, logged to docs/deliverability-log.md.
- **Christina Steinhoff's reply is very likely an autoresponder, not a person**
  — it landed 1 minute after Touch 2 sent and is near word-for-word identical
  to her Touch 1 auto-reply from 07-16 (same 1-minute latency, merge-tag
  artifacts on the first one). Logged as Reply Received/Warm per protocol
  since the rule is to record what came in, but flagged loudly in the brief —
  needs a human check (text the phone number in her signature) before treating
  it as a live warm thread.
- Ceilings held clean: Inbox 1 13/20, Inbox 2 13/20 (13 includes the 2
  bounces — a bounce still counts against ceiling, it departed the inbox).
  Neither inbox has held its ramp step 7 days yet, so no ramp reminder.
- Send queue was empty (no Audit Ready/Draft Ready rows) — bottleneck is walks,
  not sends, consistent with the standing note in CLAUDE.md.
- First scoreboard run (no prior one found in this journal) — ~66 unique leads
  cold-touched, 4 confirmed replies + 1 uncertain (Christina) ≈ 6-7.5% reply
  rate by lead, 0 discovery answers logged yet (Donna Brown's is pending), 0
  offers, 0 closes.
### Open follow-ups
- [ ] Donna Brown's price discovery answer — log VERBATIM the moment it lands,
      do not wait for the next tick.
- [ ] Confirm whether Christina Steinhoff's reply is a real person or fully
      automated before drafting anything further to her.
- [ ] Notion's SQL query quota (free plan) was exhausted mid-tick, so the
      hygiene sweep (future-dated Last Contacted, Touch#=0 on Outreach Sent)
      and the Finding Type/Source Channel/Lane attribution splits couldn't run
      this pass — re-run clean next tick.

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

## 2026-07-18 — Donna Brown replied yes to the walkthrough (Inbox 2)
- Donna Brown (Leadership/Life coach, Dubai, Inbox 2, Track A) replied a second
  time on her thread (subj "your core blueprint bundle"), at 22:05 Dubai:
  "Thank you for your message... Sure happy to know what I can do better.. By the
  way, how did you come across my page?" — a **warm yes to the Loom walkthrough**
  plus a trust-check question.
- Thread state: Touch 1 = finding #1 (Core Blueprint checkout double-charge) →
  her reply #1 slightly **misread** it (thinks the worry is that the bundle
  duplicates the course; the real flag is the checkout add-on bump stacking the
  AED 1,997 bundle on top of the AED 597 course). Touch 2 = finding #2 (Save 35%
  badge is really ~29%) + loom-offer → her reply #2 above.
- Logged her reply verbatim to the Email Thread Log; Notes refreshed; Next Action
  pulled to today. Status stays `Reply Received`, Sequence `Warm`, Touch # 2 (no
  send yet). Findings Bank #3 (course-name mismatch) + #4 (Stripe branded
  "Coaching Business") still UNUSED — Loom material.
- **Drafted the turn-two Loom-delivery reply** and created the Gmail draft in
  Inbox 2 (threaded, subject unchanged), held on a `[Loom link]` placeholder.
  Answers her question honestly (Google-footprint sourcing), re-shows the
  double-charge she misread, carries the two remaining findings, closes steering
  her toward handing it over (she said "I'll revisit it myself" — gratitude-trap
  risk).
- **UPDATE (later 07-18/19):** Haytham recorded the Loom same night, rewrote the
  reply himself (better than mine), and folded the **price-discovery question**
  into the close: "if someone took the whole site top to bottom, everything
  sorted and off your plate, what would you expect that to run?" Scope widened
  from the fixes to the whole site on purpose (lifts her anchor; read it in that
  context). Loom link: loom.com/share/9333b35228e344c5b40900a5612b5ac4.
- **SENT** (accidental click, but a good email) 2026-07-19 ~04:18 Dubai, Inbox 2,
  Touch 3. Full confirmed-send logging done: Status `Reply Received` →
  `Price Discovery Sent`, Touch # → 3, Last Contacted 07-19, Next Action 07-22,
  Findings Bank #3 → USED-T3 (Loom spent it), #4 (Stripe branding) still UNUSED /
  held. Thread log + Price Discovery section updated. This is now a
  **Price Discovery Sent** lead — her next reply IS the study data.
- Loom itself covered findings #1 (double-charge, re-shown to fix her earlier
  misread), #2 (35% vs 29%), #3 (course-name mismatch). #4 held back.
### Open follow-ups
- [ ] Watch Inbox 2 for Donna's reply. The MOMENT a number (or refusal) lands:
      log it VERBATIM into `Price Discovery Answer`, set `Discovery Anchor` per
      the uae-track mapping. Do NOT wait for a tick — this is the track's whole
      point. Then `crm-gate offer` gates any priced email.
- [ ] If quiet by ~07-22: warm bump. #4 (Stripe 'Coaching Business' branding) is
      the unused held finding for it.

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
