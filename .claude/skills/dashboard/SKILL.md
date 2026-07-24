---
name: dashboard
description: Build the command-center dashboard — one fused visual picture of the whole UAE pipeline (Notion CRM state) plus sending reality (both Gmail inboxes) plus the deliverability ceilings, rendered as a self-contained Claude Artifact. Use WHENEVER Haytham says "dashboard," "show me the board," "command center," "the big picture," "refresh the dashboard," "how's everything looking," or when a scheduled Routine fires this skill. It reads the CRM and Gmail (read-only), assembles a snapshot, renders the HTML with `python main.py dashboard render`, and publishes/updates the Artifact at a stable URL. It never sends anything, never drafts, never writes to the CRM, and never logs in to or acts as Haytham on any platform. UAE Lead CRM only, never the parenting DB.
---

# Dashboard — the command center

One job: fuse **pipeline state** (Notion), **sending reality** (both Gmail
inboxes), and the **deliverability ceilings** (`send_cap.json`) into a single
self-contained page, published as a Claude Artifact at a stable URL Haytham can
open on his phone or desktop. Read-only end to end — this skill never sends,
drafts, or writes CRM state.

**The split (same trust model as `crm-gate`):** Python owns the deterministic
pieces (the per-inbox ceilings, the registry, Inbox 2's real sent-today count,
validation, and the HTML rendering). This skill owns the MCP fetching — Notion
and Inbox 1's Gmail, which Python cannot reach. Fetch fresh, fill the snapshot,
pipe it through the renderer, quote nothing you didn't fetch.

**CRM:** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST database ID `5a9fc583160046d1a64c4e65cc804229`). Full schema, views, and
SQL: `docs/uae-track/01-crm-operating-spec.md`. **Never** touch the parenting DB
`c6209e29-55ef-4781-b735-73b2a254e34f`.

---

## Step 1 — the Python-reachable base

```bash
python main.py dashboard skeleton
```

This prints the base snapshot JSON: `generated_at` / `generated_day` (Dubai),
the per-inbox meters with each inbox's ceiling + ramp status, and — for the
**direct-API inbox (Inbox 2 / gethaytham)** — its real `sent_today`,
`sent_scheduled` (today's departures only, day-scoped — see Step 3), AND
`sent_scheduled_next_day` (tomorrow's departures already committed from the
scheduled queue) counts, all fetched by Python. Every Notion-sourced and
Gmail-MCP panel is seeded `null` for you to fill in place. Each meter also
carries `count_query` (`in:sent after:<dubai-midnight-epoch>`),
`scheduled_query` (`in:scheduled`), and `next_day` (tomorrow's Dubai date,
ISO) for the Gmail-MCP inbox to run itself. The Today/Tomorrow toggle on the
rendered Inboxes card reads `sent_scheduled_next_day` — leave it `null` (not
`0`) if you can't determine it, so the card shows "count not fetched yet"
rather than a fabricated zero.

Save this JSON to the scratchpad as `snapshot.json`; you will fill its null
fields and keep the Python-filled ones verbatim.

---

## Step 2 — fill the Notion panels (MCP)

Run these against the data source with `mcp__Notion__notion-query-data-sources`
(or query the named views listed in the spec §1). Write each result into the
matching snapshot key.

- **`pipeline.by_status`** — counts per Status:
  ```sql
  SELECT "Status", COUNT(*) AS cnt
  FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
  GROUP BY "Status" ORDER BY cnt DESC
  ```
  Shape it as `{"pipeline": {"by_status": {"Sourced": N, ...}}}`. The renderer
  orders the funnel itself and surfaces any unknown status rather than dropping
  it.

- **`replies`** — leads awaiting a human read (top of the brief). Reply Received
  rows, plus anything with a bounce flag in `Notes`:
  ```sql
  SELECT "Contact Name", "Status", "date:Last Contacted:start", "Notes"
  FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
  WHERE "Status" = 'Reply Received'
  ```
  Shape: `[{"name","status","last_contacted","note"}, ...]`.

- **`discovery_ladder`** — the CONVERSION ladder (renamed in substance
  2026-07-24; the JSON key is unchanged so the renderer keeps working). Two
  queues:
  - `due_question`: warm leads owed a turn-two — `Status = 'Reply Received'`
    with no Leak Fix offered yet → `[{"name","status","next_action"}]`. The
    turn-two carries the paid 48-Hour Leak Fix or the calendar, never the
    retired price-discovery question.
  - `offer_unlocked`: leads who have EARNED a number —
    `"Status" IN ('Call Booked','Leak Fix Sold','Leak Fix Delivered','Offer Sent','Won')`
    OR `"Asked For Price" = '__YES__'` → `[{"name","anchor","answer"}]` (any
    logged answer stays VERBATIM; it is advisory now, not the unlock).

- **`due_followups`** — `Next Action` at or before today, in the send sequence:
  ```sql
  SELECT "Contact Name", "Touch #", "Inbox", "date:Next Action:start"
  FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
  WHERE "Status" IN ('Outreach Sent','Reply Received')
    AND date("date:Next Action:start") <= date('now')
  ```
  Shape: `[{"name","touch","inbox","carries","next_action"}]` (`carries` is the
  planned new element for touch 2/3, or blank).

- **`send_queue`** — the 📤 Send Queue view (`39c382c8-4585-81aa-9d49-000c0ad49a3f`):
  only verified-finding leads. Shape:
  `[{"name","status","inbox","finding_verified","email_verified"}]` — the
  renderer groups by inbox and splits Draft Ready vs Audit Ready.

- **`price_discovery`** — the CONCLUDED study (spec §6). Kept for the
  historical record: 3 answers, all `Refused to name`, 0 numbers. Nothing new
  enters it.
  ```sql
  SELECT "Contact Name","Discovery Anchor","Price Discovery Answer","Est. Value"
  FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
  WHERE "Discovery Anchor" != 'Not asked yet'
  ```
  Aggregate into `{"anchors": {"<anchor>": count}, "est_value": {"<value>": count}}`.

- **`scoreboard`** — the weekly numbers, BY LEAD not message (unique leads
  cold-touched this week, reply rate, discovery answers, offers, closes). Shape
  as a flat `{"label": value}` map; the renderer draws one tile per entry.

- **`hygiene`** — a list of one-line alert strings: impossible states, missing
  verifications on a queued lead, any inbox over its ceiling today, stale warm
  threads (Reply Received / Price Discovery Sent / Offer Sent with
  `Last Contacted` older than 5 days — see the stalled-threads query in spec §6).

- **`calendar`** — extra dated events for the calendar tab, shape
  `[{"date": "YYYY-MM-DD", "kind": "touch|send|ramp|other", "label": "..."}]`.
  The renderer already derives due follow-ups, discovery-due dates, and each
  inbox's ramp-eligibility day on its own (`build_events` in
  `audit/dashboard.py`) — only add what it can't see: **scheduled sends** (from
  the `in:scheduled` sweep, with their departure dates, kind `send`) and
  **revival bumps** (Dormant leads' future `Next Action`, kind `other`). An
  unknown kind folds to `other`; a malformed date is dropped, so use real ISO
  days.

---

## Step 3 — fill the Gmail counts + replies (branch by transport)

For **each inbox**, use the meter's `count_query` and `scheduled_query`.
Branch on `send_via` (from `python main.py inbox list`):

- **Inbox 1 (`gmail-mcp`):** run `count_query` with `mcp__Gmail__search_threads`
  to count sent messages, write the total to that meter's `sent_today`.
- **Inbox 2 (`gmail-gethaytham`):** `sent_today` is already filled by the
  skeleton — leave it. `sent_scheduled` is also pre-filled, day-scoped by
  `gmail_gethaytham.count_scheduled_by_day()` (see below) — leave it too.

**`sent_scheduled` means "scheduled to depart TODAY," never "everything
currently in the scheduled queue."** `in:scheduled` alone returns every
future-dated scheduled message — a Touch 2 queued tonight to leave tomorrow
morning matches it exactly the same as one departing in the next hour. Only
today's departures belong in the ceiling meter; folding tomorrow's into
today's total overstates usage and can trip a false "over ceiling" reading
(this happened in practice: 10 messages scheduled for the next Dubai day got
added to today's count and showed Inbox 1 as 7 over its cap when it wasn't).
Inbox 2 gets this for free from Python (`count_scheduled_by_day`, which
checks each candidate's actual `Date` header against the target day, called
once for `generated_day` and once more for `next_day`). For **Inbox 1
(`gmail-mcp`, the one Python can't reach)**, do the equivalent by hand —
one fetch, two buckets:

1. Run `scheduled_query` (`in:scheduled`) with `mcp__Gmail__search_threads`.
2. For each thread, find the message with no `labelIds` (the not-yet-sent
   scheduled one) and read its send date from the thread/message detail.
3. Count the ones landing on `generated_day` (Dubai) and write that count to
   `sent_scheduled` (today's meter). Separately count the ones landing on
   `next_day` and write that to `sent_scheduled_next_day` (the Tomorrow
   toggle) — same fetched list, just bucketed by date, no second API call.

Then, for **every inbox**, list the actual scheduled messages (not just the
count) so ALL of them — today's and future ones alike — can be placed on the
calendar — `mcp__Gmail__search_threads` with `in:scheduled` for Inbox 1,
`python main.py gmail-gethaytham search "in:scheduled"` for Inbox 2. For
each one found, add an entry to `snapshot["calendar"]` with its real
departure date, kind `"send"`, and the recipient's name (see Step 2's
`calendar` panel below) — this is the only way scheduled sends reach the
calendar tab; `build_events()` cannot derive them on its own. A future-dated
scheduled send belongs on the calendar even though it's excluded from
today's `sent_scheduled` meter count.

Sweep both inboxes for new replies since the last run and fold anything not
already in the CRM into the `replies` panel as a note (this dashboard does not
write to the CRM — that is uae-tick's job; here it is display only).

---

## Step 4 — render

Write the completed snapshot to the scratchpad and render:

```bash
python main.py dashboard render /path/to/snapshot.json --out /path/to/dashboard.html
```

The renderer **validates** the load-bearing core (fails loudly if the skeleton
was corrupted) and draws every panel — a still-null panel becomes an "awaiting
data" empty state rather than a crash. Quote the `DASHBOARD RENDER: OK` line.

---

## Step 5 — publish / update the Artifact (stable URL)

The dashboard lives at ONE Artifact URL that every refresh updates in place, so
Haytham keeps one bookmark.

1. Read `dashboard_state.json` at the repo root (gitignored). If it has a
   `url`, pass it to the Artifact tool's `url` param so the SAME artifact
   updates. If the file is missing / has no url, publish fresh.
2. Publish `dashboard.html` with the Artifact tool (favicon `📊`, a stable
   title like "Funnel Auditor — Command Center"). The HTML is already a
   self-contained fragment (its own `<title>` + inline `<style>`, no external
   assets) — publish the file as-is.
3. Write the returned URL back to `dashboard_state.json`:
   `{"url": "<artifact url>", "last_refresh": "<generated_at>"}`.

Report the URL to Haytham with a one-line state summary (e.g. "Inbox 2 is 1 over
ceiling; 2 replies waiting").

---

## Scheduling (set up once)

To keep the board fresh without asking, create a Routine that fires this skill
on a daytime cadence. Bind it to this session (or fresh-session mode) with a
prompt like `run the /dashboard skill`, cron e.g. hourly 06:00–22:00 Dubai
(`0 2-18 * * *` in UTC). It updates the same Artifact URL each fire. Cadence is
Haytham's call — offer it, don't assume it.

---

## Hard rules for this skill

- **Read-only.** Never send, never draft, never write a CRM row or advance a
  Status/Touch. This skill only reads and renders.
- **UAE CRM only.** Never read or write the parenting DB.
- **Never fabricate a number.** A count you could not fetch stays `null` — the
  meter shows "unknown", never a fake 0. The skeleton already fails Inbox 2
  closed to `null` when its creds are missing; do the same for anything you
  can't confirm.
- **Never log in as Haytham** on any platform. Everything here is Notion MCP,
  Gmail MCP, and the direct read-only Gmail API — no account impersonation.
