# Project Journal — cross-session memory

The narrative git history and Notion don't capture: **what happened each
session** (pipeline ops AND dev), the decisions behind it, gotchas learned, and
open follow-ups. Notion holds live *state* (where each lead is); git holds *code
changes*; this file is the thread that ties sessions together so a fresh session
isn't starting cold.

**How it's used:** the `SessionStart` hook (`.claude/hooks/session_memory.py`)
injects the most recent entries here + the last few commits at the top of every
session, so context loads automatically — no fetch, no prompting.

**How to write it:** at the end of a session with anything worth remembering,
add a new `## ` block at the TOP (newest first), then commit + push. A
journal-only commit is fine on an ops-only session — the point is that it
survives the ephemeral container. Keep entries short and scannable: a few
bullets, then an `### Open follow-ups` list if any are outstanding.

Entry template:

```
## YYYY-MM-DD — <one-line title>
- what happened (ops events, sends, sourcing, ticks, or code)
- decisions made and why
- gotchas / things that surprised us
### Open follow-ups
- [ ] the next thing someone should pick up
```

---

## 2026-07-18 — Four bug fixes + cross-session memory setup
- Fixed and merged 4 bugs to `uae-track` (PR #48, squash `9cdc428`):
  mobile-screenshot re-settle, calendar events surviving Gmail/Notion date
  shapes, the noon-Dubai send-day cutoff for openers, and the
  authoritative-skills `SessionStart` hook.
- Added THIS journal + a second `SessionStart` hook that auto-loads recent
  memory (this file's latest entries + `git log`) so new sessions boot with
  context. Decision: keep session memory in git (auto-loads at start, diffable,
  lives with CLAUDE.md) rather than Notion, which stays the source of truth for
  live pipeline *state*, not narrative.
- Gotcha: past noon Dubai, a fresh touch-1 opener now needs
  `--sends-next-day <inbox's scheduled count>` on `crm-gate send`, or it fails
  closed asking for it. `inbox counts` prints `send_day` + an `opener_note`
  when this applies.
### Open follow-ups
- [ ] If phone-readable ops notes become useful, mirror journal entries to a
  Notion page (not needed yet).
