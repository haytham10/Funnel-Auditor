---
name: source-leads
description: Fill and keep filling the UAE Lead CRM's top of funnel, web-natively. Three modes — sourcing (Day-1 bootstrap: volume collection of raw candidates into the CRM as Sourced, no judgment), qualifying (Day-2 bootstrap: mechanical Gate 0 + Gate 1 over Sourced rows, promoting survivors to Qualifying and killing fails to Disqualified), and top-up (the everyday tap: a small, lightweight, repeatable sourcing run you can fire any day for the life of the track). Use WHENEVER Haytham says "source leads," "sourcing day," "fill the pipeline," "run the sprint," "qualify the raw names," "run Gate 0 on the batch," "top up," "source me 20," "find more coaches," "grab some fresh leads," or names a sourcing channel to work (ICF directory, Google footprint, LinkedIn, podcasts, lateral). Works the five channels via Firecrawl search/scrape as the default, plus `apify search` (Google SERP) run alongside Firecrawl on the Google footprint channel — it never sources from Instagram (not a cold-sourcing channel for this track), never logs in anywhere, and never acts as Haytham on any platform. It does not walk funnels (that's batch-audit/process-lead after qualifying) and it never sends anything.
---

# Source Leads — the sourcing engine, as a skill

Three modes, two jobs. The **sprint** (Modes 1 + 2) is a one-time
bootstrap that fills an empty CRM: Day 1 sources ONLY, Day 2 qualifies
ONLY. The **top-up** (Mode 3) is the everyday tap that keeps the pipeline
alive after the bootstrap — a small, repeatable sourcing run you fire on
demand for the life of the track.

The two-day sprint (docs/uae-track/03): **Day 1 sources ONLY, Day 2
qualifies ONLY.** Separating them is the point — mixing sourcing and
qualifying is what makes both slow. Run the one mode Haytham asked for and
do not drift into another. If he asks for "the sprint" without a day, ask
which day this is — that's the one decision that changes everything
downstream. If he asks to "top up," "source me N," or "find more" once the
CRM already has leads in it, that's Mode 3, not a sprint.

**CRM (all writes):** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
**Never write to the parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`).

The ICP, one line: a UAE-based solo coach or course creator with a real
funnel or paid digital product, active in the last 30 days, operating in
English. Full targeting spec: `docs/uae-track/03-targeting-and-sourcing.md`.

---

## MODE 1 — SOURCING (volume, no judgment)

Target for a full Day-1 run: **60-70 raw names**, so 50+ survive Gate 0.
For a smaller ask ("source me 20"), scale accordingly. Collect name +
site + whatever else falls out for free. Do NOT qualify, do NOT walk
funnels, do NOT reject anyone except obvious non-candidates (not a coach,
not plausibly UAE, no site at all).

**Dedup first, once:** pull the CRM's existing Contact Names + Site URLs
in one SQL query at the start of the run. Skip anything already logged,
in any status. Never create a duplicate row.

**Check the Apify quota once, up front, if this run will touch channel 2:**
`python main.py apify limits`. `apify search` is cheap (~$0.002/call,
confirmed 2026-07-16), but it still draws off the same small monthly USD
budget everything else on this layer shares. If `near_cap` is `true`, skip
`apify search` for the whole run and work channel 2 on `firecrawl_search`
alone — note it in the run report, don't silently degrade.

### The five channels (work them in this order)

1. **Coach directories (highest density, start here).** `firecrawl_scrape`
   / `firecrawl_crawl` the ICF UAE chapter directory and regional coach
   directories/marketplaces. Directory listings almost always carry name,
   city, specialty, and a site link — exactly the intake fields.
2. **Google footprint (proof of a paid product baked in).** Run BOTH
   engines on the same query, not one or the other — a same-query
   side-by-side comparison (2026-07-16) showed near-zero URL overlap
   between them on a loose query, and each surfaced a real UAE candidate
   the other missed on a scoped one:
   - `firecrawl_search` for the PLATFORM, not the person:
     `mykajabi.com coach Dubai`, `teachable.com UAE coach`, platform
     domain + city for Thinkific/Podia/Systeme/Skool.
   - `python main.py apify search "<same platform+city query>" --site
     <platform domain> --country ae` — the `--site`/`--country` scoping
     matters far more than which engine runs it; a loose query (no
     `--site`) is weak on both engines, so always scope it.
   - Merge the two result lists and dedupe by URL before triage. A
     platform footprint IS a funnel — these candidates come pre-passed on
     the funnel floor. Set the Platform property while it's free.
3. **LinkedIn (the UAE unlock).** `firecrawl_search` for UAE coaches
   announcing programs/cohorts, then fetch what's PUBLIC. LinkedIn walls
   most content — take what renders, log the profile URL, move on.
   **Never log in, never use Haytham's account, never automate anything
   through it.** If a candidate looks strong but everything is walled,
   log them anyway with what's known; qualifying can dig later.
4. **Podcasts and events (pre-qualified for ambition).** `firecrawl_search`
   Dubai/UAE business podcasts' guest lists, event speaker pages, then
   follow the "where to find me" links to their sites.
5. **Lateral discovery.** From every good candidate found above: who they
   collaborate with, get interviewed by, or are recommended alongside.
   Follow the thread — each good lead is the next anchor.

### What gets logged per candidate (Status = Sourced)

Contact Name, Site URL, Profile URL, City if stated, Coach Type best
guess, Platform if obvious, Audience Size if visible for free, Source
Channel, Status = `Sourced`. Nothing else. No page body, no notes
essays. Speed is the deliverable.

**Site URL is required to log the row (2026-07-14).** It is the one
field the rest of the machine cannot work without, and the first
bootstrap proved the failure mode: 78 rows landed as name-only shells (0
site URLs), which just moved the entire enrichment cost into qualifying
and left the Walk Queue empty. A candidate whose site you can't find in
one obvious hop (their directory entry's link, their LinkedIn contact
section as rendered, one `firecrawl_search` on the name) does NOT get a
CRM row — list them at the end of the run report under "seen, no site
found" so the name isn't lost, and move on. Grab the audience number
whenever it's visible at zero extra cost; never guess it.

Create rows in batches (notion-create-pages takes multiples), not one
call per lead.

### The run report

One message: how many logged per channel, total in CRM at `Sourced`, any
channel that came up dry (and why, one line), and whether the 60-70
target was hit. If it wasn't, say what's left to try — don't quietly
stop short.

---

## MODE 2 — QUALIFYING (mechanical, fast, no funnel walks)

Pull every `Sourced` row. For each, run the gates MECHANICALLY — this is
triage, not the walk. Budget ~2 fetches per lead (site + one search),
not a crawl. The full 5-stop walk happens later (batch-audit) on
Qualifying survivors only.

**Gate 0 — all four must be true. Any fail = Disqualified, move on:**
- **UAE-based:** site footer/About/LinkedIn location says Dubai, Abu
  Dhabi, Sharjah, or UAE. "Serves the region" from elsewhere = Fail.
  Genuinely can't tell = leave City `Unconfirmed` and Gate 0
  `Not checked`, flag for a second look — don't guess either way.
- **Has a funnel or paid product:** the site shows a sales page,
  checkout, course, or paid digital offer. Call-only, DM-only, or
  brochure-only = Fail.
- **Activity recency:** something posted, emailed, or launched in the
  last 30 days (one `firecrawl_search`, or visible on the site/profile).
  Dormant = Fail.
- **Audience floor:** 1,500+ on their largest visible channel. Under it
  with no bigger owned channel in sight = Fail. **A Pass needs a real
  number, not a vibe** — a follower/subscriber count you actually saw. If
  the number isn't cheaply visible, do NOT stamp `Gate 0` = Pass on a soft
  claim ("looks big," "well above floor," a likes count read as followers):
  leave `Gate 0` = `Not checked` with the number unconfirmed in Notes, same
  as the can't-tell UAE-base rule above. A soft "Pass" is exactly what sent
  three leads into a batch that each burned a full walk before failing on
  the real number — an unconfirmed floor must stay visibly unconfirmed, not
  ride into the Walk Queue as a confirmed pass.

**Gate 1 — the solo test (2 seconds, on Gate 0 survivors only):** team or
gatekeeper between Haytham and the owner? "Our team", agency footer,
support@ ticketing, named marketing lead = Fail → Disqualified. Own face,
own story, single-person About = Pass.

**Writes per lead:**
- Fail → `Gate 0`/`Gate 1` = Fail (whichever failed), Status =
  `Disqualified`, one-line reason in Notes. Set and move on, do not
  linger.
- Pass both → `Gate 0` = Pass, `Gate 1` = Pass, Status = `Qualifying`,
  plus City / Platform / Audience Size / Coach Type filled with whatever
  the triage fetches surfaced.

**The run report:** sourced → qualified funnel math (N raw, N gate-0
fails by floor, N gate-1 fails, N at Qualifying), the Walk Queue count,
and the reminder of what's next: batch-audit works the Walk Queue at up
to 20 per run — walks/day must keep pace with the send ceiling
(`python main.py send-cap status`, ramping 20 → 25 → 30), since every
opener under it needs a walked, verified finding behind it.

---

## MODE 3 — TOP-UP (the everyday tap)

The sprint is a one-time bootstrap. Top-up is what keeps the track alive
after it: a small, lightweight sourcing run you fire any day — "source me
20," "top up," "find more coaches," "grab some from LinkedIn." Mechanically
it IS sourcing mode (Mode 1) — same channels, same `Sourced` logging, same
"no judgment, no funnel walks" discipline — shrunk and made repeatable.
Everything in Mode 1's "What gets logged" and "The run report" applies.
Only the four things below differ.

**1. Volume: small by default.** Default target ~15-20 raw names, or
whatever N Haytham names. This is a top-up, not a sprint — do not mine
60-70. The Walk Queue drains at up to ~20/day (the send ceiling's pace); a top-up exists to refill a
day or two of that, not to overflow it.

**2. Source the flow, not the stock.** This is the anti-exhaustion rule
and the reason top-up stays useful for a year. The UAE / English / solo
market has a FINITE stock of coaches — re-mine the same ICF directory
every week and it dries up in a month. So top-up biases to what is NEW
since last time: recently-added directory entries, podcast episodes from
the last few weeks, "just launched / now enrolling / new cohort" LinkedIn
posts, fresh platform footprints. Use recency in the searches (recent
posts, recent episodes, current launches). The sprint mined the
back-catalog once; top-up skims the new arrivals. A top-up run that just
re-scrapes the same back-catalog and leans on dedup to discard it has
drifted — you are burning fetches to find nothing new.

**3. Rotate to the stalest channel (no new schema needed).** Unless
Haytham names a channel, pick the one worked least recently, derived from
data already in the CRM: for each Source Channel, the most recent row's
Created time is when that channel was last worked. Start with the channel
whose most-recent row is oldest (or a channel with zero rows). One SQL
query up front gets this. Name the channel you chose and why in the
report. If Haytham named a channel ("top up from podcasts"), work that one
and skip the rotation logic.

**4. Dedup against EVERY status, Disqualified included.** Same one-time
dedup pull as Mode 1, but be explicit: skip a name/site already in the CRM
in ANY status — Sourced, Qualifying, Disqualified, anything. A coach you
already killed must not come back as a fresh Sourced row. (Future hook,
not built yet: leads that failed Gate 0 only on activity or audience — not
niche or geography — are recheck-later candidates, since a dormant coach
may relaunch; a hard niche/geo Disqualified is dead for good.)

**The top-up report:** how many logged, which channel(s) worked and why
that channel was picked (staleness or named), how many candidates were
seen-but-skipped as already-in-CRM duplicates (the dedup rate is the early
warning that a channel is drying up — call it out if it's high), the new
`Sourced` count, and the reminder that these need Day-2 qualifying (Mode 2)
before they reach the Walk Queue.

---

## Hard rules

- **Never source from Instagram.** Sourcing died there once — browsing as
  Haytham got the account banned — and this whole skill exists because of
  it. This is a *sourcing* exclusion only; it does not touch the separate
  enrichment rule, where read-only no-login IG data is a valid hook source
  (see `haytham-hook-finder`). What is banned is logging in or acting as
  Haytham, on IG or anywhere.
- **Never log in to, act as, or automate anything through Haytham's
  accounts on any platform.** Read-only public fetching via Firecrawl is
  the ceiling. LinkedIn especially: public pages only.
- One mode per run. Sourcing and top-up runs do not qualify; qualifying
  runs do not source. (Lateral discovery inside a sourcing or top-up run
  is still sourcing, not qualifying.) Top-up is sourcing-shaped: it logs
  `Sourced` rows that Mode 2 qualifies later — it never walks or gates.
- No funnel walks in either mode. The walk is batch-audit's job, on
  Qualifying rows, with the vision gate. A qualifying-mode fetch that
  turns into a 10-page crawl has drifted — stop it.
- Never invent a candidate, a city, or an audience number. Unknown is a
  fine value; a guessed one poisons Gate 0.
- Never write to the parenting DB, and never source parenting/faith leads
  into this CRM — that niche is closed.
- Out of scope stays out: agencies/teams, non-English funnels, coaches
  outside the UAE however adjacent. Do not dilute the geographic thesis.
