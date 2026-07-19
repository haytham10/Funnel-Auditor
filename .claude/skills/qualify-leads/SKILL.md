---
name: qualify-leads
description: Mechanically gate the UAE Lead CRM's raw `Sourced` rows — run Gate 0 (UAE-based, has a funnel/paid product, active in last 30 days, 1,500+ audience) and Gate 1 (solo operator, no gatekeeper) over each one, promoting survivors to `Qualifying` and killing fails to `Disqualified`. Triage speed, not a funnel walk — it resolves each floor with the cheapest tool that settles it (Firecrawl first, a no-login Apify actor for a login-walled follower count on LinkedIn/IG/YouTube), never a crawl. Use WHENEVER Haytham says "qualify the raw names," "qualify the sourced rows," "run Gate 0 on the batch," "gate the leads," "run the gates," "clear the Sourced pile," or when a batch of fresh `Sourced` rows needs gating before it can reach the Walk Queue. This is the step BETWEEN sourcing (`source-leads`, which only collects `Sourced` rows) and the funnel walk (`batch-audit`/`process-lead`, which works `Qualifying` rows). It never sources new candidates, never walks funnels, never sends anything, and never logs in to or acts as Haytham on any platform. Reads and writes the UAE Lead CRM only, never the parenting DB.
---

# Qualify Leads — the mechanical gate, as a skill

**One job: turn raw `Sourced` rows into `Qualifying` or `Disqualified`.**
This is triage, not the walk. `source-leads` collects candidates with no
judgment; this skill applies the cheap mechanical floors so only real fits
reach the Walk Queue; `batch-audit`/`process-lead` then run the full 5-stop
walk on the survivors. This skill sits in the middle and does the gating —
nothing else.

It's the sibling of `batch-audit`: both process rows that already exist in
the CRM at a given status, and both now run the **same verified orchestration**
(`docs/agent-orchestration.md`) — fan out workers, then independently verify
the claim the stage self-certifies. batch-audit walks `Qualifying` rows one
agent per lead; this skill gates `Sourced` rows a *slice of rows* per agent
(a gate is ~2 fetches, far too cheap to justify one cold agent per row; the
walk is a full crawl + vision pass, so it goes per lead). The claim this stage
self-certifies is the Gate 0/1 verdict — and it has asymmetric, expensive
failure modes — so the verifier re-checks it on every promotion and every kill.

**Resolve each floor with the cheapest tool that settles it; decide, don't
defer.** Firecrawl first for anything on the open web; a no-login Apify actor
(`apify li-profile` / `ig --mode details` / `youtube`) only for a follower count
Firecrawl can't read off a login/JS-walled channel. The old qualifier stalled
leads at "unconfirmed audience" whenever Firecrawl couldn't see the number — the
fix is to spend the few-cent actor call, not to defer. Still no crawl: the full
5-stop walk happens later in batch-audit on survivors; a fetch that turns into a
10-page crawl has drifted — stop it. The full per-datum tool map + cost
discipline lives in `.claude/agents/qualifier-worker.md`.

**CRM (all reads and writes):**
`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
**Never write to the parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`).

The ICP, one line: a UAE-based solo coach or course creator with a real
funnel or paid digital product, active in the last 30 days, operating in
English. Full targeting spec: `docs/uae-track/03-targeting-and-sourcing.md`.

---

## The run — orchestrator

**Once, up front (before spawning workers):** `pip install -q -r requirements.txt`
(a missing dep once silently broke the whole `main.py` CLI and degraded every
worker to Firecrawl-only while `APIFY_TOKEN` was present), then `python main.py
apify limits` — pass the `near_cap` flag into every worker prompt so they skip the
actors if the monthly budget is tight. One check, not one per lead.

**Size the batch to downstream demand.** Pull the `Sourced` rows, but qualify
only enough to keep the Walk Queue full, not the whole pile — batch-audit's run
cap is 20 and walks size to send headroom, so qualifying 60 rows into a queue
that can absorb 20 this week just ages the extra verdicts. Name the leftover for
the next run.

**Fan out, don't loop.** Split the batch into slices (roughly 15 rows each) and
spawn one **`qualifier-worker`** per slice, at most 5 running at once. Each
worker runs the Gate 0 → Gate 1 mechanics below over its slice — Gate 0 first
(all four), then Gate 1 on Gate 0 survivors only, resolving each blocked datum
with the cheapest tool (Firecrawl first, then the count-only actor per channel),
`audit/gates.py` for the machine-checkable half (audience 1,500, activity 30
days, funnel present; UAE residency comes back needs-review for the judgment
layer). Rows are disjoint by construction, so each worker **writes its own
verdicts** — there is no cross-worker merge. It returns a per-row summary block.

**Verify, don't trust.** Then spawn a **`qualifier-verifier`** over every
**promotion and every kill** the workers made. It re-runs `audit/gates.py` and
re-confirms the three judgment inputs the worker self-certified: the audience
number's provenance (a real *seen* count, not a vibe — the soft pass that once
sent three leads into full walks), the UAE-base evidence, and the solo/team
read. The failure modes are asymmetric and both expensive: a false **Qualify**
burns a full 185–268K-token walk downstream; a false **Disqualify** kills a real
lead for good (`source-leads` never re-sources a hard Disqualify). The verifier
flips any verdict it can't stand behind back to `Sourced` / `Not checked` with
the reason; only verifier-confirmed promotions reach the Walk Queue. If it
overturns ≥2 of the first wave, pause and surface it before spending the rest.

The Gate 0 / Gate 1 mechanics and the writes-per-lead below are the per-row spec
each worker executes; the orchestration above wraps them (`docs/agent-orchestration.md`).
A genuinely tiny pile (a handful of rows) can run inline with no fan-out — the
orchestration earns its keep on a real batch, not on three rows.

### Gate 0 — all four must be true. Resolve, then decide; any fail = Disqualified

- **UAE-based:** site footer/About/LinkedIn location says Dubai, Abu Dhabi,
  Sharjah, or UAE. "Serves the region" from elsewhere = Fail. Not on the site?
  resolve it — `li-profile.location.full`, or a UAE phone (+971) in a
  YouTube/site `description` — before deferring. Only genuinely conflicting or
  unfindable → City `Unconfirmed`, Gate 0 `Not checked`.
- **Has a funnel or paid product:** the site shows a sales page, checkout,
  course, or paid digital offer. Call-only, DM-only, or brochure-only = Fail.
  (Firecrawl the resolved Site URL — this floor stays Firecrawl, no paid
  detector.)
- **Activity recency:** something posted, emailed, or launched in the last 30
  days — Firecrawl the site/blog/`/videos` page, else `li-posts --since month`
  / `ig --mode posts --newer-than "30 days"`. Dormant = Fail.
- **Audience floor:** 1,500+ on their largest channel. **Resolve the real
  number with the count-only actor for that channel** (`li-profile`
  followerCount / `ig` followersCount / `youtube` subscriberCount) when
  Firecrawl can't see it — do NOT leave it `Not checked` just because it wasn't
  on the homepage. **Never stamp Pass on a guessed number** (a likes count read
  as followers, "looks big"): the actor's real count is a Pass; a guess is not.
  Only when no channel yields a countable number → the honest verdict is a Fail
  (or `Not checked` if a plausible channel just couldn't be located), never a
  soft Pass — that soft pass once sent three leads into walks that all failed on
  the real number.

### Gate 1 — the solo test (2 seconds, on Gate 0 survivors only)

Team or gatekeeper between Haytham and the owner? "Our team", agency
footer, support@ ticketing, named marketing lead = Fail → Disqualified.
Own face, own story, single-person About = Pass.

---

## Writes per lead

- **Fail** → `Gate 0`/`Gate 1` = Fail (whichever failed), Status =
  `Disqualified`, one-line reason in Notes. Set and move on, do not linger.
- **Genuinely can't resolve** (after trying the cheap tools) → leave the failing
  check `Not checked`, `Unconfirmed` + what you tried in Notes, Status stays
  `Sourced`. Do NOT guess it into a Pass or a Fail — but "I didn't try the actor"
  is not "can't resolve."
- **Pass both** → `Gate 0` = Pass, `Gate 1` = Pass, Status = `Qualifying`,
  plus City / Platform / Audience Size / Coach Type filled with whatever
  the triage fetches surfaced.

---

## The run report

The sourced → qualified funnel math: N raw pulled, N Gate-0 fails (broken
out by which floor), N Gate-1 fails, N left `Not checked` / unconfirmed, N
promoted to `Qualifying`. Then the Walk Queue count and the reminder of
what's next: batch-audit works the Walk Queue at up to 20 per run — walks/day
must keep pace with the **combined** send ceiling across both inboxes
(`python main.py send-cap status --all`, each inbox ramping 20 → 25 → 30 on its
own, so capacity is additive, not one pooled number), since every opener under
it needs a walked, verified finding behind it.

---

## Hard rules

- **This skill gates; it never sources.** It reads existing `Sourced` rows
  and never creates new candidates. Finding more leads is `source-leads`'s
  job — do not drift into it.
- **No funnel walks.** The walk is batch-audit's job, on `Qualifying` rows,
  with the vision gate. A follower-count actor call or a light scrape per datum
  is fine; a fetch that turns into a crawl has drifted — stop it.
- **Never guess a gate input, but resolve it first.** An unconfirmed UAE-base or
  audience number stays visibly unconfirmed (`Not checked`, `Unconfirmed`) —
  never a soft Pass. The fix is the cheap actor call that gets the real number,
  not a guess and not a lazy defer. A guessed number poisons the Walk Queue and
  burns a walk.
- **Never log in to, act as, or automate anything through Haytham's accounts on
  any platform.** Read-only, no-login fetching — Firecrawl plus the no-login
  Apify actors — is the ceiling.
- Never write to the parenting DB. This skill reads and writes the UAE Lead
  CRM only.
- Out of scope stays out: agencies/teams, non-English funnels, coaches
  outside the UAE however adjacent. A Gate that lets one of these through
  dilutes the geographic thesis.
