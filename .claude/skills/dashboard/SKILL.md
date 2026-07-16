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
**direct-API inbox (Inbox 2 / gethaytham)** — its real `sent_today` count. Every
Notion-sourced and Gmail-MCP panel is seeded `null` for you to fill in place.
Each meter also carries `count_query` (`in:sent after:<dubai-midnight-epoch>`).

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

- **`discovery_ladder`** — two queues:
  - `due_question`: Reply Received leads not yet asked
    (`"Discovery Anchor" = 'Not asked yet'`) → `[{"name","status","next_action"}]`.
  - `offer_unlocked`: answer logged (`"Discovery Anchor" != 'Not asked yet'` and
    a non-placeholder `Price Discovery Answer`) → `[{"name","anchor","answer"}]`
    (the answer VERBATIM).

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

- **`price_discovery`** — the study (spec §6):
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

For **each inbox**, use the meter's `count_query`. Branch on `send_via`
(from `python main.py inbox list`):

- **Inbox 1 (`gmail-mcp`):** run the query with `mcp__Gmail__search_threads`,
  count sent messages, and add `in:scheduled` due today. Write the total to that
  meter's `sent_today` and the scheduled count to `sent_scheduled`.
- **Inbox 2 (`gmail-gethaytham`):** already filled by the skeleton — leave it.
  (If you want to re-verify: `python main.py gmail-gethaytham search "<query>"`.)

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
