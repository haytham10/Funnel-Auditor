# UAE Lead CRM — Operating Spec

Machine-readable reference for operating the UAE Coach Pipeline CRM via the Notion MCP.
Written for Claude Code. Last updated 2026-07-14.

> Adopted into the repo 2026-07-13 with corrections confirmed by Haytham:
> - ~~**The AED price is 735, not 550.**~~ **SUPERSEDED 2026-07-27.** Track A
>   (735 AED) and Track B (2,575 AED) are retired along with the whole
>   funnel-fix offer. The live offer is The First Five: 1,500 AED setup
>   credited against the first three calls, then 600 AED per call that
>   actually happens. See `docs/uae-track/02-the-offer-first-five.md`. The
>   `Discovery Anchor` options still carry the old wording and are legacy
>   buckets, not live pricing.
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
| 💸 Asked For Price | `3a7382c8-4585-81be-9b04-000c02607c46` (added 2026-07-24) |
| 🎯 Constraint Board | `3a7382c8-4585-8145-9a6c-000c59480cf2` (added 2026-07-24, board) |
| 💰 Price Discovery Study (concluded) | `39c382c8-4585-812b-8a35-000cc323df37` |
| 🔎 Qualifying | `39c382c8-4585-8173-b1e9-000c6eeb772d` |

**💸 Asked For Price** — `Asked For Price` = checked, `Last Contacted` desc.
The highest-intent leads in the system, and the ones most likely to go stale
unattended: on the day this view was created it held Avneet Kohli and Rita
Baki, both 3-4 days cold after explicitly asking what it costs. That failure
is what the view exists to make impossible.

**🎯 Constraint Board** — grouped by `Status`, filtered to `Reply Received` /
`Offer Sent` / `Call Booked` (plus the legacy `Leak Fix Sold`). **reply → call is the
constraint** (0 of 9 replies have ever converted), so it gets its own board
rather than being a slice of the full pipeline.

**💰 Price Discovery Study (concluded)** — kept for the historical record, not
worked. 3 rows, all `Refused to name`, 0 numbers. The study is over; see §4
rule 3.

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
| `Email Verified` | checkbox | **SEND GATE.** `__YES__` / `__NO__` in SQL. Checked only after `python main.py email-verify <addr>` prints PASS (deliverability confirmed, not just syntax+MX — a bounce burns that inbox's sending domain), or `python main.py email-enrich` prints `EMAIL ENRICH: PASS` on a name-guessed address it adopted (that line IS a verify PASS on the adopted mailbox), or Haytham checks it by hand to accept a catch_all/unknown risk. `crm-gate send` fails closed on this. |
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
| `Finding Type` | select | `Unbooked calendar` `No opt-in capture` `Weak/no nurture sequence` `Broken checkout` `No order bump/upsell` `Weak sales page` `No launch system` `Dead/stale element` `Broken booking flow` `No visible pricing` `Other` — **`Unbooked calendar` added 2026-07-27** (acquisition state, DEEP, the preferred opener; everything else on this list is a funnel-mechanics defect and usually SHALLOW). Notion select options must be added by hand in the UI. |
| `Findings Bank` | text | Every verified finding from the walk, ranked depth-first (deep over shallow, then tier, then sting), one per line: `N. STATUS \| DEPTH \| verified:YYYY-MM-DD \| finding`. `STATUS` ∈ `UNUSED` / `USED-Tn` / `RESERVED` (the one deep finding held as call bait, never emailed); `DEPTH` ∈ `SHALLOW` / `DEEP` (self-fixability); `verified:` is the date this finding was last confirmed still true (set at walk time, bumped by `python main.py refresh-finding`). E.g. `1. USED-T1 \| SHALLOW \| verified:2026-07-20 \| booking button drops to a form` / `2. UNUSED \| DEEP \| verified:2026-07-24 \| pricing split across 4 platforms` / `3. RESERVED \| DEEP \| verified:2026-07-24 \| whole program readable free`. #1 is the opener; touches 2-3 draw the next UNUSED entry (never the RESERVED one). Statuses flip to `USED-TN` only at confirmed-send logging. `crm-gate send --carries second-finding` parses this property, skips RESERVED, and warns when no DEEP entry exists. Legacy lines without a DEPTH or `verified:` tag still parse — but a missing `verified:` tag now fails the freshness gate (below), so a pre-2026-07-26 lead needs a `refresh-finding` pass before its next send/offer. |
| *(freshness)* | — | **HARD GATE (2026-07-26), the Rita Baki case.** `crm-gate send` fails if the drawn finding's `verified:` date is more than 3 days old. **`crm-gate offer` no longer has a freshness ceiling** (removed 2026-07-27): its rationale was "a priced offer quotes work, so the work must still need doing", which was true of the retired funnel-fix offer and is not true of The First Five, which quotes no work against the finding. Applies to EVERY touch, cold or warm (touch 1 opener, touch 2/3, and touch 4+ warm bumps alike — fixed 2026-07-26, an upper bound used to let warm touches past 3 skip this check entirely, which is the exact shape of the real incident: Rita was at Touch 5). `python main.py refresh-finding <row.json> --rank N --url <finding-url> --baseline-file <file> [--save-baseline-to <file>]` is the cheap re-check (single-URL fetch + diff, not a full re-walk) run before every send/offer — an UNCHANGED page auto-stamps `verified:` and hands back the ready-to-write `new_findings_bank`, no hand-edit; a CHANGED page never auto-stamps and needs a human read (or a fresh vision pass) first. See `audit/crm_gate.py`'s module docstring and `docs/journal.md` (2026-07-21/25). |
| `SMYKM Hook` | text | One line, real public evidence only. Never fabricated. |
| `Status` | select | see lifecycle below (incl. `Draft Ready` and `Scheduled`, added 2026-07-14; `Lane 2`, added 2026-07-16). `Price Discovery Sent`, `Leak Fix Sold` and `Leak Fix Delivered` are all legacy — no new lead enters them. |
| `Inbox` | select | `Inbox 1` `Inbox 2` (added 2026-07-16). Which sending inbox this lead's whole thread goes out of — a LOGICAL label, mapped to a real address + transport by the registry (`audit/inboxes.py`; Inbox 1 = auto-mate.one via Gmail MCP, Inbox 2 = gethaytham.com via `main.py gmail-gethaytham`). Assigned once, sticky for the life of the thread. Blank = unassigned; routing fills it when the lead first enters the send queue. Each inbox has its OWN send ceiling. |
| `Sequence` | select | `Cold` `Warm` |
| `Touch #` | number | Increment on every send incl. follow-ups. |
| `Last Contacted` | date | |
| `Next Action` | date | Today view sorts on this. |
| `Asked For Price` | checkbox | Added 2026-07-24. Set when a lead explicitly asks what it costs. **The highest-intent signal in the CRM**, and the second route through `crm-gate offer` on its own. Filterable via the "Asked For Price" view. |
| `Cash Collected` | number (AED) | Added 2026-07-24. Real money actually received from this lead. All-time total was 0 AED and there was nowhere to record it when that changed. |
| `Price Discovery Answer` | text | **VERBATIM.** Never paraphrase. **Advisory since 2026-07-24**, not blocking — `crm-gate offer` reports it as a note. Keep collecting it. |
| `Discovery Anchor` | select | **LEGACY buckets**, worded against the retired Track A / Track B prices: `Above/At/Below 735 AED`, `Above/At/Below 2575 AED`, plus `Refused to name` `Not asked yet`. **Advisory since 2026-07-24.** Do not add options and do not read the labels as live pricing — for a fresh answer only `Refused to name` carries meaning; everything else belongs in the verbatim `Price Discovery Answer`. `Refused to name` reads as a TRUST signal, not a price signal, and the gate emits a WARNING note saying so. |
| `Est. Value` | select | **LEGACY as of 2026-07-27** — every option is worded against a retired price (`Track A ($200)` `Track B ($700)` `Leak Fix (500 AED)` `Sprint (2575 AED)` `Funnel Watch (600/mo)` `Retainer` `Custom` `Unknown`). The First Five bills per booked call, so there is no per-lead deal value at walk time: set `Unknown` on new rows. Note: no comma in `Sprint (2575 AED)` — Notion rejects commas in select option names. |
| `Lost Reason` | select | `No reply` `Price` `Not interested` `Bad timing` `Went elsewhere` `Ghosted after reply` `Wrong fit` `Other` `No measurable audience`. **Scope changed 2026-07-27**: stops being used for disqualifications the moment `Disqualification Reason` exists — reverts to meaning "lost after engagement" (a reply came in, then the thread died). Existing pre-2026-07-27 rows are NOT backfilled; Wave 2 sources those from `docs/leads/_dq-extraction.json` instead. |
| `Gate 0 Failed Floors` | multi_select | Added 2026-07-27. `Not UAE-based` `No funnel or paid offer` `Inactive 30d` `Audience below floor` — which of Gate 0's four floors actually fired (a lead can fail more than one). Set alongside `Gate 0 = Fail`, before moving to `Disqualified`. See `docs/uae-track/schema-delta.md` for the Airtable mapping and the spelling hazard vs. `Disqualification Reason` (different property, deliberately different wording — do not conflate). |
| `Gate 1 Failed Reason` | select | Added 2026-07-27. `Team gatekeeper` `Agency-run` `Assistant-managed` `Other`. Set alongside `Gate 1 = Fail`. |
| `Disqualification Reason` | select | Added 2026-07-27. 11-option taxonomy data-derived from `docs/leads/_dq-extraction.json` (246 already-disqualified rows) — see that file or `docs/uae-track/schema-delta.md` for the exact option strings and definitions. Set whenever `Status` moves to `Disqualified`. Coarser than `Gate 0 Failed Floors`/`Gate 1 Failed Reason` and includes non-gate reasons (`Duplicate/re-sourced by mistake`, `Lane 3 skip`). |
| `Hook Type` | select | Added 2026-07-27. `WORK` `LIFE` `METRIC` `No hook found`. Written by the `hook-verifier` the same moment it writes the resolved `SMYKM Hook` line — it already has the cited source in hand. |
| `Hook Source URL` | url | Added 2026-07-27. The citation for the SMYKM line, written alongside `Hook Type`. |
| `Last Reply Type` | select | Added 2026-07-27. `Interested` `Price question` `Brush-off` `Logistics` `Blunt` `Decline`. **Denormalised convenience mirror of the most recent reply only** — the authoritative per-reply type lives in the `TOUCH:` line's `type=` token in the page body (`docs/uae-track/log-grammar.md`), because a lead can have several replies of different types. Never analyse off this property; it exists for views and the Constraint Board. |
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
  → Reply Received
  → Call Booked          (legacy: Leak Fix Sold → Leak Fix Delivered)
  → Offer Sent → Won
```

Terminal / off-ramps: `Lost`, `Dormant`, `Disqualified`, `Lane 2`

**`Leak Fix Sold` and `Leak Fix Delivered` are LEGACY as of 2026-07-27** —
kept so historical rows keep gating, but nothing new reaches them. The
turn-two is now a **call ask with two specific times**, and a lead who accepts
goes straight to `Call Booked`, which is both the product and the status that
passes `crm-gate offer`.

*(Historical: added 2026-07-24 as the paid turn-two rungs. The offer was the
48-Hour Leak Fix (500 AED, paid
after; 365 AED up front as the alternative), and before these statuses
existed a paying customer had nowhere to sit. `Leak Fix Sold` = they said
yes and access is being arranged; `Leak Fix Delivered` = the fix is live and
working, `Cash Collected` set. Either one, like `Call Booked`, earns the
right to the priced Sprint offer.

**`Price Discovery Sent` is LEGACY.** Do not move new leads into it. The
price discovery question was falsified as an email step on 2026-07-24 (see
§4 rule 3). Existing rows sitting there are worked like `Reply Received`.

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
Gmail awaiting Haytham's send. As of 2026-07-19 the hook resolution AND the
draft are one **merged hook+draft stage** (`haytham-hook-finder`, draft-first):
Audit Ready → Draft Ready happens in a single pass, so Haytham reviews finished
drafts in Gmail rather than approving bare hooks. `Scheduled` = Haytham scheduled the send in
Gmail and it has not departed yet — the message is in neither `in:sent`
nor drafts, which is why this state exists: without it, scheduled sends
are invisible to the daily count and get logged with future dates. Both
are optional pass-throughs (a hand-sent draft can jump Draft Ready →
Outreach Sent directly; Scheduled only appears when he actually schedules).
`Outreach Sent` means the message ACTUALLY departed — it must have a
matching message in Gmail's sent mail, and uae-tick reconciles this every
morning (Scheduled rows whose message has departed get flipped to
Outreach Sent with the real departure date).

**The turn-two artifact is a call ask with two specific times.** The ask is
made inside `Reply Received` and logged in the page body's Email Thread Log;
if they accept a time, the row moves to `Call Booked`.

**Every turn-two ends in a call ask she can accept in one word.** Never a
question about her business, never a menu, never a soft exit, and never a
calendar link sitting beside the times (that pair is a menu by this track's
own definition).

Three retired shapes, none to be reinstated: the free Loom (3 offers, 0
takers), the price discovery question (3 asks, 3 refusals, 0 numbers), and
the paid 48-Hour Leak Fix (retired 2026-07-27 with the funnel-fix offer —
findings don't sell, because the lead fixes them and leaves).

### Transition rules

| From → To | Requires |
| --- | --- |
| Sourced → Qualifying | Name + site captured |
| Qualifying → Audit Ready | `Gate 0` = Pass, `Gate 1` = Pass, funnel walk done, `Lane` set, `Finding Verified` = checked, AND `Email Verified` = checked (deliverability confirmed via `email-verify`, or Haytham accepted a catch_all/unknown risk by hand). Both hard gates are set before a lead is declared sendable — a verified finding on an address that bounces still burns the domain. |
| Qualifying → Disqualified | Either gate = Fail. Set and move on, do not linger. |
| Qualifying → Lane 2 | Walk complete, both gates Pass, but no felt leak survives the two filters (`Lane` = `Lane 2: No leak`). `Finding Verified` stays unchecked. Warm-up angle in Notes; no cold send. Do NOT leave these at Qualifying. |
| Audit Ready → Draft Ready | The merged **hook+draft stage** (`haytham-hook-finder`, draft-first) does this in one pass: SMYKM hook line resolved (hook-worker → hook-verifier writes the line), `Inbox` assigned if still blank (`python main.py inbox route` → set the label), `crm-gate send … --inbox "<label>"` PASS (which now requires `Email Verified` checked, not just an `@`-shaped address), Gmail draft created IN THAT INBOX (Inbox 1 → Gmail MCP `create_draft`; Inbox 2 → `python main.py gmail-gethaytham draft`). Sets nothing else — a draft is not a send. |
| Draft Ready → Scheduled | Haytham scheduled the send in Gmail (tick detects it in the scheduled queue, or he says so). |
| Audit Ready / Draft Ready / Scheduled → Outreach Sent | Touch #1 ACTUALLY departed (matching message in Gmail sent mail). Set `Last Contacted` (real departure date), `Next Action` (+3 days), `Touch #` = 1, `Sequence` = Cold. **Gate: `crm-gate send … --touch 1 --followups-due M` must have printed PASS at queue time.** |
| Outreach Sent → Reply Received | They replied. Set `Sequence` = Warm |
| Reply Received → Call Booked | They accepted one of the two times proposed in the turn-two call ask. NOT gated — a booked call IS the rung that earns the priced offer, so gating it would deadlock the motion. *(Replaced `Reply Received → Leak Fix Sold` on 2026-07-27.)* |
| Leak Fix Sold → Leak Fix Delivered | LEGACY (retired 2026-07-27). Historical rows only. |
| Reply Received → Call Booked | They took the calendar link instead. |
| Any → (`Asked For Price` checked) | They explicitly asked what it costs, at any stage. Not a status change — a checkbox, and the highest-intent signal in the CRM. It is the second route through the offer gate on its own. |
| [Leak Fix Delivered / Leak Fix Sold / Call Booked / `Asked For Price`] → Offer Sent | The lead has EARNED a number. **Gate: `crm-gate offer` must print PASS first** — an earned `Status` (`Call Booked`, `Offer Sent`, `Won`, or the legacy `Leak Fix Sold` / `Leak Fix Delivered`) or `Asked For Price` checked. `Price Discovery Answer` / `Discovery Anchor` are advisory and reported, never blocking. |
| ~~Reply Received → Price Discovery Sent~~ | **RETIRED 2026-07-24.** Do not use. The discovery question no longer goes out over email. |
| Any → Dormant | 3 cold touches (day 0, 3, 9), no reply. There is no touch 4. Set Next Action to a revival bump 2-3 weeks out — if that date lands on a Sunday, bump it to Monday (sends are paused every Sunday; a 2-3 week/multiple-of-7 offset from a Sunday lands back on a Sunday). |
| Any → Lost | Explicit no, or ghost after reply. Always set `Lost Reason`. |

---

## 4. Hard rules (do not violate)

1. **No send without `Finding Verified` = checked AND `Email Verified` = checked.** The finding produces the reply rate; a thin finding burns the lead and the domain. The verified address protects deliverability; a bounce burns that inbox's sending domain the whole ramp is built to protect (`email-check` is syntax+MX only and PASSED for two addresses that then hard-bounced — `email-verify` is the deliverability confirm). Both enforced by `python main.py crm-gate send`, which fails closed on either flag.
2. **Never past a sending inbox's daily ceiling — PER INBOX, never pooled.** The ceiling is TOTAL sends leaving THAT inbox (openers + follow-ups + warm replies, both tracks). Each inbox is a separate domain with its own reputation, so each has its own independent ramp in `send_cap.json` (keyed by logical label, fails closed to 20 per inbox), moved 20 → 25 → 30 only by Haytham's explicit `python main.py send-cap set --inbox "<label>"` after 7+ days of that inbox's deliverability holding; **30 is the hard cap for ONE inbox — more volume means more inboxes, never a bigger number.** A lead's sends count against its assigned `Inbox`. Follow-ups due on an inbox eat that inbox's budget first; its openers get what's left. Enforced by `crm-gate send --sends-today N --touch T [--followups-due M] --inbox "<label>"` (`--sends-today` = that inbox's own count). Which inbox a new lead lands on: `python main.py inbox route`.
3. **The lead must have EARNED a number before any priced offer.** Either an earned `Status` (`Call Booked`, `Offer Sent`, `Won`, or the legacy `Leak Fix Sold` / `Leak Fix Delivered`) or `Asked For Price` checked. Enforced by `python main.py crm-gate offer`. The turn-two call ask is exempt — a booked call IS the rung that earns the right. *(Changed 2026-07-24. The old rule was "price discovery happens BEFORE the priced offer, this is the entire point of the track". It was tested: across 100 touched leads, 182 touches and 9 replies, the question was asked 3 times, produced 3 answers, all `Refused to name`, and 0 numbers; two of the three refusers asked US for a price instead. Nobody names a budget to a stranger over email. The refusal is a trust signal, not a price signal — the answer to it is more risk reversal, never a smaller number. The question moved to the call.)*
4. **`Price Discovery Answer` is logged verbatim** whenever a lead volunteers anything. Not summarized. Advisory now, not blocking — still the best qualitative data in the system.
5. **The price never moves.** Per Grand Slam Offer v2. A low anchor is market data, not an instruction to discount. Objections get bonuses, restructured terms, or a named rung of the downsell ladder. 3,600 AED is the documented next Sprint price and is gated on 2 closes; do not quote it.
6. **Never write UAE leads into the parenting DB.**
7. **The cold sequence is 3 touches (day 0, 3, 9), then Dormant — and touches 2-3 must carry something new:** the next UNUSED `Findings Bank` entry, the paid leak-fix offer, or the disambiguating question. A bare bump doesn't pass the gate (`--carries`, second-finding claims checked against the bank; `loom-offer` is still accepted as a deprecated alias for `leak-fix-offer`).
8. **A finding older than 3 days can't be sent on, and older than 1 day can't be quoted — on any touch, cold or warm.** (Added 2026-07-26, the Rita Baki case — her 3,200 AED offer was scoped around a leak she'd already fixed herself before it was quoted, and Rita's own thread was on Touch 5 when it happened — a warm bump, not a cold one.) `Findings Bank` entries carry a `verified:YYYY-MM-DD` tag; `crm-gate send` fails on a finding verified >3 days ago, `crm-gate offer` fails past 1 day. `python main.py refresh-finding` is the cheap re-check — a single-URL fetch of just that finding's page (not a full re-walk) that auto-stamps `verified:` when the page comes back unchanged from the stored baseline, and hands back the exact `Findings Bank` value to write.

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

### Pull the price discovery study (CONCLUDED — historical record only)
```sql
SELECT "Contact Name", "Discovery Anchor", "Price Discovery Answer",
       "Coach Type", "Audience Size", "Status", "Lost Reason"
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "Discovery Anchor" != 'Not asked yet'
```

### Pull the leads who asked for a price (the highest-intent queue)
```sql
SELECT "Contact Name", "Status", "date:Last Contacted:start", "Est. Value", "Email"
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "Asked For Price" = '__YES__'
ORDER BY date("date:Last Contacted:start") DESC
```

### The constraint: reply → call
```sql
SELECT "Status", COUNT(*) AS cnt
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "Status" IN ('Reply Received','Leak Fix Sold','Leak Fix Delivered',
                   'Offer Sent','Call Booked','Won')
GROUP BY "Status"
```

### Cash collected, all time
```sql
SELECT SUM("Cash Collected") AS aed_collected, COUNT(*) AS paying_leads
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "Cash Collected" > 0
```

### Find stalled threads (the failure mode from the last pipeline)
```sql
SELECT "Contact Name", "Status", "Touch #", "date:Last Contacted:start"
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE "Status" IN ('Reply Received','Leak Fix Sold','Price Discovery Sent','Offer Sent')
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
#   (second-finding is verified against the row's Findings Bank). Touch 4+
#   (warm) runs the exact same gate — cold and warm are not special-cased:
python main.py crm-gate send /path/to/row.json --sends-today N --touch 2 --carries second-finding

# Before EITHER of the above, when the drawn finding's `verified:` date is
# close to its ceiling (3 days for send, 1 day for offer): the cheap re-check.
# Unchanged auto-stamps `verified:` and prints the ready-to-write bank value;
# changed prints the diff and waits on a human read.
python main.py refresh-finding /path/to/row.json --rank 1 \
    --url https://theirsite.com/the-finding-page \
    --baseline-file docs/leads/<slug>/evidence/finding-1-baseline.txt \
    --save-baseline-to docs/leads/<slug>/evidence/finding-1-baseline.txt
```

Exit 0 + a literal `CRM GATE (...): PASS` line, or exit 1 with the reasons.
Quote the tool's exact output line in any report — never paraphrase a PASS.
Same trust model as the vision gate: fetch fresh, pipe verbatim.

---

## 7. Page body format for a lead

**Changed 2026-07-27** (`docs/uae-track/log-grammar.md`): `## Email Thread
Log`, `## Money`, and the sourcing line under `## Overview` now use a
machine-readable sentinel grammar instead of free prose, so the next
Notion -> Airtable migration is a parser (`audit/touchlog.py`), not a
per-lead recovery session. **This applies to logs written from now on —
existing pre-2026-07-27 page bodies are NOT rewritten**, and
`parse_body()` is tolerant of the old shape so mixed-format pages work
unmodified. The other sections stay prose exactly as before; they migrate
to the repo's walk doc, not to an Airtable field.

Each lead page body should carry, in this order:

```
## Overview
Who they are, audience, offers, platform, city, solo-operator evidence.
SOURCE: channel="..." query="..." date=YYYY-MM-DD

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
Gate 0: pass/fail + why (+ `Gate 0 Failed Floors` set on a fail)
Gate 1: pass/fail + why (+ `Gate 1 Failed Reason` set on a fail)

## Lane + Finding
Lane assignment. The strongest verified finding (bank #1). The innocent explanation.

## Findings Bank
Every verified finding that survived both filters, ranked depth-first (deep
over shallow, then tier, then sting), with each one's depth tag and innocent
explanation. The one deep finding held as call bait is marked RESERVED — its
fix is call-only, never written into email. If no deep finding exists, note
"low-value: no deep finding to reserve" here and in `Notes`. Mirrored compactly
into the `Findings Bank` property (`N. STATUS | DEPTH | verified:YYYY-MM-DD |
finding`, STATUS ∈ UNUSED/USED-Tn/RESERVED) for the send/offer gates to parse
— `verified:` is set to the walk date here and bumped by `refresh-finding` on
every later re-check. **This DSL is unchanged by the 2026-07-27 log-grammar
work** — do not touch it, `parse_findings_bank` and `--carries second-finding`
depend on it exactly as it is.

## SMYKM Hook
One line, with the source it came from. `Hook Type` and `Hook Source URL`
are written as properties at the same moment (the hook-verifier already has
the cited source in hand).

## Email Thread Log
TOUCH: n=1 dir=out date=YYYY-MM-DD inbox="Inbox 1" seq=cold carries=opener subject="..." thread=<gmail-thread-id> gate=<literal crm-gate send verdict>
````
[verbatim body, byte for byte as it left Gmail]
````
TOUCH: n=1 dir=in date=YYYY-MM-DD reply_to=1 type=<Interested|Price question|Brush-off|Logistics|Blunt|Decline> thread=<gmail-thread-id>
````
[verbatim reply, or omit this record entirely if there was no reply]
````

Never hand-type a `TOUCH:` line — build it with `python main.py touch-log
render` (self-lints before printing) and log it in the SAME step that sets
`Touch #` / `Last Contacted` / `Status`, never batched to end of day. Full
token contract, enums, and the legacy-format fallback:
`docs/uae-track/log-grammar.md`.

## Money
OFFER: type="First Five" amount=1500 currency=AED date=YYYY-MM-DD status=Proposed rung=0

One `OFFER:` line per offer made or per status change — append only, never
edit or overwrite a prior line (`python main.py touch-log offer`).

## Price Discovery (advisory, legacy — only if they volunteered something)
Their answer (VERBATIM): "..."
Anchor: a legacy bucket (the options are worded against the retired Track A /
Track B prices), or
`Refused to name` — which reads as a TRUST signal, not a price signal
```

Run `python main.py log-lint <row.json>` (or `--slug <slug>` from the repo
archive) after any touch/offer/source write — it re-derives the touch
history and cross-checks it against `Touch #`, the Findings Bank, and the
inbox registry, and fails closed on any ERROR. See
`docs/uae-track/log-grammar.md` for the full rule set.

---

## 8. Context: why this track exists

The parenting cold pipeline: 125 cold-touched leads, ~364 touches, 11 replies (~9%), **0 closes**.
Only 2 of those 11 ever surfaced a real priced objection. Nobody was ever asked what they'd pay.

The outreach mechanic works. The close does not, and there is no data explaining why.

This track held the mechanic constant, changed the market (UAE), and added the one missing step:
price discovery before the offer.

**That step is falsified as of 2026-07-24.** UAE numbers: 100 touched leads, 182 touches, 9 replies.
The question was asked 3 times. It produced 3 answers, all `Refused to name`, and **0 numbers**.
Two of the three refusers responded by asking US for a price instead. Nobody names a budget to a
stranger over email, and the refusal is a trust signal rather than a price signal.

**The real constraint was never price. It is reply → call, which is 0/9.** So the missing step is
now a *paid tiny yes* — the 500 AED 48-Hour Leak Fix at turn-two — and the gate moved from "you
extracted their number" to "you earned the right to name a number." Review date: **2026-08-15**.
