---
name: qualify-leads
description: Mechanically gate the UAE Lead CRM's raw `Sourced` rows — run Gate 0 (UAE-based, has a funnel/paid product, active in last 30 days, 1,500+ audience) and Gate 1 (solo operator, no gatekeeper) over each one, promoting survivors to `Qualifying` and killing fails to `Disqualified`. Triage speed, not a funnel walk — budget ~2 fetches per lead (site + one search), never a crawl. Use WHENEVER Haytham says "qualify the raw names," "qualify the sourced rows," "run Gate 0 on the batch," "gate the leads," "run the gates," "clear the Sourced pile," or when a batch of fresh `Sourced` rows needs gating before it can reach the Walk Queue. This is the step BETWEEN sourcing (`source-leads`, which only collects `Sourced` rows) and the funnel walk (`batch-audit`/`process-lead`, which works `Qualifying` rows). It never sources new candidates, never walks funnels, never sends anything, and never logs in to or acts as Haytham on any platform. Reads and writes the UAE Lead CRM only, never the parenting DB.
---

# Qualify Leads — the mechanical gate, as a skill

**One job: turn raw `Sourced` rows into `Qualifying` or `Disqualified`.**
This is triage, not the walk. `source-leads` collects candidates with no
judgment; this skill applies the cheap mechanical floors so only real fits
reach the Walk Queue; `batch-audit`/`process-lead` then run the full 5-stop
walk on the survivors. This skill sits in the middle and does the gating —
nothing else.

It's the sibling of `batch-audit`: both process rows that already exist in
the CRM at a given status. batch-audit walks `Qualifying` rows; this skill
gates `Sourced` rows. The difference is depth — a gate is ~2 fetches, a
walk is a full crawl + vision pass.

**Budget ~2 fetches per lead (site + one search), not a crawl.** The full
5-stop walk happens later, in batch-audit, on Qualifying survivors only. A
qualifying fetch that turns into a 10-page crawl has drifted — stop it.

**CRM (all reads and writes):**
`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
**Never write to the parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`).

The ICP, one line: a UAE-based solo coach or course creator with a real
funnel or paid digital product, active in the last 30 days, operating in
English. Full targeting spec: `docs/uae-track/03-targeting-and-sourcing.md`.

---

## The run

Pull every `Sourced` row. For each, run the gates MECHANICALLY, in order —
Gate 0 first (all four), then Gate 1 on Gate 0 survivors only. Set the
result and move on. Do not linger, do not walk, do not enrich beyond what
the two triage fetches surface.

The machine-checkable half of Gate 0 is available from `audit/gates.py`
(audience 1,500, activity 30 days, funnel present; UAE residency comes back
as needs-review for the judgment layer) — use it where it helps, but the
judgment calls below are yours.

### Gate 0 — all four must be true. Any fail = Disqualified, move on

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

### Gate 1 — the solo test (2 seconds, on Gate 0 survivors only)

Team or gatekeeper between Haytham and the owner? "Our team", agency
footer, support@ ticketing, named marketing lead = Fail → Disqualified.
Own face, own story, single-person About = Pass.

---

## Writes per lead

- **Fail** → `Gate 0`/`Gate 1` = Fail (whichever failed), Status =
  `Disqualified`, one-line reason in Notes. Set and move on, do not linger.
- **Can't-tell on UAE-base or audience** → leave the failing check
  `Not checked`, the value `Unconfirmed` in Notes, Status stays `Sourced`,
  flag for a second look. Do NOT guess it into a Pass or a Fail.
- **Pass both** → `Gate 0` = Pass, `Gate 1` = Pass, Status = `Qualifying`,
  plus City / Platform / Audience Size / Coach Type filled with whatever
  the triage fetches surfaced.

---

## The run report

The sourced → qualified funnel math: N raw pulled, N Gate-0 fails (broken
out by which floor), N Gate-1 fails, N left `Not checked` / unconfirmed, N
promoted to `Qualifying`. Then the Walk Queue count and the reminder of
what's next: batch-audit works the Walk Queue at up to 20 per run — walks/day
must keep pace with the send ceiling (`python main.py send-cap status`,
ramping 20 → 25 → 30), since every opener under it needs a walked, verified
finding behind it.

---

## Hard rules

- **This skill gates; it never sources.** It reads existing `Sourced` rows
  and never creates new candidates. Finding more leads is `source-leads`'s
  job — do not drift into it.
- **No funnel walks.** The walk is batch-audit's job, on `Qualifying` rows,
  with the vision gate. Budget ~2 fetches per lead here. A qualifying fetch
  that turns into a crawl has drifted — stop it.
- **Never guess a gate input.** An unconfirmed UAE-base or audience number
  stays visibly unconfirmed (`Not checked`, `Unconfirmed` in Notes) — never
  a soft Pass. A guessed number poisons the Walk Queue and burns a walk.
- **Never log in to, act as, or automate anything through Haytham's
  accounts on any platform.** Read-only public fetching via Firecrawl is
  the ceiling.
- Never write to the parenting DB. This skill reads and writes the UAE Lead
  CRM only.
- Out of scope stays out: agencies/teams, non-English funnels, coaches
  outside the UAE however adjacent. A Gate that lets one of these through
  dilutes the geographic thesis.
