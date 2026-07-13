# UAE Lead CRM — Operating Spec

Machine-readable reference for operating the UAE Coach Pipeline CRM via the Notion MCP.
Written for Claude Code. Last updated 2026-07-13.

> Adopted into the repo 2026-07-13 with corrections confirmed by Haytham:
> - **The AED price is 735, not 550.** $200 is canonical; 550 AED (~$150) was a
>   conversion error. Track A = 735 AED, Track B = 2,575 AED (both round the
>   pegged conversion up to the nearest 5 so the AED figure is never below the
>   dollar price). Discovery Anchor options updated to match, and Track B
>   anchor options added.
> - The turn-two artifact (recorded walkthrough) is tracked in the lead's
>   page body, not as a Status — see the lifecycle note below.
> - Both hard gates are enforced in code, not convention: `python main.py
>   crm-gate offer|send` (see §6).

---

## 1. IDs (copy these exactly)

| Object | ID / URL |
| --- | --- |
| HQ hub page | `39c382c8-4585-81a1-9710-c3247ebf7157` |
| Database | `5a9fc583160046d1a64c4e65cc804229` |
| **Data source (use for all queries/writes)** | `collection://5efbdd9b-1e19-468c-96db-f94a525846e0` |
| Doc: Targeting Spec | `39c382c8-4585-8193-9917-de60bd94d0c7` |
| Doc: Sourcing SOP | `39c382c8-4585-8169-b0df-ce840918b228` |
| Doc: Daily System | `39c382c8-4585-817f-9894-c16e77498877` |

### Views

| View | ID |
| --- | --- |
| All Leads | `39c382c8-4585-8175-b262-000c38e7745d` (board: Pipeline Board) |
| All Leads (table) | `e6f21f28-d377-4eca-b59f-d4ff9dad3474` |
| 🔥 Today | `39c382c8-4585-816e-bad3-000c4011b5df` |
| 📤 Send Queue | `39c382c8-4585-81aa-9d49-000c0ad49a3f` |
| 🔬 Walk Queue | `39c382c8-4585-8194-bba1-000cf32dee66` |
| 💬 Live Threads | `39c382c8-4585-817f-90e3-000cd221a0a0` |
| 💰 Price Discovery Study | `39c382c8-4585-812b-8a35-000cc323df37` |
| 🔎 Qualifying | `39c382c8-4585-8173-b1e9-000c6eeb772d` |

### DO NOT TOUCH

The old parenting Lead Pipeline DB is `c6209e29-55ef-4781-b735-73b2a254e34f`.
It runs in parallel (live threads only, no new leads). Never write UAE leads into it.
Archived old DB `afb13dd2-100f-4f8f-bcfc-42186ab3c63d` — never use.

---

## 2. Schema

SQLite table name is the data source URL, quoted:
`"collection://5efbdd9b-1e19-468c-96db-f94a525846e0"`

| Property | Type | Notes |
| --- | --- | --- |
| `Contact Name` | title | |
| `Email` | email | Required before any send. |
| `Site URL` | url | Funnel entry point. |
| `Profile URL` | url | LinkedIn / wherever found. |
| `City` | select | `Dubai` `Abu Dhabi` `Sharjah` `Other UAE` `Unconfirmed` |
| `Coach Type` | multi_select | `Business` `Life` `Fitness` `Career` `Mindset` `Leadership` `Health` `Other` |
| `Platform` | select | `Kajabi` `Teachable` `Thinkific` `Podia` `Skool` `GHL` `Systeme` `WordPress` `Squarespace` `Wix` `Other` `Unknown` |
| `Audience Size` | number | UAE floor is 1500. |
| `Source Channel` | select | `ICF Directory` `Coach Directory` `Google Footprint` `LinkedIn` `Podcast` `Event Speaker` `Lateral` `Other` |
| `Gate 0` | select | `Pass` `Fail` `Not checked` |
| `Gate 1` | select | `Pass` `Fail` `Not checked` |
| `Lane` | select | `Lane 1: Felt leak` `Lane 2: No leak` `Lane 3: Skip` |
| `Finding Verified` | checkbox | **HARD GATE.** `__YES__` / `__NO__` in SQL. |
| `Finding Type` | select | `No opt-in capture` `Weak/no nurture sequence` `Broken checkout` `No order bump/upsell` `Weak sales page` `No launch system` `Dead/stale element` `Broken booking flow` `No visible pricing` `Other` |
| `SMYKM Hook` | text | One line, real public evidence only. Never fabricated. |
| `Status` | select | see lifecycle below |
| `Sequence` | select | `Cold` `Warm` |
| `Touch #` | number | Increment on every send incl. follow-ups. |
| `Last Contacted` | date | |
| `Next Action` | date | Today view sorts on this. |
| `Price Discovery Answer` | text | **VERBATIM.** Never paraphrase. |
| `Discovery Anchor` | select | Track A: `Above 735 AED` `At 735 AED` `Below 735 AED` · Track B: `Above 2575 AED` `At 2575 AED` `Below 2575 AED` · plus `Refused to name` `Not asked yet` |
| `Est. Value` | select | `Track A ($200)` `Track B ($700)` `Retainer` `Unknown` |
| `Lost Reason` | select | `No reply` `Price` `Not interested` `Bad timing` `Went elsewhere` `Ghosted after reply` `Wrong fit` `Other` |
| `Notes` | text | One-line flags only. Detail goes in page body. |
| `Created` | created_time | system |
| `Last Update` | last_edited_time | system |

### Date properties in SQL/writes

Expand into three columns:
- `date:Next Action:start` (ISO 8601)
- `date:Next Action:end` (null for single dates)
- `date:Next Action:is_datetime` (0)

Same pattern for `Last Contacted`.

---

## 3. Lifecycle (Status)

```
Sourced → Qualifying → Audit Ready → Outreach Sent → Reply Received
  → Price Discovery Sent → Offer Sent → Call Booked → Won
```

Terminal / off-ramps: `Lost`, `Dormant`, `Disqualified`

**The turn-two artifact has no Status of its own.** The artifact offer and
its delivery (the recorded walkthrough of their live page) happen inside
`Reply Received` and are logged in the page body's Email Thread Log. The
discovery question goes out after the reply (usually after the artifact
lands, riding the warmth it creates) and always BEFORE any priced offer.

### Transition rules

| From → To | Requires |
| --- | --- |
| Sourced → Qualifying | Name + site captured |
| Qualifying → Audit Ready | `Gate 0` = Pass, `Gate 1` = Pass, funnel walk done, `Lane` set, `Finding Verified` = checked |
| Qualifying → Disqualified | Either gate = Fail. Set and move on, do not linger. |
| Audit Ready → Outreach Sent | Touch #1 sent. Set `Last Contacted`, `Next Action`, `Touch #` = 1, `Sequence` = Cold. **Gate: `crm-gate send` must print PASS first.** |
| Outreach Sent → Reply Received | They replied. Set `Sequence` = Warm |
| Reply Received → Price Discovery Sent | **MANDATORY STEP.** Discovery question sent. |
| Price Discovery Sent → Offer Sent | Their answer logged verbatim in `Price Discovery Answer`, `Discovery Anchor` set. **Gate: `crm-gate offer` must print PASS first.** |
| Any → Dormant | 4 cold touches, no reply. |
| Any → Lost | Explicit no, or ghost after reply. Always set `Lost Reason`. |

---

## 4. Hard rules (do not violate)

1. **No send without `Finding Verified` = checked.** The finding produces the reply rate. A thin finding burns the lead and the domain. Enforced by `python main.py crm-gate send`.
2. **12-15 cold sends/day maximum.** One inbox, one domain. This is a deliverability ceiling. Enforced by the same gate (`--sends-today`, hard cap 15).
3. **Price discovery happens BEFORE the priced offer**, not after a stall. This is the entire point of the track. Enforced by `python main.py crm-gate offer`.
4. **`Price Discovery Answer` is logged verbatim.** Not summarized.
5. **The price never moves.** Per Grand Slam Offer v2. A low anchor is market data, not an instruction to discount. Objections get bonuses or restructured terms.
6. **Never write UAE leads into the parenting DB.**

---

## 5. Voice rules for any generated copy

- No operator jargon: never "funnel", "conversion", "audit", "sequence".
- **No em-dashes anywhere, ever.**
- Proper capitalization. Capitalize every sentence start and always capitalize "I".
- No sign-off or name at the end of email drafts (Gmail auto-signature handles it).
- One finding per opener, never stacked.
- SMYKM hook must be specific and falsifiable, never a performed reaction.
- Casual register, human on the first try. Tone comes from word choice and rhythm, not dropped capitalization.
- No weak closing lines, ever. "No pressure / no rush / whenever timing's right" stays banned in every message type, including silence-breakers.

---

## 6. Common operations

### Get today's work
Query view `39c382c8-4585-816e-bad3-000c4011b5df` (🔥 Today).

### Get the send queue
Query view `39c382c8-4585-81aa-9d49-000c0ad49a3f` (📤 Send Queue).
Only leads with a verified finding appear here. If empty, do walks before sending.

### Get leads needing a funnel walk
Query view `39c382c8-4585-8194-bba1-000cf32dee66` (🔬 Walk Queue).

### Count pipeline by status
```sql
SELECT "Status", COUNT(*) AS cnt
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
GROUP BY "Status" ORDER BY cnt DESC
```

### Pull the price discovery study
```sql
SELECT "Contact Name", "Discovery Anchor", "Price Discovery Answer",
       "Coach Type", "Audience Size", "Status", "Lost Reason"
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "Discovery Anchor" != 'Not asked yet'
```

### Find stalled threads (the failure mode from the last pipeline)
```sql
SELECT "Contact Name", "Status", "Touch #", "date:Last Contacted:start"
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "Status" IN ('Reply Received','Price Discovery Sent','Offer Sent')
  AND date("date:Last Contacted:start") < date('now','-5 days')
```

### Daily send-count check (deliverability guard)
```sql
SELECT date("date:Last Contacted:start") AS d, COUNT(*) AS sends
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "date:Last Contacted:start" IS NOT NULL
GROUP BY d ORDER BY d DESC LIMIT 14
```
Any day over 15 is a deliverability risk. Flag it.

### The transition gates (run before the transitions they guard)

Dump the lead row's properties (fetched FRESH from Notion, verbatim) to a
JSON file, then:

```bash
# Before setting Offer Sent, or drafting any priced offer:
python main.py crm-gate offer /path/to/row.json

# Before queueing/logging any cold send (today's count from the SQL above):
python main.py crm-gate send /path/to/row.json --sends-today N
```

Exit 0 + a literal `CRM GATE (...): PASS` line, or exit 1 with the reasons.
Quote the tool's exact output line in any report — never paraphrase a PASS.
Same trust model as the vision gate: fetch fresh, pipe verbatim.

---

## 7. Page body format for a lead

Each lead page body should carry, in this order:

```
## Overview
Who they are, audience, offers, platform, city, solo-operator evidence.

## Funnel Walk
Stop 1 (entry point): ...
Stop 2 (freebie/opt-in): ...
Stop 3 (offer page): ...
Stop 4 (checkout/booking): ...
Stop 5 (own audience): ...

## Evidence
Site vision pass: [literal `python main.py vision check` output line]
Pasted evidence: [what Haytham supplied, or "none — crawl-only walk"]
Machine flags rejected: [N + one-word reasons, or "none rejected"]

## Gates
Gate 0: pass/fail + why
Gate 1: pass/fail + why

## Lane + Finding
Lane assignment. The one verified finding. The innocent explanation.

## SMYKM Hook
One line, with the source it came from.

## Email Thread Log
[date] — Touch #N — Subject: "..." — Sent
[body]
Reply: [verbatim, or "No reply"]
Artifact: [offered/delivered + date, or omit]
Next: [date + planned action]

## Price Discovery
Question sent: [date]
Their answer (VERBATIM): "..."
Anchor: above / at / below 735 AED (Track A) or 2575 AED (Track B)
```

---

## 8. Context: why this track exists

The parenting cold pipeline: 125 cold-touched leads, ~364 touches, 11 replies (~9%), **0 closes**.
Only 2 of those 11 ever surfaced a real priced objection. Nobody was ever asked what they'd pay.

The outreach mechanic works. The close does not, and there is no data explaining why.

This track holds the mechanic constant, changes the market (UAE), and adds the one missing step
(price discovery before the offer). Review date: **2026-08-15**.
