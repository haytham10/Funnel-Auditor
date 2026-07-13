---
name: source-leads
description: Fill the UAE Lead CRM's top of funnel, web-natively. Two modes matching the two-day sprint — sourcing (volume collection of raw candidates into the CRM as Sourced, no judgment) and qualifying (mechanical Gate 0 + Gate 1 over Sourced rows, promoting survivors to Qualifying and killing fails to Disqualified). Use WHENEVER Haytham says "source leads," "sourcing day," "fill the pipeline," "run the sprint," "qualify the raw names," "run Gate 0 on the batch," or names a sourcing channel to work (ICF directory, Google footprint, LinkedIn, podcasts, lateral). Works the five channels via Firecrawl search/scrape only — it never touches Instagram, never logs in anywhere, and never acts as Haytham on any platform. It does not walk funnels (that's batch-audit/process-lead after qualifying) and it never sends anything.
---

# Source Leads — the two-day sprint, as a skill

The two-day sprint (docs/uae-track/03): **Day 1 sources ONLY, Day 2
qualifies ONLY.** Separating them is the point — mixing sourcing and
qualifying is what makes both slow. This skill runs either mode; run the
one Haytham asked for and do not drift into the other. If he asks for
"the sprint" without a mode, ask which day this is — that's the one
decision that changes everything downstream.

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

### The five channels (work them in this order)

1. **Coach directories (highest density, start here).** `firecrawl_scrape`
   / `firecrawl_crawl` the ICF UAE chapter directory and regional coach
   directories/marketplaces. Directory listings almost always carry name,
   city, specialty, and a site link — exactly the intake fields.
2. **Google footprint (proof of a paid product baked in).**
   `firecrawl_search` for the PLATFORM, not the person:
   `mykajabi.com coach Dubai`, `teachable.com UAE coach`, platform domain
   + city for Thinkific/Podia/Systeme/Skool. A platform footprint IS a
   funnel — these candidates come pre-passed on the funnel floor. Set the
   Platform property while it's free.
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

Contact Name, Site URL (the funnel entry point — the one field the rest
of the machine cannot work without), Profile URL, City if stated,
Coach Type best guess, Platform if obvious, Audience Size if visible for
free, Source Channel, Status = `Sourced`. Nothing else. No page body, no
notes essays. Speed is the deliverable.

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
  with no bigger owned channel in sight = Fail.

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
and the reminder of what's next: batch-audit works the Walk Queue at ~15
per run, matching the 12-15 walks/day the send ceiling implies.

---

## Hard rules

- **Never touch instagram.com.** Sourcing died there once; this whole
  skill exists because of it.
- **Never log in to, act as, or automate anything through Haytham's
  accounts on any platform.** Read-only public fetching via Firecrawl is
  the ceiling. LinkedIn especially: public pages only.
- One mode per run. Sourcing runs do not qualify; qualifying runs do not
  source. (Lateral discovery inside a sourcing run is sourcing, not
  qualifying.)
- No funnel walks in either mode. The walk is batch-audit's job, on
  Qualifying rows, with the vision gate. A qualifying-mode fetch that
  turns into a 10-page crawl has drifted — stop it.
- Never invent a candidate, a city, or an audience number. Unknown is a
  fine value; a guessed one poisons Gate 0.
- Never write to the parenting DB, and never source parenting/faith leads
  into this CRM — that niche is closed.
- Out of scope stays out: agencies/teams, non-English funnels, coaches
  outside the UAE however adjacent. Do not dilute the geographic thesis.
