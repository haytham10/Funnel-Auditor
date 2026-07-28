# UAE Lead CRM — schema delta for the Notion → Airtable migration

Every property below is **additive** to the UAE Lead CRM
(`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`, database
`5a9fc583160046d1a64c4e65cc804229`) — nothing existing is renamed, retyped,
or deleted, so nothing that reads the CRM today breaks. Added 2026-07-27
alongside `docs/uae-track/log-grammar.md`.

**Status: live in Notion as of 2026-07-27.** All 6 properties below were
added to the live CRM via `notion-update-data-source` (additive `ADD
COLUMN` only, verified against a fresh schema fetch first — none of the 6
names collided with an existing property). The Airtable side is NOT done —
that's the manual checklist at the bottom of this file, and it's the part
that still needs Haytham's hands.

**Why this file exists.** Airtable cannot create or edit select/multi-select
*options* via API — only through the UI. So every literal option string
introduced here has to be typed into Airtable by hand, once, in one
sitting, before the Phase 9 cutover parse runs against them. An option
string that's live in Notion but missing from this list is an option
nobody remembers to create in Airtable, and the cutover parse silently
drops or mis-maps that value. List everything here first; create in
Airtable from this list, not from memory.

Where a field already exists in the target Airtable base
(`appaBExqyEZykb1Qk`), match its existing spelling exactly. Where it
doesn't yet, this file's spelling is canonical going forward.

---

## New properties

| Property | Type | Options | Airtable target |
|---|---|---|---|
| `Gate 0 Failed Floors` | multi-select | `Not UAE-based` · `No funnel or paid offer` · `Inactive 30d` · `Audience below floor` · `Program below AED 5000` | Leads · `Gate 0 Failed Floors` |
| `Gate 1 Failed Reason` | select | `Team gatekeeper` · `Agency-run` · `Assistant-managed` · `Other` | Leads · `Gate 1 Failed Reason` |
| `Disqualification Reason` | select | see taxonomy below (from `docs/leads/_dq-extraction.json`) | Leads · `Disqualification Reason` |
| `Hook Type` | select | `WORK` · `LIFE` · `METRIC` · `No hook found` | Leads · `Hook Type` |
| `Hook Source URL` | url | (free-form, no options) | Leads · `Hook Source URL` |
| `Last Reply Type` | select | `Interested` · `Price question` · `Brush-off` · `Logistics` · `Blunt` · `Decline` | denormalised convenience mirror only — the authoritative per-reply type lives in the `TOUCH:` line's `type=` token (see `log-grammar.md`); never analyse off this property |

### ⚠️ Option-spelling hazard: two DIFFERENT properties, deliberately different wording

`Gate 0 Failed Floors` and `Disqualification Reason` both describe why a
lead died, but they are not the same list and must not be typed
identically in Airtable:

- `Gate 0 Failed Floors` is a **multi-select of literal floor names** —
  exactly the 4 floors in `audit/gates.py` (`Not UAE-based`, `No funnel or
  paid offer`, `Inactive 30d`, `Audience below floor`, `Program below AED
  5000`). A lead can fail
  more than one floor at once, hence multi-select.
- `Disqualification Reason` is a **single-select bucket**, data-derived
  from 246 already-disqualified rows (`docs/leads/_dq-extraction.json`,
  generated 2026-07-25) — its taxonomy is coarser and includes reasons
  that aren't Gate 0 floors at all (`Has team/gatekeeper` is a Gate 1
  fail; `Duplicate/re-sourced by mistake` and `Lane 3 skip` aren't gate
  fails at all).

Do not merge these into one property or reuse one's option strings for the
other — Wave 2 planning already keys off the exact `_dq-extraction.json`
wording for `Disqualification Reason`.

### `Disqualification Reason` taxonomy (from `docs/leads/_dq-extraction.json`, generated 2026-07-25, 246 leads)

| Option | Wave 1 count | Definition |
|---|---|---|
| `Not UAE-based` | 34 | Notes show the lead's real location/market is not UAE (foreign country, offshore checkout, or a stated non-UAE primary market). |
| `No funnel / no paid offer` | 89 | No owned sales page, checkout, or purchasable product was found (link-in-bio, DM-only, directory listing, or booking-call-only). |
| `Inactive 30+ days` | 27 | The lead's channel or funnel shows no recent activity (dormant blog/page, stale posts, outdated copyright year). |
| `Audience below floor` | 25 | Confirmed audience size sits below the 1,500 floor on the platform checked. |
| `Program below AED 5000` | 0 | Added 2026-07-28 with the re-niche. **The option does not exist in Notion yet, on purpose** — Notion creates a select/multi-select option on first write, and rewriting the option list via DDL would have touched all 246 already-disqualified rows for a cosmetic addition. The first real price-floor kill creates it. Write the string EXACTLY as spelled here. Her HIGHEST live program is confirmed below the AED 5,000 floor, so the per-call economics cannot work for her. Zero historical rows carry it — it is forward-looking only, and pre-2026-07-28 rows are NOT backfilled. |
| `Has team/gatekeeper` | 30 | The business is run by a team, partner, co-founder, or agency rather than a true solo operator (Gate 1 fail). |
| `No deliverable email` | 6 | Gates passed but no reachable/deliverable email address could ever be found or verified. |
| `Duplicate/re-sourced by mistake` | 6 | The lead already exists elsewhere in the CRM under a different row/status. |
| `Lane 3 skip` | 7 | Lane assignment killed the lead — pivoted out of coaching, or the funnel isn't an active business, regardless of gate status. |
| `Wrong fit` | 15 | Manual judgement that the lead is outside the track's ICP despite passing some gates. |
| `Manual judgement call by Haytham` | 4 | Haytham personally overrode an automated pass/verdict based on external evidence not captured by the standard gates. |
| `Other` | 1 | Disqualification reason present in Notes but doesn't cleanly map to any bucket above. |

---

## Related, not new: `Lost Reason` scope change

`Lost Reason` (existing 9-option select) keeps its current options — this
is a usage-scope note, not a schema change. It stops being used for
disqualifications the moment `Disqualification Reason` exists (going
forward only); it reverts to meaning "lost after engagement" (a reply
came in, then the thread died). The existing ~50 `Wrong fit` rows already
in `Lost Reason` are **not** migrated or backfilled here — Wave 2 sources
those from `_dq-extraction.json` instead. No Airtable action needed for
this row; it's a behavior note for the skills, not a field.

---

## Explicitly NOT added (by design — see the migration handover)

- No split of `Discovery Anchor` into direction + price — advisory legacy
  data since 2026-07-24, three rows use it, splitting costs more than it
  returns.
- No offer fields on the Lead record — offers are many-per-lead and live
  in the `OFFER:` body lines (`log-grammar.md`), migrating to the Offers
  table, not a Leads column.

---

## Checklist for creating these in Airtable (manual, once, before cutover)

- [ ] `Gate 0 Failed Floors` — multi-select, 4 options above
- [ ] `Gate 1 Failed Reason` — select, 4 options above
- [ ] `Disqualification Reason` — select, 11 options above (exact spelling
      from the taxonomy table)
- [ ] `Hook Type` — select, 4 options above
- [ ] `Hook Source URL` — url, no options
- [ ] `Last Reply Type` — select, 6 options above (matches the `TOUCH:`
      `type=` enum in `log-grammar.md` exactly — keep these two in sync if
      either changes)
