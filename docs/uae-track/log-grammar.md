# UAE Lead CRM — page-body log grammar

Standalone reference for the sentinel-line grammar every skill that logs a
touch, reply, offer, or sourcing event writes to. Added 2026-07-27 for the
lossless Notion -> Airtable migration (docs/journal.md, that date). Every
skill that writes to a lead's page body points HERE rather than restating
this — change it once, here.

**Implementation:** `audit/touchlog.py`. **Enforcement:** `python main.py
log-lint`. **The only sanctioned way to write a line:** `python main.py
touch-log render|offer|source` (or the equivalent `render_touch` /
`render_offer` / `render_source` calls if a skill is composing the body
itself before a single Notion write) — nothing hand-types a sentinel line.

This is a **logging-format change**, not an operating change. The pipeline,
gates (`crm_gate.py`, `send_cap.py`, `inboxes.py`), the 3-touch sequence,
the Sunday pause, and the earned-right offer rule are all unchanged and
untouched by this doc. Notion stays the source of truth until Phase 6.

---

## Why this shape

Wave 1 of the migration (122 leads) cost almost all its effort turning
prose into structured rows: 40 of 243 sends (16%) were missing from their
thread logs and had to be recovered from Gmail, 8 sent bodies are
permanently unrecoverable, reply *type* was never data anywhere, Gate 0
stored a verdict but not which floor fired, and parsing was Claude-per-lead
instead of a regex. The fix is not a bigger recovery job — it's writing the
log so `parse_body()` in a loop is the entire migration, no judgement call
per lead.

Two places every Airtable-bound field can live, and never a third:

- **A Notion property** — one value per lead (see
  `01-crm-operating-spec.md` §2 and `schema-delta.md` for the new ones).
- **A sentinel line in a fenced block in the page body** — many per lead
  (a touch, a reply, an offer). That's what this doc defines.

The prose sections (`## Overview`, `## Funnel Walk`, `## Evidence`,
`## Gates`, `## Lane + Finding`, `## Findings Bank`, `## SMYKM Hook`) stay
prose — they migrate to the repo's walk doc, not to an Airtable field, so
they are out of scope here.

---

## Grammar rules

- Sentinel keywords are `TOUCH:`, `OFFER:`, `SOURCE:` — uppercase,
  line-initial, colon-terminated.
- One logical record per physical line. **No wrapping** — a long subject
  stays on one line.
- Tokens are `key=value`, space-separated. A value containing a space,
  `=`, or `"` is double-quoted; a literal `"` inside a value is `\"` (and a
  literal `\` is `\\`).
- A bare `key` with no `=` is invalid (a grammar error, not silently
  skipped).
- Unknown keys are preserved by the parser and reported as a WARNING —
  never silently dropped.
- Every verbatim body (a sent email, a received reply) sits in a
  **four-backtick** fenced block on the line immediately after its
  `TOUCH:` sentinel — four backticks, not three, so a body that itself
  contains a triple-backtick code block still survives.
- Dates are always `YYYY-MM-DD`, Dubai calendar day. Never a datetime,
  never a locale format.
- Records under `## Email Thread Log` are in chronological order.
- Corrections **append a new line**; nothing is ever edited in place
  (same discipline as the Findings Bank DSL).

---

## TOUCH: (Email Thread Log — one per send, one per reply)

```
TOUCH: n=2 dir=out date=2026-07-28 inbox="Inbox 1" seq=cold carries=second-finding finding=3 subject="Quick thing on your checkout page" thread=18f2a9c4b7e1 gate=PASS
````
[verbatim body, byte for byte as it left Gmail]
````
```

A reply is its own `TOUCH:` line, `dir=in`, immediately following the
outbound touch it answers:

```
TOUCH: n=2 dir=in date=2026-07-30 reply_to=2 type="price question" thread=18f2a9c4b7e1
````
[verbatim reply]
````
```

| Token | Required | Values | Airtable field |
|---|---|---|---|
| `n` | yes | integer; matches `Touch #` after the send | Touches · `Touch #` |
| `dir` | yes | `out` / `in` | Touches · `Direction` |
| `date` | yes | `YYYY-MM-DD`, the real departure/receipt date, Dubai calendar | Touches · `Date Sent` |
| `inbox` | yes on `dir=out` | `"Inbox 1"` / `"Inbox 2"` — logical label, quoted | Touches · `Inbox` |
| `seq` | yes on `dir=out` | `cold` / `warm` | Touches · `Sequence` |
| `carries` | yes on `dir=out` where `n>=2` | `opener`, `second-finding`, `call-ask`, `disambiguating-question`, `price-discovery`, `money-email`, `objection-reply`, `reactivation` (`loom-offer` and `leak-fix-offer` are deprecated aliases for `call-ask`, both still accepted so historical logs parse) | Touches · `Carries` |
| `finding` | when `carries=second-finding`, or the touch quotes a finding | the rank number from `Findings Bank` | Touches · `Finding Used` |
| `subject` | yes on `dir=out` | quoted | Touches · `Subject` |
| `thread` | yes | Gmail thread ID | Touches · `Gmail Thread ID` |
| `gate` | yes on `dir=out` | the literal `crm-gate send` verdict token | Touches · `Gate Output` |
| `type` | yes on `dir=in` unless `auto=true`/`bounce=true` | `Interested`, `Price question`, `Brush-off`, `Logistics`, `Blunt`, `Decline` | Touches · reply-type field, and mirrored to the lead's `Last Reply Type` property |
| `reply_to` | yes on `dir=in` | the `n` of the out touch this answers | — |
| `bounce` | only if true | `bounce=true` | excluded from all denominators (reply rate, out-touch numbering) |
| `auto` | only if true | `auto=true` for an autoresponder | logged, never counted as a reply |

`carries` on touch 1 is always `opener`.

---

## OFFER: (## Money — one line per offer made, never overwritten, only appended)

```
OFFER: type="First Five" amount=1500 currency=AED date=2026-07-28 status=Proposed rung=0
OFFER: type="Fewer Calls" amount=1500 currency=AED date=2026-08-02 status=Declined rung=1 objection=price terms="pay after"
```

| Token | Values | Airtable field |
|---|---|---|
| `type` | `First Five`, `Fewer Calls`, `Setup Deferred`, `Custom` — plus the RETIRED `Leak Fix`, `Sprint`, `The Minimum`, `Payment Plan`, `Funnel Watch`, kept in the enum only so historical OFFER: lines still parse | Offers · `Type` |
| `amount` | number, no currency symbol | Offers · `Amount AED` |
| `currency` | `AED` (recorded even though it's always AED — makes the parse total) | — |
| `date` | `YYYY-MM-DD` — the date of THIS status, not necessarily the original proposal date | Offers · `Date Proposed` |
| `status` | `Proposed`, `Accepted`, `Declined`, `Paid`, `Refunded` | Offers · `Status` |
| `rung` | `0` original, `1` payment plan, `2` The Minimum | Offers · `Downsell Rung` |
| `objection` | free text, quoted | Offers · `Objection` |
| `terms` | `pay after`, `50% deposit`, `plan`, `full up front` | Offers · `Payment Terms` |

A status change appends a **new** `OFFER:` line with the same `type` — it
never edits the old line. `log-lint` warns (does not block) when a
non-`Proposed` status line has no earlier `Proposed` line for the same
`type`.

---

## SOURCE: (## Overview — one line, written at sourcing time)

```
SOURCE: channel="Google Footprint" query="Dubai business coach kajabi" date=2026-07-27
```

| Token | Values | Airtable field |
|---|---|---|
| `channel` | free text (matches `Source Channel` select where possible) | Sources · `Channel` |
| `query` | the literal query string that produced this lead | Sources · `Query` |
| `date` | `YYYY-MM-DD` | Sources · `Date` |

This is what makes source yield answerable one level deeper than the
`Source Channel` select — it tells you which *query string* produced the
good leads, not just which platform.

---

## Writing a line

Never hand-type a sentinel line. Use the CLI (which self-lints before
printing — an invalid block prints nothing and exits non-zero, because a
half-valid block is worse than none, it looks logged):

```bash
python main.py touch-log render --n 2 --dir out --date 2026-07-28 --inbox "Inbox 1" \
    --seq cold --carries second-finding --finding 3 --subject "Quick thing on your checkout page" \
    --thread 18f2a9c4b7e1 --gate "<literal crm-gate send verdict line>" --body-file /tmp/sent.txt

python main.py touch-log offer --type "First Five" --amount 1500 --currency AED \
    --date 2026-07-28 --status Proposed --rung 0

python main.py touch-log source --channel "Google Footprint" \
    --query "Dubai business coach kajabi" --date 2026-07-27
```

`--body-from-gmail <thread-id>` pulls the body straight from the sent
message (direct Gmail API path) instead of a transcription step, when that
transport is reachable from the calling context.

**Log at confirmation time** — in the same step that sets `Touch #` /
`Last Contacted` / `Status` on the Notion page, never batched to end of
day. Batching is exactly what produced the 16% of Wave 1 sends that were
missing from their logs.

---

## Checking a lead's log

```bash
python main.py log-lint <row.json>              # one lead, from a dumped Notion row + body
python main.py log-lint --slug <slug>           # from the repo archive (docs/leads/<slug>/raw.md)
python main.py log-lint --all --manifest <file> # every lead in one pass
```

`log-lint` never talks to Notion itself (same trust model as every other
gate in this repo — Python holds no Notion credentials anywhere). The
calling skill fetches fresh via the Notion MCP and hands this a plain row
dict + page body string: for `--all`, that means assembling a manifest —
a JSON array of `{"row": {...}, "page_body": "..."}` objects, one per
non-Disqualified lead — before invoking the CLI.

**ERROR** (fails closed, non-zero exit):

- A `TOUCH:` line missing a required token for its direction.
- An inbound touch with no `type` and no `auto=true`/`bounce=true`.
- `n` not contiguous from 1, or duplicated, within the non-bounce out
  direction.
- The lead's `Touch #` property doesn't equal the count of `dir=out`
  non-bounce touches (exact-set match, catches both a missing early touch
  and an over-claimed count — same check `crm_gate.check_log_integrity`
  already runs on the legacy format, extended here to the new grammar).
- A `date` in the future, or an inbound `date` earlier than the touch it
  replies to.
- `carries=second-finding` whose `finding=N` isn't a real rank in the
  lead's `Findings Bank`.
- `inbox` not a label registered in `audit/inboxes.py`.
- An unterminated fenced block.
- Any token value not in its enum.

**WARN** (reported, never blocks):

- Empty body on a non-bounce touch.
- An unknown token key (still preserved in the parsed record).
- `Last Reply Type` disagreeing with the most recently logged inbound
  `type`.
- An offer status transition with no earlier `Proposed` line for the same
  `type`.

Every ERROR/WARN condition has a matching test in `tests/test_touchlog.py`.

---

## Legacy format (pre-2026-07-27)

The 122 Wave 1 leads keep their existing page bodies verbatim — they are
NOT rewritten. `parse_body()` is tolerant of the old shape:

```
[2026-07-20] — Touch #1 — Subject: "..." — Sent
[verbatim body]
Reply: [verbatim, or "No reply"]
Next: [date + planned action]
```

Every record `parse_body()` returns carries `format: "v2" | "legacy"`, so
adoption is measurable rather than assumed. A legacy record is a
`dir=out` touch (the old format never machine-typed a reply); a non-"No
reply" `Reply:` line is surfaced as its own synthetic `dir=in` legacy
record with `type=None` — legacy never captured reply type, which is
exactly the gap this grammar closes going forward, not something to
fabricate retroactively. Legacy records are never held to the v2
required-token rules in `log-lint` (that would just re-fail every one of
the 122 leads for a format they predate) but they DO count toward Touch #
reconciliation and out-touch numbering, because a mixed-format thread
(some legacy sends, then a v2 send after this lands) is the normal case
between now and cutover, not an edge case.

Mixed formats are fine. The parser handles both; the `format` field tells
you which is which.
