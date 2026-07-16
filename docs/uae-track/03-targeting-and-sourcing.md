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

The parenting pipeline sourced through personal IG browsing — logging in and browsing as Haytham. That is gone (his account was permanently banned Jun 22, 2026). The lesson was an **account-safety** one, not a platform ban: what killed the account was *acting as Haytham through his own login*, not touching Instagram at all.

So the fix is not "web-native, full stop" — it is **no-login, full stop.** Sourcing is dynamic and channel-agnostic: work whatever vein produces UAE solo coaches with an audience and a way to get paid, Instagram and link-in-bio stores included, **through read-only no-login tools only** (Firecrawl, or an Apify actor that takes a username/URL and needs no account). The channels below are a menu of veins to work adaptively, not a fixed set or a rotation. What stays permanently banned is logging in or acting as Haytham on any platform. See `CLAUDE.md` hard rules, the `source-leads` skill, and `haytham-hook-finder`.

The same no-login IG/LinkedIn data also feeds enrichment: once a lead is being worked, **SMYKM hook evidence comes primarily from LinkedIn posts, podcast appearances, YouTube, and their own About page.**

## Channel 1 — Coach directories (highest density, start here)

Directory listings are pre-filtered for "actively marketing themselves" and almost always link straight to a site, which is the funnel entry point.

- ICF (International Coaching Federation) UAE chapter directory. Certified coaches, UAE-based by definition.
- Regional coach directories and marketplace listings.

Pull name, site, city, specialty. Log as `Sourced`. Do not qualify yet.

## Channel 2 — Google footprint searches (finds the funnel directly)

Search for the **platform**, not the person. Platform footprint + UAE geographic marker. Kajabi, Teachable, Thinkific, Podia, Systeme, Kartra, Skool.

This is the single best channel for Gate 0, because a platform footprint IS proof of a paid product. Work it two ways, because they catch different, barely-overlapping segments (confirmed 2026-07-16):
- **Subdomain** (`site:mykajabi.com coach Dubai`) — coaches on the free default platform subdomain.
- **Footer signature** (`"powered by kajabi" coach Dubai`, not site-scoped) — coaches on a **custom domain** still running the platform underneath, which the subdomain query never sees and which skew more established.

The mechanics (both shapes, both engines, merge/dedupe, geo rotation across the emirates, and the confirmation the wider footer-signature net needs) live in the `source-leads` skill and `apify-actors.md`. `python main.py apify footprint <platform> --geo <emirate>` is the wrapper that runs it.

## Channel 3 — LinkedIn (the UAE-specific unlock)

UAE professionals live on LinkedIn far more than US coaches do. This is both a sourcing channel AND the primary SMYKM hook-evidence source now that browsing IG as Haytham is gone (read-only, no-login IG data is still a valid enrichment source — see the note above).

Look for: coaches posting regularly, coaches announcing programs or cohorts, coaches with a profile link pointing to a real funnel.

## Channel 4 — Podcasts and events (pre-qualified for ambition)

Dubai has a dense business-event and podcast scene. Anyone who shows up as a guest or a speaker is by definition actively marketing themselves.

Guest lists, speaker pages, and the "where to find me" links that follow.

## Channel 5 — Link-in-bio footprint (the IG/DM-native coaches)

Where the Instagram- and DM-native coaches keep their money page: `site:stan.store`, `site:beacons.ai`, `site:linktr.ee` + coach + emirate/niche. The link-in-bio page **is** the funnel and is scrapable — confirm UAE + solo + a paid offer and grab the real name off it. This is the vein that catches exactly the coaches a domain-only search misses. Pair with the no-login IG actor (`apify ig <profile> --mode details`) when you have a handle but no store link: it returns followers (audience), bio (UAE + solo), and the external link (the funnel).

## Channel 6 — Lateral discovery

Once a good lead is found, the people they collaborate with, get interviewed by, or are recommended alongside are usually the same profile. Follow the thread. Each good lead becomes the next anchor.

---

## Two functions, two skills — sourcing and qualifying

Sourcing and qualifying are **separate operations, and separate skills.**
Keeping them apart is the point — mixing "collect names" and "gate names" is
what makes both slow, so the split is structural, not just advised:

- **`source-leads` collects ONLY.** No qualifying, no funnel walks, no
  judgment. Collect names, sites, cities into the CRM as `Sourced`. It runs
  at two volumes — a one-time **bootstrap** (60-70 raw names to fill an
  empty CRM) and everyday **top-up** (~15-20, repeatable) — but the job is
  the same either way: a logged `Sourced` row and nothing more.
- **`qualify-leads` gates ONLY.** Run Gate 0 on every `Sourced` row,
  mechanically, no funnel walk yet. Kill anything that fails to
  `Disqualified`. Then Gate 1 on the survivors, promoting passes to
  `Qualifying`. Triage speed — ~2 fetches per lead.

Historically this ran as a one-time **two-day bootstrap sprint** (Day 1
source, Day 2 qualify) to fill an empty CRM — targeted 50+ qualified by
mid-Jul 2026. That framing is retired: the calendar-day language described
a one-off event, but both functions run for the life of the track (every
top-up produces `Sourced` rows that then need qualifying). Name them by
function — source, then qualify — not by day.

### Keeping the tap on — top-up

Once the CRM has leads, sourcing continues as **top-up**: a small, on-demand
`source-leads` run ("source me 20," "find more coaches") that adds ~15-20
fresh `Sourced` rows any day, then gets gated by `qualify-leads` like any
other batch. Same channels, same gates, just smaller and repeatable.

Two rules keep top-up from drying up in a small market:

- **Source the flow, not the stock.** The UAE / English / solo pool is finite.
  Do not re-mine the same back-catalog — bias to what is new since last time
  (recent directory additions, recent podcast episodes, current launches and
  cohort announcements). A bootstrap run mines the stock once; top-up skims
  the flow.
- **Follow what's producing; abandon what's dry.** There is no fixed rotation
  and no channel you owe a turn to. Start wherever the ask points or where you
  last had signal, and let results steer: a vein returning fresh UAE coaches
  gets worked harder, a vein returning mostly dedup hits or noise gets dropped
  for the day. The rising dedup rate is the drying signal — read it and switch.

The full mechanics of both live in the skills:
`.claude/skills/source-leads` and `.claude/skills/qualify-leads`.

---

## After qualifying — the funnel walk

Only leads that pass both gates get a walk. The walk assigns the Lane, produces the verified Finding, and sets `Finding Verified`. Only then does a lead become `Audit Ready` and eligible to send.

**This is the bottleneck and it is supposed to be.**

Every new opener needs a verified finding, so the day's opener headroom (the send ceiling minus follow-ups due — 20/day ramping to 30, see `send-cap status`) is the real daily walk workload. Plan the day around the walks, not the sends.

## The hard gate

**No send without `Finding Verified` checked.**

A send with a thin or generic finding is worse than no send. It burns the lead, burns the domain, and produces a data point that means nothing.
