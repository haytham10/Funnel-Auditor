# UAE Lead CRM — Operating Spec

Machine-readable reference for operating the UAE Coach Pipeline CRM via the Notion MCP.
Written for Claude Code. Last updated 2026-07-14.

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
| `Email Verified` | checkbox | **SEND GATE.** `__YES__` / `__NO__` in SQL. Checked only after `python main.py email-verify <addr>` prints PASS (deliverability confirmed, not just syntax+MX — a bounce burns the one shared domain), or `python main.py email-enrich` prints `EMAIL ENRICH: PASS` on a name-guessed address it adopted (that line IS a verify PASS on the adopted mailbox), or Haytham checks it by hand to accept a catch_all/unknown risk. `crm-gate send` fails closed on this. |
| `Phone Number` | phone_number | Decision-maker phone / WhatsApp if publicly listed. Optional; enables the WhatsApp pivot on warm trust-verification threads. |
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
| `Findings Bank` | text | Every verified finding from the walk, ranked strongest first, one per line: `1. USED-T1 \| finding` / `2. UNUSED \| finding`. #1 is the opener; touches 2-3 draw the next UNUSED entry. Written by the walk; statuses flip to `USED-TN` only at confirmed-send logging. `crm-gate send --carries second-finding` parses this property. |
| `SMYKM Hook` | text | One line, real public evidence only. Never fabricated. |
| `Status` | select | see lifecycle below (incl. `Draft Ready` and `Scheduled`, added 2026-07-14; `Lane 2`, added 2026-07-16) |
| `Inbox` | select | `Inbox 1` `Inbox 2` (added 2026-07-16). Which sending inbox this lead's whole thread goes out of — a LOGICAL label, mapped to a real address + transport by the registry (`audit/inboxes.py`; Inbox 1 = auto-mate.one via Gmail MCP, Inbox 2 = gethaytham.com via `main.py gmail-gethaytham`). Assigned once, sticky for the life of the thread. Blank = unassigned; routing fills it when the lead first enters the send queue. Each inbox has its OWN send ceiling. |
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
Sourced → Qualifying → Audit Ready → Draft Ready → (Scheduled) → Outreach Sent
  → Reply Received → Price Discovery Sent → Offer Sent → Call Booked → Won
```

Terminal / off-ramps: `Lost`, `Dormant`, `Disqualified`, `Lane 2`

**`Lane 2` (added 2026-07-16) is the home for walked leads with no felt
leak** (`Lane` = `Lane 2: No leak`) — both gates can pass but nothing
survived the two filters, so there is no verified finding and no cold send.
Before this status existed, no-leak leads were parked at `Qualifying`,
which was ambiguous (indistinguishable from a not-yet-walked lead); they
now get their own off-ramp. `Finding Verified` stays unchecked. Haytham can
work these by hand with the warm-up angle in Notes, but the machine never
cold-sends them.

**`Draft Ready` and `Scheduled` (added 2026-07-14) make Gmail state
queryable.** `Draft Ready` = hook resolved + a Touch 1 draft sitting in
Gmail awaiting Haytham's send. `Scheduled` = Haytham scheduled the send in
Gmail and it has not departed yet — the message is in neither `in:sent`
nor drafts, which is why this state exists: without it, scheduled sends
are invisible to the daily count and get logged with future dates. Both
are optional pass-throughs (a hand-sent draft can jump Draft Ready →
Outreach Sent directly; Scheduled only appears when he actually schedules).
`Outreach Sent` means the message ACTUALLY departed — it must have a
matching message in Gmail's sent mail, and uae-tick reconciles this every
morning (Scheduled rows whose message has departed get flipped to
Outreach Sent with the real departure date).

**The turn-two artifact has no Status of its own.** The artifact offer and
its delivery (the recorded walkthrough of their live page) happen inside
`Reply Received` and are logged in the page body's Email Thread Log. The
discovery question goes out after the reply (usually after the artifact
lands, riding the warmth it creates) and always BEFORE any priced offer.

### Transition rules

| From → To | Requires |
| --- | --- |
| Sourced → Qualifying | Name + site captured |
| Qualifying → Audit Ready | `Gate 0` = Pass, `Gate 1` = Pass, funnel walk done, `Lane` set, `Finding Verified` = checked, AND `Email Verified` = checked (deliverability confirmed via `email-verify`, or Haytham accepted a catch_all/unknown risk by hand). Both hard gates are set before a lead is declared sendable — a verified finding on an address that bounces still burns the domain. |
| Qualifying → Disqualified | Either gate = Fail. Set and move on, do not linger. |
| Qualifying → Lane 2 | Walk complete, both gates Pass, but no felt leak survives the two filters (`Lane` = `Lane 2: No leak`). `Finding Verified` stays unchecked. Warm-up angle in Notes; no cold send. Do NOT leave these at Qualifying. |
| Audit Ready → Draft Ready | SMYKM hook line resolved (hook-finder ran), `Inbox` assigned if still blank (`python main.py inbox route` → set the label), `crm-gate send … --inbox "<label>"` PASS (which now requires `Email Verified` checked, not just an `@`-shaped address), Gmail draft created IN THAT INBOX (Inbox 1 → Gmail MCP `create_draft`; Inbox 2 → `python main.py gmail-gethaytham draft`). Sets nothing else — a draft is not a send. |
| Draft Ready → Scheduled | Haytham scheduled the send in Gmail (tick detects it in the scheduled queue, or he says so). |
| Audit Ready / Draft Ready / Scheduled → Outreach Sent | Touch #1 ACTUALLY departed (matching message in Gmail sent mail). Set `Last Contacted` (real departure date), `Next Action` (+3 days), `Touch #` = 1, `Sequence` = Cold. **Gate: `crm-gate send … --touch 1 --followups-due M` must have printed PASS at queue time.** |
| Outreach Sent → Reply Received | They replied. Set `Sequence` = Warm |
| Reply Received → Price Discovery Sent | **MANDATORY STEP.** Discovery question sent. |
| Price Discovery Sent → Offer Sent | Their answer logged verbatim in `Price Discovery Answer`, `Discovery Anchor` set. **Gate: `crm-gate offer` must print PASS first.** |
| Any → Dormant | 3 cold touches (day 0, 3, 9), no reply. There is no touch 4. Set Next Action to a revival bump 2-3 weeks out. |
| Any → Lost | Explicit no, or ghost after reply. Always set `Lost Reason`. |

---

## 4. Hard rules (do not violate)

1. **No send without `Finding Verified` = checked AND `Email Verified` = checked.** The finding produces the reply rate; a thin finding burns the lead and the domain. The verified address protects deliverability; a bounce burns the one shared domain the whole ramp is built to protect (`email-check` is syntax+MX only and PASSED for two addresses that then hard-bounced — `email-verify` is the deliverability confirm). Both enforced by `python main.py crm-gate send`, which fails closed on either flag.
2. **Never past a sending inbox's daily ceiling — PER INBOX, never pooled.** The ceiling is TOTAL sends leaving THAT inbox (openers + follow-ups + warm replies, both tracks). Each inbox is a separate domain with its own reputation, so each has its own independent ramp in `send_cap.json` (keyed by logical label, fails closed to 20 per inbox), moved 20 → 25 → 30 only by Haytham's explicit `python main.py send-cap set --inbox "<label>"` after 7+ days of that inbox's deliverability holding; **30 is the hard cap for ONE inbox — more volume means more inboxes, never a bigger number.** A lead's sends count against its assigned `Inbox`. Follow-ups due on an inbox eat that inbox's budget first; its openers get what's left. Enforced by `crm-gate send --sends-today N --touch T [--followups-due M] --inbox "<label>"` (`--sends-today` = that inbox's own count). Which inbox a new lead lands on: `python main.py inbox route`.
3. **Price discovery happens BEFORE the priced offer**, not after a stall. This is the entire point of the track. Enforced by `python main.py crm-gate offer`.
4. **`Price Discovery Answer` is logged verbatim.** Not summarized.
5. **The price never moves.** Per Grand Slam Offer v2. A low anchor is market data, not an instruction to discount. Objections get bonuses or restructured terms.
6. **Never write UAE leads into the parenting DB.**
7. **The cold sequence is 3 touches (day 0, 3, 9), then Dormant — and touches 2-3 must carry something new:** the next UNUSED `Findings Bank` entry, the Loom offer, or the disambiguating question. A bare bump doesn't pass the gate (`--carries`, second-finding claims checked against the bank).

---

## 5. Voice rules for any generated copy

- No operator jargon: never "funnel", "conversion", "audit", "sequence".
- **No em-dashes anywhere, ever.**
- Proper capitalization. Capitalize every sentence start and always capitalize "I".
- **Sign off "Haytham" at the end of every email** (changed Jul 14, 2026: the
  Gmail auto-signature was taken down, so the body must carry the name — the
  old "no sign-off" rule would now ship unsigned mail).
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

### Daily send-count check (deliverability guard) — PER INBOX

The ceiling and the count are two separate reads, and both are **per
inbox** now (one ramp and one count for each sending domain):

- **The ceiling:** `python main.py send-cap status --all` — quote the
  literal block. Each inbox ramps 20 → 25 → 30 on its OWN reputation, by
  Haytham's hand only, and fails closed to 20 per inbox (see
  `audit/send_cap.py`). The additive total is the whole system's capacity.
- **The count:** TOTAL sends that left or WILL leave THAT inbox today, not
  just UAE openers. "Today" is the **Dubai calendar day** (UTC+4 — the
  same day boundary `send_cap.py` uses; compute the date string once and
  use it everywhere). Count each inbox on its own transport:
  - **Inbox 1** (auto-mate.one, Gmail MCP): `in:sent after:<today>`
    **plus** `in:scheduled` due today.
  - **Inbox 2** (gethaytham.com, direct API):
    `python main.py gmail-gethaytham search "in:sent after:<today>"`
    (this inbox is not on the scheduled-send path).
  Warm replies + parenting + deliverability tests all count against
  whichever inbox they left from — they all burn that domain. Scheduled
  sends sit in neither sent nor drafts until they depart, and missing them
  overshoots the ceiling by exactly their count. Cross-check against the
  CRM, split by `Inbox`:

```sql
SELECT date("date:Last Contacted:start") AS d, "Inbox" AS inbox, COUNT(*) AS sends
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "date:Last Contacted:start" IS NOT NULL
GROUP BY d, inbox ORDER BY d DESC LIMIT 28
```

The SQL undercounts by design (one row per lead, UAE only) — when the
two disagree, Gmail wins. Any day over the ceiling is a deliverability
risk. Flag it.

### The transition gates (run before the transitions they guard)

Dump the lead row's properties (fetched FRESH from Notion, verbatim) to a
JSON file, then:

```bash
# Before setting Offer Sent, or drafting any priced offer:
python main.py crm-gate offer /path/to/row.json

# Before queueing/logging any cold send. --sends-today is the Gmail total
# for today; --touch is 1, 2, or 3 (there is no touch 4).
#   Touch 1 opener — follow-ups due today eat the budget first:
python main.py crm-gate send /path/to/row.json --sends-today N --touch 1 --followups-due M
#   Touch 2/3 follow-up — must declare the new thing it carries
#   (second-finding is verified against the row's Findings Bank):
python main.py crm-gate send /path/to/row.json --sends-today N --touch 2 --carries second-finding
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
Lane assignment. The strongest verified finding (bank #1). The innocent explanation.

## Findings Bank
Every verified finding that survived both filters, ranked strongest first,
with each one's innocent explanation. Mirrored compactly into the
`Findings Bank` property (`N. UNUSED | finding`) for the send gate to parse.

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
