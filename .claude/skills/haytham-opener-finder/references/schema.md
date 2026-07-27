# UAE CRM Schema + Page Body Format

## Pipeline database (UAE Lead CRM)

- **Data source ID** (MCP `collection://`): `5efbdd9b-1e19-468c-96db-f94a525846e0`
- **Database ID** (REST API `/v1/databases/`): `5a9fc583160046d1a64c4e65cc804229`
- Full operating spec (views, lifecycle, SQL, gates): `docs/uae-track/01-crm-operating-spec.md`

**NEVER write to the old parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`). It runs live threads only, no new leads.

## Properties reference

Usually already set at sourcing/qualifying time: Contact Name, Site URL, Profile URL, Source Channel, City (maybe), Email (maybe).

The walk fills / updates:

| Property | Type | What to set |
|---|---|---|
| City | select | Dubai / Abu Dhabi / Sharjah / Other UAE / Unconfirmed. Gate 0 needs a confirmed UAE base — "Unconfirmed" means Gate 0 can't pass yet. |
| Coach Type | multi_select | Business / Life / Fitness / Career / Mindset / Leadership / Health / Other |
| Platform | select | Kajabi / Teachable / Thinkific / Podia / Skool / GHL / Systeme / WordPress / Squarespace / Wix / Other / Unknown. Infer from page design, URL, or checkout style. |
| Phone Number | phone_number | Decision-maker phone / WhatsApp if publicly listed on the site (footer, contact page) or profile. Optional, leave blank if not visible. Enables the WhatsApp pivot on warm trust-verification threads. |
| Audience Size | number | Largest owned or social channel. Floor is 1,500. Leave blank if not visible. |
| Gate 0 | select | Pass / Fail. Set from the four floors (UAE-based, funnel exists, 30-day activity, 1,500 audience). |
| Gate 1 | select | Pass / Fail. The solo-operator test. |
| Lane | select | "Lane 1: Felt leak" / "Lane 2: No leak" / "Lane 3: Skip" |
| Finding Verified | checkbox | **The walker never checks this — it PROPOSES the finding and leaves this unchecked.** It is the hard send gate, checked only by the independent `finding-verifier` on a VERIFIED verdict. Lane 2/3 never carry it. |
| Finding Type | select | "No opt-in capture" / "Weak/no nurture sequence" / "Broken checkout" / "No order bump/upsell" / "Weak sales page" / "No launch system" / "Dead/stale element" / "Broken booking flow" / "No visible pricing" / "Other". Set from bank #1. Descriptive only — it classifies the CALL BAIT, not the opener (the opener is a cold read and carries no finding). No new option was added for the calendar check; "Broken booking flow" covers it. |
| Findings Bank | text | **Lane 1 only.** Every visually-confirmed finding that survived both filters, ranked depth-first, one compact line each: `N. RESERVED \| DEPTH \| verified:YYYY-MM-DD \| <finding, one felt-cost phrase>`. **Every finding is `RESERVED` since 2026-07-27** — no finding is emailed, so there is no opener entry and nothing is spent by a send. They are call bait. `DEPTH` = `SHALLOW` or `DEEP` (self-fixability — see `walk.md`); `verified:` = **today's date, stamped at walk time**. Rank 1 is the strongest and is what the `finding-verifier` certifies. Example: `1. RESERVED \| DEEP \| verified:2026-07-27 \| pricing split across 4 platforms` / `2. RESERVED \| SHALLOW \| verified:2026-07-27 \| booking button drops to a form`. Both tags mandatory. If no deep finding exists, all lines are SHALLOW and the low-value flag goes in `Notes` — still sendable, just weak call bait. Lane 2/3: leave empty. |
| Status | select | A freshly walked Lane 1 lead stays "Qualifying" (finding proposed, not yet verified); it becomes "Audit Ready" only after the `finding-verifier` returns VERIFIED and `Email Verified` is set. "Lane 2" if Lane 2 — the dedicated no-leak status (added 2026-07-16; it was a Qualifying hold before that). "Disqualified" if Lane 3 or any gate fail. |
| Est. Value | select | LEGACY — the options are still worded against the retired Track A / Track B prices. Set `Unknown` on new rows: The First Five bills per booked call, so there is no per-lead deal value to estimate at walk time. |
| Notes | text | One line. Strongest finding, warm-up angle, or one-line flag. Full detail goes in the body. Email-source problems go FIRST. |

Sequence, Touch #, Last Contacted, Next Action, Price Discovery Answer, Discovery Anchor, Lost Reason — leave alone. Those belong to the email skill, uae-tick, and Haytham during outreach.

`SMYKM Hook` (the property): leave for `haytham-hook-finder`. The walk only writes the placeholder line in the page body.

## Page body structure (exact format, always in this order)

Every lead page body follows this structure. Write it fresh — don't append to existing content unless a walk is already there and you're adding to the email thread log.

```
## Overview
One short paragraph. Name, business, coach type, city, platform, main offer,
audience. Human context that doesn't fit in a field.

## Funnel Walk
One line per stop where something was found or ruled out. Skip clean, unremarkable stops.
Format: Stop X (name) — [what's there] — [what it means]

## Evidence
Three lines, always present (the vision gate's own output, never a paraphrase):
- Site vision pass: [paste the literal `python main.py vision check evidence/<slug>`
  output, e.g. "VISION PASS: COMPLETE — 6 of 6 required images confirmed read"].
  If the line says INCOMPLETE, write INCOMPLETE, plus which paths, plus the
  reason if known — do not round up to "read."
- Pasted evidence: [what Haytham pasted/attached, one line] OR "none — crawl-only walk".
- Machine flags rejected in the vision pass: [N — one-word reason each] OR "none rejected".

## Gates
Gate 0: Pass/Fail — one line per floor that mattered (UAE base, funnel, activity, audience).
Gate 1: Pass/Fail — solo-operator signals or gatekeeper flags, one to two lines.

## Lane + Finding
Three lines max.
- Lane verdict + one-phrase reason.
- The strongest verified finding (Lane 1 — bank #1) or warm-up angle (Lane 2). Omit entirely if Lane 3.
- Innocent explanation (Lane 1, required): the plausible non-blame reason for the
  finding, one phrase. Feeds the either/or closing question in the email.

## Findings Bank
(Lane 1 only — omit the section body for Lane 2/3, write "(empty — no verified
findings banked)".)
Every visually-confirmed finding that survived both filters, ranked depth-first
(deep over shallow, then tier, then sting). One numbered line each: the finding
as a felt cost, its depth tag (shallow/deep), then its innocent explanation
after " — innocent: ". #1 is the strongest call bait and the one the
finding-verifier certifies. ALL of them are call-only — name each as a cost,
never write the fix, and never put any of them in an email. If no deep
finding exists, note "low-value: no deep finding to reserve" here and in
`Notes`. Mirror the same ranking into the `Findings Bank` PROPERTY in compact
form (`N. RESERVED | DEPTH | verified:YYYY-MM-DD | finding`) — the property is
what the send gate parses, the body section is what a human reads. Stamp
`verified:` with today's date as you write it.

## Call Prep
(Lane 1 only — omit for Lane 2/3. Renamed from "Loom Skeleton" 2026-07-27
with the Loom offer; the artifact stayed because the call is now the product.)
Three lines, written at walk time while the funnel is fresh in context, so a
booked call opens with specifics instead
of a re-research session (slow artifact delivery was the old track's #1
controllable failure):
- Show: [the exact page/element to put on screen, with URL — where the finding lives]
- Fix: [the one change to walk through, in her platform's terms]
- Done state: [what she'd see working when it's fixed — the before/after in one phrase]

## SMYKM Hook
SMYKM hook: not run yet — see haytham-hook-finder
(`haytham-hook-finder` is the only skill that overwrites this line, from real
public evidence — LinkedIn, podcast, YouTube, About page — with the source cited.
Every other line in this body belongs to opener-finder; hook-finder must never
touch them.)

## Email Thread Log
(Leave blank on a fresh walk — the email skill and Haytham fill it after sends.)

## Price Discovery
(Leave blank on a fresh walk — filled when the discovery question goes out.
Question sent: [date] / Their answer (VERBATIM): "..." / Anchor: [option].)
```

## Writing rules for the page body

- Stop-by-stop format: "Stop X (Name): [what's there] — [what it means]." Skip stops that were clean and unremarkable.
- Lane verdict in one phrase. Opening angle in one to two sentences max.
- No editorializing, no hedging, no "it might be worth considering." State what's there and what it means.
- The Email Thread Log and Price Discovery sections are always left blank by this skill.
- The Evidence section requires the vision gate's literal output line. A body that says "screenshots read" without that line is a false statement.
