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
| Finding Type | select | "No opt-in capture" / "Weak/no nurture sequence" / "Broken checkout" / "No order bump/upsell" / "Weak sales page" / "No launch system" / "Dead/stale element" / "Broken booking flow" / "No visible pricing" / "Other". Prefer "Dead/stale element" for time-bound breakage (stale cohort/webinar dates, empty calendars, dead links, expired events, placeholders) — most warm repliers in the old track lived there. Set from bank #1. |
| Findings Bank | text | **Lane 1 only.** Every visually-confirmed finding that survived both filters, ranked strongest first, one compact line each, all UNUSED on a fresh walk: `1. UNUSED \| <finding, one felt-cost phrase>`. The send gate parses these lines (`crm-gate send --carries second-finding` needs an UNUSED entry past #1), so keep the exact `N. UNUSED \| text` shape. Never mark anything USED here — only confirmed-send logging flips statuses. Lane 2/3: leave empty. |
| Status | select | A freshly walked Lane 1 lead stays "Qualifying" (finding proposed, not yet verified); it becomes "Audit Ready" only after the `finding-verifier` returns VERIFIED and `Email Verified` is set. "Lane 2" if Lane 2 — the dedicated no-leak status (added 2026-07-16; it was a Qualifying hold before that). "Disqualified" if Lane 3 or any gate fail. |
| Est. Value | select | "Track A ($200)" default / "Track B ($700)" when real launch or sales volume is visible / "Unknown". |
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
Every visually-confirmed finding that survived both filters, ranked strongest
first. One numbered line each: the finding as a felt cost, then its innocent
explanation after " — innocent: ". #1 restates the Lane + Finding opener; #2
onward is Touch 2/3 material. Mirror the same ranking into the `Findings Bank`
PROPERTY in compact form (`N. UNUSED | finding`) — the property is what the
send gate parses, the body section is what a human (and the drafting skill)
reads.

## Loom Skeleton
(Lane 1 only — omit for Lane 2/3.)
Three lines, written at walk time while the funnel is fresh in context, so a
"yes, show me" reply turns into a recorded walkthrough in 30 minutes instead
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
