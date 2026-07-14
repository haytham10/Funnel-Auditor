# Targeting + Sourcing — UAE Track

Who counts as a lead, and where to find them. Gate 0 and Gate 1 rewritten for this market.

> Adopted into the repo 2026-07-13, unchanged in substance. The Gate 0 floors
> are enforced in code where machine-checkable (`audit/gates.py`: audience
> 1,500, activity 30 days, funnel present; UAE residency comes back as
> needs-review for the judgment layer).

---

## The ICP, one line

**A UAE-based solo coach or course creator with a real funnel or paid digital product, active in the last 30 days, operating in English.**

---

## GATE 0 — mechanical, no judgment needed

All four must be true. Any fail = Disqualified. Do not spend another minute.

| Check | Pass condition | Why |
| --- | --- | --- |
| **UAE-based** | Physically based in Dubai, Abu Dhabi, Sharjah, or elsewhere in the UAE | "Serves clients in the region" does not count. The cultural and trust advantage only exists if they are actually here. |
| **Has a funnel or paid product** | A live sales page, checkout, course, or paid digital offer exists | This is the entire scope of the niche. A coach who only sells 1:1 by DM has nothing to fix. |
| **Activity recency** | Posted, emailed, or launched something in the last 30 days | Dormant operators do not buy. |
| **Audience floor** | 1,500+ on their largest owned or social channel | Lowered from the US pool. UAE audiences are smaller. A 2K UAE-focused list is worth what 8K is in the US. |

---

## GATE 1 — the solo operator test

One question, two seconds: **is there a team or a gatekeeper between me and the owner?**

- **YES → SKIP.** Cannot reach the decision-maker cold. File as long-term inbound.
- **NO or can't tell → PROCEED.**

**Pass signals:** own face, own story, replies to their own comments, single-person About page, no "our team" language.

**Fail signals:** "we" / "our team", an agency visible in the footer, a support@ inbox with a ticketing system, a named marketing lead, a verified mega-account with someone triaging the inbox.

A Gate 1 fail is not a bad person. It is a bad fit for a solo operator selling a 48-hour fix. Skip.

The ONLY thing this gate filters is a human wall. A real funnel, a custom site, a Kajabi build, a verified badge — none of these are skip reasons. If a funnel is genuinely optimized with no leaks, the funnel walk finds that in 90 seconds and routes to Lane 2.

---

## In scope

Business coaches, life coaches, executive and leadership coaches, career coaches, mindset coaches, fitness and health coaches, and course creators of any of the above.

The only thing that matters: **do they have a funnel with something in it that can leak.**

## Out of scope

- Call-only coaches with no digital product and no funnel. Nothing to fix, nothing to sell.
- Agencies, consultancies, anyone with a team. Gate 1 fail.
- Anyone whose funnel is not in English. Standing decision for this track.
- Coaches outside the UAE, even if Arab or adjacent. The whole thesis is geographic concentration. Do not dilute it.

---

## The buyer profile (soft signal, do NOT over-prune)

The openable-AND-buyable lead sits in the middle:

- **Ceiling:** polished, established, gatekept. Funnel works, no openable leak. Warm/inbound only.
- **Floor:** hobbyists. A leak may exist but they are not monetizing seriously and cannot or will not buy.
- **The buyers are in the middle:** committed to income AND messy enough to leak.

Polish correlates with no openable leak. This is a pattern, not a law. Messy-funnel is the real test, not audience size. Do not auto-reject the edges.

---

# SOURCING

## The IG problem, and the fix

The parenting pipeline sourced through personal IG browsing — logging in and browsing as Haytham. That is gone (his account was permanently banned Jun 22, 2026), so **Instagram is not a cold-sourcing channel for this track. Sourcing is web-native, full stop** — everything below is the web-native channel set.

That is a *sourcing* exclusion, and it is separate from enrichment. Once a lead is sourced and being worked, **SMYKM hook evidence for UAE leads comes primarily from LinkedIn posts, podcast appearances, YouTube, and their own site's About page** — and read-only public Instagram data pulled through a no-login third-party tool (an Apify-style actor, no account required) is a fair enrichment source too, the same as the others. The banned account was an identity/account-safety loss; it never made Instagram off-limits as public read-only data. What stays banned is logging in or acting as Haytham on any platform. See `CLAUDE.md` hard rules and `haytham-hook-finder`.

## Channel 1 — Coach directories (highest density, start here)

Directory listings are pre-filtered for "actively marketing themselves" and almost always link straight to a site, which is the funnel entry point.

- ICF (International Coaching Federation) UAE chapter directory. Certified coaches, UAE-based by definition.
- Regional coach directories and marketplace listings.

Pull name, site, city, specialty. Log as `Sourced`. Do not qualify yet.

## Channel 2 — Google footprint searches (finds the funnel directly)

Search for the **platform**, not the person. Platform domain footprint + UAE geographic marker. Kajabi, Teachable, Thinkific, Podia, Systeme, Skool.

This is the single best channel for Gate 0, because a platform footprint IS proof of a paid product.

## Channel 3 — LinkedIn (the UAE-specific unlock)

UAE professionals live on LinkedIn far more than US coaches do. This is both a sourcing channel AND the primary SMYKM hook-evidence source now that browsing IG as Haytham is gone (read-only, no-login IG data is still a valid enrichment source — see the note above).

Look for: coaches posting regularly, coaches announcing programs or cohorts, coaches with a profile link pointing to a real funnel.

## Channel 4 — Podcasts and events (pre-qualified for ambition)

Dubai has a dense business-event and podcast scene. Anyone who shows up as a guest or a speaker is by definition actively marketing themselves.

Guest lists, speaker pages, and the "where to find me" links that follow.

## Channel 5 — Lateral discovery

Once a good lead is found, the people they collaborate with, get interviewed by, or are recommended alongside are usually the same profile. Follow the thread. Each good lead becomes the next anchor.

---

## The two-day sprint (50+ qualified leads)

**Status as of Jul 13, 2026: not started. The CRM has zero leads in it.** The Jul 15 target for 50+ sourced and qualified is missed and has moved to Jul 20. Everything below is the plan, not a description of work already done.

**Day 1 — sourcing ONLY.** No qualifying, no funnel walks, no judgment. Collect names, sites, cities into the CRM as `Sourced`. Volume mode. Target 60-70 raw names so 50+ survive Gate 0.

**Day 2 — qualifying ONLY.** Run Gate 0 on every raw name. Mechanical, fast, no funnel walk yet. Kill anything that fails. Then Gate 1 on the survivors. Target 50+ at `Qualifying` with both gates passed.

**Separating these two days is the point.** Mixing sourcing and qualifying is what makes both slow.

The `source-leads` skill runs both modes (`.claude/skills/source-leads`).

## After the bootstrap — top-up (keeping the tap on)

The two-day sprint is a one-time bootstrap for an empty CRM. It is not the
whole life of the feature. Once leads exist, sourcing continues as **top-up**:
a small, on-demand run ("source me 20," "find more coaches") that adds ~15-20
fresh `Sourced` rows any day, then gets qualified by the Day-2 mechanics like
any other batch. Same channels, same gates, just smaller and repeatable.

Two rules keep top-up from drying up in a small market:

- **Source the flow, not the stock.** The UAE / English / solo pool is finite.
  Do not re-mine the same back-catalog — bias to what is new since last time
  (recent directory additions, recent podcast episodes, current launches and
  cohort announcements). The sprint mines the stock once; top-up skims the flow.
- **Rotate to the stalest channel.** Which channel was worked least recently is
  derivable for free from the CRM — the most recent Created time per Source
  Channel. Top-up defaults to the channel that has gone longest without a fresh
  row. A rising dedup rate on a channel is the early warning it is drying up.

Top-up is Mode 3 in the `source-leads` skill.

---

## After the sprint — the funnel walk

Only leads that pass both gates get a walk. The walk assigns the Lane, produces the verified Finding, and sets `Finding Verified`. Only then does a lead become `Audit Ready` and eligible to send.

**This is the bottleneck and it is supposed to be.**

Every new opener needs a verified finding, so the day's opener headroom (the send ceiling minus follow-ups due — 20/day ramping to 30, see `send-cap status`) is the real daily walk workload. Plan the day around the walks, not the sends.

## The hard gate

**No send without `Finding Verified` checked.**

A send with a thin or generic finding is worse than no send. It burns the lead, burns the domain, and produces a data point that means nothing.
