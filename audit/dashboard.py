"""
The command-center dashboard — deterministic assembly + rendering.

The Notion CRM is the source of truth for pipeline state, but it is hard to
read at a glance and it says nothing about the two sending inboxes or their
ceilings. This module builds ONE fused picture — pipeline (Notion) + sending
reality (Gmail, both inboxes) + the deliverability ceilings (send_cap.json) —
and renders it as a single self-contained interactive HTML page for a Claude
Artifact.

## The split (same grain as crm_gate / vision_gate)

Python owns deterministic logic; the skill layer owns MCP fetching. Python
CANNOT reach Notion (no REST token here) or Inbox 1's Gmail (MCP-only), so:

  - `build_skeleton()` fills only the Python-reachable slice — the per-inbox
    ceilings (send_cap), the registry (inboxes), and Inbox 2's exact sent-today
    count (direct Gmail API) — and leaves every Notion-sourced and MCP-only
    field as an explicit `null` placeholder for the `/dashboard` skill to fill.
  - The skill runs the documented Notion SQL (01-crm-operating-spec.md §6) and
    the Gmail MCP queries, merges the results into the snapshot, and calls
    `render_html()`.

The snapshot is a plain JSON dict — one contract, `SNAPSHOT_KEYS` below. The
renderer is defensive: a panel whose data is still `null`/empty renders an
"awaiting data" empty state rather than crashing, so a partial snapshot still
produces a usable page. `validate_snapshot()` guards only the load-bearing
core (the Python-produced keys) so a malformed skeleton fails loudly.

## The page

Triage-first, so the state of the world reads in seconds:

  1. An alert banner (only when hygiene flags exist — alerts never hide).
  2. A summary band: one hero figure ("needs you today") + stat tiles that
     jump to their sections.
  3. Three tabs: TODAY (action queues + inbox meters), CALENDAR (a month grid
     of everything dated — due touches, scheduled sends, ramp-eligibility
     days — click a day for its items), PIPELINE (funnel, price-discovery
     study, weekly scoreboard).

Calendar events are merged by `build_events()`: the skill may supply extra
dated items in `snapshot["calendar"]` (scheduled sends, revival bumps), and
the renderer derives the rest itself from `due_followups`, the discovery
ladder, and each inbox's ramp-eligibility date — so the calendar has content
even before the skill fills anything.

The output is a self-contained fragment (a `<title>`, an inline `<style>`,
the page body, and inline JS — tabs, calendar, hover tooltips) with no
external assets, matching the Artifact CSP. Dates and "today" come from the
snapshot (Dubai day), never the viewer's clock, so the page always shows the
truth as of its own refresh.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta

from audit import inboxes, send_cap

# The Status lifecycle, in funnel order (01-crm-operating-spec.md §3). Defined
# here because the statuses live only in docs/skills (driven via MCP) — the
# render order is a presentation concern this module owns.
STATUS_ORDER = [
    "Sourced", "Qualifying", "Audit Ready", "Draft Ready", "Scheduled",
    "Outreach Sent", "Reply Received", "Price Discovery Sent", "Offer Sent",
    "Call Booked", "Won",
]
TERMINAL_STATUSES = ["Lost", "Dormant", "Disqualified"]

# Discovery Anchor options, in a natural high→low order per track.
ANCHOR_ORDER = [
    "Above 735 AED", "At 735 AED", "Below 735 AED",
    "Above 2575 AED", "At 2575 AED", "Below 2575 AED",
    "Refused to name", "Not asked yet",
]

# Calendar event kinds → fixed categorical slots (validated palette, slots
# 1-4, both modes — see the /dashboard skill). Fixed assignment, never cycled.
EVENT_KINDS = ("touch", "send", "other", "ramp")

# The load-bearing keys build_skeleton() always produces. Panels beyond these
# are skill-filled and may be null; the renderer degrades gracefully.
SNAPSHOT_KEYS = ("generated_at", "generated_day", "inboxes", "cap_total")

# Every panel key the renderer knows how to draw, so the skeleton can seed them
# as null and the skill fills them in place (no key means "awaiting data").
_PANEL_KEYS = (
    "pipeline", "replies", "discovery_ladder", "due_followups",
    "send_queue", "price_discovery", "scoreboard", "hygiene", "calendar",
)

_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}")
# A date can reach build_events() in more than the strict ISO shape: Gmail
# reports scheduled-send dates as YYYY/MM/DD, and a Notion date property comes
# back as {"start": "YYYY-MM-DD"} (or {"date": {"start": ...}}). All of these
# name a real day; only a genuinely unparseable value should be dropped.
_SLASH_DAY = re.compile(r"^(\d{4})/(\d{2})/(\d{2})")


def _normalize_day(value) -> str:
    """Coerce a date-ish value to a leading 'YYYY-MM-DD', or '' if it isn't one.

    Accepts the strict ISO shape, a full ISO datetime (truncated to its day), a
    Gmail-style 'YYYY/MM/DD', and a Notion date object ({"start": ...} or nested
    {"date": {"start": ...}}). Anything else returns '' so build_events drops it
    rather than placing a garbage key on the grid.
    """
    if isinstance(value, dict):
        # Notion date property: {"start": ...} or a wrapping {"date": {...}}.
        inner = value.get("start")
        if inner is None and isinstance(value.get("date"), dict):
            inner = value["date"].get("start")
        return _normalize_day(inner)
    if value is None:
        return ""
    text = str(value).strip()
    if _ISO_DAY.match(text):
        return text[:10]
    m = _SLASH_DAY.match(text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


class DashboardError(ValueError):
    """A snapshot that cannot be rendered (missing load-bearing keys)."""


# ---------------------------------------------------------------------------
# Assembly — the Python-reachable slice
# ---------------------------------------------------------------------------

def _inbox_skeleton(cap_state: send_cap.CapState, ib: inboxes.Inbox, query: str, scheduled_query: str) -> dict:
    """One inbox's meter, with everything Python can settle. The sent-today
    AND sent-scheduled counts are filled here ONLY for the direct-API inbox;
    for a Gmail-MCP inbox both stay null and the skill runs `count_query` plus
    `scheduled_query`."""
    eligible_on = None
    if cap_state.valid and cap_state.next_step and cap_state.set_on:
        eligible_on = str(cap_state.set_on + timedelta(days=send_cap.MIN_DAYS_PER_STEP))
    ramp = {
        "cap": cap_state.cap,
        "valid": cap_state.valid,
        "problem": cap_state.problem,
        "set_on": str(cap_state.set_on) if cap_state.set_on else None,
        "days_at_cap": cap_state.days_at_cap,
        "step_index": cap_state.step_index if cap_state.valid else None,
        "step_of": len(send_cap.RAMP_STEPS),
        "next_step": cap_state.next_step if cap_state.valid else None,
        "eligible_on": eligible_on,  # the day the next ramp step unlocks
        "status_lines": send_cap.status_lines(cap_state),
    }
    meter = {
        "label": ib.label,
        "address": ib.address,
        "send_via": ib.send_via,
        "primary": ib.is_primary,
        "cap": cap_state.cap,
        "ramp": ramp,
        "count_query": query,
        "scheduled_query": scheduled_query,
        "sent_today": None,
        "sent_scheduled": None,  # Gmail-MCP only; skill fills via scheduled_query
        "count_source": None,
    }

    if ib.send_via == "gmail-gethaytham":
        # Direct API — Python can settle both counts exactly, same calls `inbox
        # counts` uses. Fail closed to null (never a fake 0) if creds/network
        # are unavailable, so the meter shows "unknown", not "empty".
        meter["count_source"] = "python"
        try:
            from audit import gmail_gethaytham as gg
            meter["sent_today"] = gg.count_messages(query)
        except Exception as exc:  # noqa: BLE001 — report, never crash the build
            meter["count_error"] = str(exc)
        try:
            from audit import gmail_gethaytham as gg
            meter["sent_scheduled"] = gg.count_messages(scheduled_query)
        except Exception as exc:  # noqa: BLE001 — report, never crash the build
            meter["scheduled_error"] = str(exc)
    else:
        # MCP-only (Gmail connector) — Python can't reach this domain. The skill
        # runs count_query for in:sent and scheduled_query for in:scheduled.
        meter["count_source"] = "gmail-mcp"

    return meter


def build_skeleton(now: datetime | None = None) -> dict:
    """The Python-reachable base snapshot. Notion-sourced and Gmail-MCP fields
    are seeded as null for the /dashboard skill to fill in place."""
    now = now or datetime.now(send_cap.DUBAI_TZ)
    day = now.astimezone(send_cap.DUBAI_TZ).date()
    query = f"in:sent after:{send_cap.dubai_midnight_epoch(day)}"
    scheduled_query = "in:scheduled"

    caps = send_cap.load_all()
    meters = []
    total = 0
    for ib in inboxes.all_inboxes():
        st = caps.get(ib.label) or send_cap.load_cap(ib.label)
        meters.append(_inbox_skeleton(st, ib, query, scheduled_query))
        total += st.cap

    snapshot: dict = {
        "generated_at": now.astimezone(send_cap.DUBAI_TZ).isoformat(timespec="seconds"),
        "generated_day": day.isoformat(),
        "timezone": "Asia/Dubai (UTC+4)",
        "inboxes": meters,
        "cap_total": total,
        "cap_status_lines": send_cap.all_status_lines(),
    }
    for key in _PANEL_KEYS:
        snapshot[key] = None
    return snapshot


def validate_snapshot(snapshot) -> None:
    """Fail loudly if the load-bearing (Python-produced) core is missing or
    malformed. Skill-filled panels are allowed to be null — the renderer draws
    an empty state for those — so they are NOT required here."""
    if not isinstance(snapshot, dict):
        raise DashboardError(f"snapshot must be a JSON object, got {type(snapshot).__name__}")
    missing = [k for k in SNAPSHOT_KEYS if k not in snapshot]
    if missing:
        raise DashboardError(
            f"snapshot is missing required key(s): {', '.join(missing)}. "
            "Build it with `python main.py dashboard skeleton` first, then fill "
            "the panels — do not hand-author the core."
        )
    if not isinstance(snapshot["inboxes"], list) or not snapshot["inboxes"]:
        raise DashboardError("snapshot['inboxes'] must be a non-empty list of inbox meters")
    for i, m in enumerate(snapshot["inboxes"]):
        if not isinstance(m, dict) or "label" not in m or "cap" not in m:
            raise DashboardError(f"inbox meter #{i} must be an object with at least 'label' and 'cap'")


def build_events(snapshot: dict) -> list[dict]:
    """Merge every dated item into one calendar event list, sorted by date.

    Sources, in order:
      - `snapshot["calendar"]` — skill-supplied extras (scheduled sends from
        Gmail, revival bumps, anything the renderer can't see itself).
      - `due_followups` / the discovery ladder — kind "touch".
      - each inbox's ramp `eligible_on` — kind "ramp".

    Every event is {"date": "YYYY-MM-DD", "kind": <EVENT_KINDS>, "label": str}.
    Dates are normalized from the shapes the skill actually supplies (strict
    ISO, a full ISO datetime, Gmail's YYYY/MM/DD, or a Notion date object) via
    `_normalize_day`; only a genuinely unparseable date is dropped (a bad date
    can't be placed on a grid). Unknown kinds fold to "other" rather than
    inventing a color slot.
    """
    events: list[dict] = []

    def add(date, kind, label):
        date = _normalize_day(date)
        if not date or not label:
            return
        events.append({
            "date": date,
            "kind": kind if kind in EVENT_KINDS else "other",
            "label": str(label),
        })

    for ev in snapshot.get("calendar") or []:
        if isinstance(ev, dict):
            add(ev.get("date"), ev.get("kind"), ev.get("label"))

    for fu in snapshot.get("due_followups") or []:
        if isinstance(fu, dict):
            touch = fu.get("touch")
            label = f"{fu.get('name', '?')} · touch {touch}" if touch else f"{fu.get('name', '?')} · follow-up"
            add(fu.get("next_action"), "touch", label)

    ladder = snapshot.get("discovery_ladder") or {}
    for lead in ladder.get("due_question") or []:
        if isinstance(lead, dict):
            add(lead.get("next_action"), "touch", f"{lead.get('name', '?')} · discovery question")

    for m in snapshot.get("inboxes") or []:
        ramp = (m or {}).get("ramp") or {}
        if ramp.get("eligible_on") and ramp.get("next_step"):
            add(ramp["eligible_on"], "ramp",
                f"{m.get('label')} ramp: {ramp.get('cap')}/day held 7 days, {ramp['next_step']}/day eligible")

    events.sort(key=lambda e: e["date"])
    return events


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _pct(part: float, whole: float) -> float:
    if not whole:
        return 0.0
    return max(0.0, min(100.0, 100.0 * part / whole))


def _human_stamp(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso))
    except ValueError:
        return str(iso)
    return f"{dt.strftime('%A')} {dt.day} {dt.strftime('%B')} · {dt.strftime('%H:%M')} Dubai"


def _empty(msg: str) -> str:
    return f'<p class="empty">{_esc(msg)}</p>'


def _await(msg: str = "Awaiting first refresh.") -> str:
    return _empty(msg)


# --- summary band -----------------------------------------------------------

def _meter_usage(m: dict) -> tuple[int | None, int, int]:
    """(used, scheduled, cap) for a meter; used is None when the count is unknown."""
    cap = int(m.get("cap") or 0)
    sent = m.get("sent_today")
    sched = int(m.get("sent_scheduled") or 0)
    if sent is None:
        return None, sched, cap
    return int(sent) + sched, sched, cap


def _summary(snapshot: dict) -> str:
    replies = snapshot.get("replies")
    fus = snapshot.get("due_followups")
    sq = snapshot.get("send_queue")

    def count(x):
        return len(x) if isinstance(x, list) else None

    parts = [count(replies), count(fus), count(sq)]
    hero = sum(p for p in parts if p is not None) if any(p is not None for p in parts) else None

    # Headroom left today, summed across inboxes; partial knowledge is labeled,
    # never silently presented as the whole picture.
    known_room = 0
    unknown = 0
    for m in snapshot.get("inboxes", []):
        used, _, cap = _meter_usage(m)
        if used is None:
            unknown += 1
        else:
            known_room += max(cap - used, 0)
    if unknown == 0:
        room_val, room_sub = str(known_room), "across all inboxes"
    elif unknown < len(snapshot.get("inboxes", [])):
        room_val, room_sub = f"{known_room}+", f"{unknown} inbox count still unknown"
    else:
        room_val, room_sub = "–", "counts not fetched yet"

    def tile(value, label, sub, target):
        v = "–" if value is None else str(value)
        return (f'<button class="tile" data-jump="{_esc(target)}">'
                f'<span class="tile-v">{_esc(v)}</span>'
                f'<span class="tile-l">{_esc(label)}</span>'
                f'<span class="tile-s">{_esc(sub)}</span></button>')

    hero_v = "–" if hero is None else str(hero)
    hero_sub = ("replies + follow-ups + sends ready" if hero is not None
                else "refresh to pull live numbers")
    tiles = (
        tile(count(replies), "Replies waiting", "read these first", "sec-replies")
        + tile(count(fus), "Follow-ups due", "today or overdue", "sec-followups")
        + tile(count(sq), "Ready to send", "gated and queued", "sec-send")
        + tile(room_val, "Room left today", room_sub, "sec-inboxes")
    )
    return (
        '<section class="summary" aria-label="Today at a glance">'
        f'<div class="hero"><span class="hero-v">{_esc(hero_v)}</span>'
        f'<span class="hero-l">need you today</span>'
        f'<span class="hero-s">{_esc(hero_sub)}</span></div>'
        f'<div class="tiles">{tiles}</div></section>'
    )


def _alert_banner(snapshot: dict) -> str:
    alerts = snapshot.get("hygiene")
    if alerts is None:
        return ""
    if not alerts:
        return '<div class="allclear">Hygiene checks: all clear.</div>'
    items = "".join(f"<li>{_esc(a)}</li>" for a in alerts)
    return (f'<div class="banner" role="alert"><strong>{len(alerts)} thing(s) look wrong</strong>'
            f'<ul>{items}</ul></div>')


# --- TODAY tab ---------------------------------------------------------------

def _meter_card(m: dict) -> str:
    label = _esc(m.get("label"))
    used, sched, cap = _meter_usage(m)
    ramp = m.get("ramp") or {}
    primary = ' <span class="mut">· primary</span>' if m.get("primary") else ""

    if used is None:
        note = m.get("count_error") or "sent count not fetched yet"
        num = f'<span class="m-num">–<span class="m-den"> / {cap}</span></span>'
        bar = '<div class="track unknown"><div class="fill" style="width:0"></div></div>'
        state = f'<span class="m-state warn-t">{_esc(note)}</span>'
        sev = ""
    else:
        pct = _pct(used, cap)
        over = used > cap
        sev = "over" if over else ("warn" if pct >= 80 else "ok")
        num = f'<span class="m-num">{used - sched}<span class="m-den"> / {cap}</span></span>'
        bar = (f'<div class="track {sev}"><div class="fill" '
               f'style="width:{pct:.0f}%"></div></div>')
        bits = []
        if over:
            bits.append(f'<strong>over ceiling by {used - cap}</strong>')
        else:
            bits.append(f"{cap - used} left")
        if sched:
            bits.append(f"{sched} scheduled")
        if m.get("scheduled_error"):
            bits.append(f'scheduled count unknown ({m["scheduled_error"]})')
        state = f'<span class="m-state {"crit-t" if over else ""}">{" · ".join(bits)}</span>'

    # The single most useful ramp fact, not the whole block.
    if not ramp.get("valid", True):
        ramp_line = f'failed closed to {cap}/day'
        ramp_cls = "crit-t"
    elif ramp.get("next_step") and ramp.get("eligible_on"):
        ramp_line = f'step {int(ramp.get("step_index", 0)) + 1}/{ramp.get("step_of", 3)} · {ramp["next_step"]}/day unlocks {ramp["eligible_on"]}'
        ramp_cls = ""
    else:
        ramp_line = "top step for this inbox (30 is the hard cap)"
        ramp_cls = ""

    return (
        f'<div class="meter"><div class="m-head"><span class="m-label">{label}{primary}</span>{num}</div>'
        f'<div class="m-addr">{_esc(m.get("address"))}</div>'
        f'{bar}{state}'
        f'<div class="m-ramp {ramp_cls}">{_esc(ramp_line)}</div></div>'
    )


def _list_rows(items, render_row) -> str:
    return '<ul class="rows">' + "".join(render_row(it) for it in items) + "</ul>"


def _today_tab(snapshot: dict) -> str:
    meters = "".join(_meter_card(m) for m in snapshot.get("inboxes", []))
    out = (f'<div class="card" id="sec-inboxes"><h2>Inboxes</h2>'
           f'<div class="meter-grid">{meters}</div></div>')

    replies = snapshot.get("replies")
    if replies is None:
        body = _await()
    elif not replies:
        body = _empty("No replies waiting.")
    else:
        body = _list_rows(replies, lambda r: (
            f'<li><span class="r-main">{_esc(r.get("name"))}</span>'
            f'<span class="r-sub">{_esc(r.get("note") or r.get("status"))}'
            f'{" · last touched " + _esc(r.get("last_contacted")) if r.get("last_contacted") else ""}</span></li>'))
    out += f'<div class="card" id="sec-replies"><h2>Replies waiting</h2>{body}</div>'

    def followup_row(f: dict) -> str:
        inbox_pill = ""
        if f.get("inbox"):
            inbox_pill = f'<span class="pill mut-pill">{_esc(f.get("inbox"))}</span>'
        return (
            f'<li><span class="r-main">{_esc(f.get("name"))}'
            f'<span class="pill">touch {_esc(f.get("touch"))}</span>{inbox_pill}</span>'
            f'<span class="r-sub">carries: {_esc(f.get("carries") or "pick from the findings bank")}'
            f' · due {_esc(f.get("next_action"))}</span></li>')

    fus = snapshot.get("due_followups")
    if fus is None:
        body = _await()
    elif not fus:
        body = _empty("Nothing due today.")
    else:
        body = _list_rows(fus, followup_row)
    out += f'<div class="card" id="sec-followups"><h2>Follow-ups due</h2>{body}</div>'

    sq = snapshot.get("send_queue")
    if sq is None:
        body = _await()
    elif not sq:
        body = _empty("Queue is empty. Do walks before sending.")
    else:
        groups: dict[str, list] = {}
        for it in sq:
            groups.setdefault(it.get("inbox") or "Unassigned", []).append(it)
        body = ""
        for inbox_label in sorted(groups):
            rows = groups[inbox_label]
            body += f'<h3>{_esc(inbox_label)} <span class="mut">· {len(rows)}</span></h3>'
            body += _list_rows(rows, lambda s: (
                f'<li><span class="r-main">{_esc(s.get("name"))}'
                f'<span class="pill">{_esc(s.get("status"))}</span></span>'
                f'<span class="r-sub">finding {_esc(s.get("finding_verified"))}'
                f' · email {_esc(s.get("email_verified"))}</span></li>'))
    out += f'<div class="card" id="sec-send"><h2>Ready to send</h2>{body}</div>'

    lad = snapshot.get("discovery_ladder")
    if lad is None:
        body = _await()
    else:
        due = lad.get("due_question") or []
        unlocked = lad.get("offer_unlocked") or []
        body = "<h3>Owed the price question</h3>"
        body += _list_rows(due, lambda d: (
            f'<li><span class="r-main">{_esc(d.get("name"))}</span>'
            f'<span class="r-sub">{_esc(d.get("status"))} · due {_esc(d.get("next_action"))}</span></li>'
        )) if due else _empty("Nobody owed the question right now.")
        body += "<h3>Answered · offer unlocked</h3>"
        body += _list_rows(unlocked, lambda u: (
            f'<li><span class="r-main">{_esc(u.get("name"))}'
            f'<span class="pill">{_esc(u.get("anchor"))}</span></span>'
            f'<span class="r-sub">“{_esc(u.get("answer"))}”</span></li>'
        )) if unlocked else _empty("No answers logged yet.")
    out += f'<div class="card" id="sec-discovery"><h2>Discovery ladder</h2>{body}</div>'

    return out


# --- CALENDAR tab -------------------------------------------------------------

def _calendar_tab() -> str:
    """Static shell only — the grid is built client-side from the embedded
    events JSON, so month navigation works without re-rendering."""
    legend = "".join(
        f'<span class="lg"><span class="dot k-{k}"></span>{name}</span>'
        for k, name in (("touch", "Touch due"), ("send", "Send scheduled"),
                        ("ramp", "Ramp step unlocks"), ("other", "Other"))
    )
    return (
        '<div class="card" id="sec-calendar"><div class="cal-head">'
        '<h2 id="cal-title">Calendar</h2>'
        '<div class="cal-nav">'
        '<button id="cal-prev" aria-label="Previous month">‹</button>'
        '<button id="cal-today">Today</button>'
        '<button id="cal-next" aria-label="Next month">›</button></div></div>'
        f'<div class="cal-legend">{legend}</div>'
        '<div class="cal-grid" id="cal-grid" role="grid"></div>'
        '<div class="cal-detail"><h3 id="cal-detail-title">Selected day</h3>'
        '<ul class="rows" id="cal-detail-list"></ul></div></div>'
    )


# --- PIPELINE tab --------------------------------------------------------------

def _funnel(snapshot: dict) -> str:
    pipe = snapshot.get("pipeline")
    if not pipe or not pipe.get("by_status"):
        return f'<div class="card"><h2>Pipeline</h2>{_await("Awaiting CRM counts.")}</div>'
    by_status = pipe["by_status"]
    active = [(s, int(by_status.get(s, 0))) for s in STATUS_ORDER]
    terminal = [(s, int(by_status.get(s, 0))) for s in TERMINAL_STATUSES]
    known = set(STATUS_ORDER) | set(TERMINAL_STATUSES)
    extra = [(s, int(n)) for s, n in by_status.items() if s not in known]
    peak = max([n for _, n in active + terminal + extra] + [1])
    total_active = sum(n for _, n in active)

    def row(label, n, klass):
        share = _pct(n, total_active) if total_active else 0
        tip = f"{label}: {n} lead(s)" + (f" · {share:.0f}% of active" if klass == "flow" else "")
        return (f'<div class="f-row" tabindex="0" data-tip="{_esc(tip)}" aria-label="{_esc(tip)}">'
                f'<span class="f-label">{_esc(label)}</span>'
                f'<div class="f-track"><div class="f-fill {klass}" style="width:{_pct(n, peak):.1f}%"></div></div>'
                f'<span class="f-val">{n}</span></div>')

    body = "".join(row(s, n, "flow") for s, n in active)
    body += '<div class="f-sep">off-ramps</div>'
    body += "".join(row(s, n, "gone") for s, n in terminal)
    body += "".join(row(s, n, "gone") for s, n in extra)
    body += f'<p class="foot">{total_active} leads in play · hover a stage for its share.</p>'
    return f'<div class="card"><h2>Pipeline</h2>{body}</div>'


def _price_discovery(snapshot: dict) -> str:
    pd = snapshot.get("price_discovery")
    if not pd:
        return f'<div class="card"><h2>Price discovery</h2>{_await("Awaiting the study query.")}</div>'
    anchors = pd.get("anchors") or {}
    est = pd.get("est_value") or {}
    peak = max([int(v) for v in anchors.values()] + [1])

    body = "<h3>Where they anchored</h3>"
    if anchors:
        for a in ANCHOR_ORDER:
            if a not in anchors:
                continue
            n = int(anchors[a])
            # Ordinal teal ramp: Above (dark) → At (mid) → Below (light);
            # non-answers recede to gray. Identity also carried by the row label.
            if a.startswith("Above"):
                step = "a-hi"
            elif a.startswith("At"):
                step = "a-mid"
            elif a.startswith("Below"):
                step = "a-lo"
            else:
                step = "gone"
            tip = f"{a}: {n} lead(s)"
            body += (f'<div class="f-row" tabindex="0" data-tip="{_esc(tip)}" aria-label="{_esc(tip)}">'
                     f'<span class="f-label">{_esc(a)}</span>'
                     f'<div class="f-track"><div class="f-fill {step}" style="width:{_pct(n, peak):.1f}%"></div></div>'
                     f'<span class="f-val">{n}</span></div>')
    else:
        body += _empty("No anchors recorded yet.")

    if est:
        body += '<h3>Track split</h3><div class="chips">'
        for k, v in est.items():
            body += f'<span class="chip">{_esc(k)} <b>{_esc(v)}</b></span>'
        body += "</div>"
    return f'<div class="card"><h2>Price discovery</h2>{body}</div>'


def _scoreboard(snapshot: dict) -> str:
    sb = snapshot.get("scoreboard")
    if not sb:
        return f'<div class="card"><h2>This week</h2>{_await("Awaiting weekly aggregates.")}</div>'
    tiles = "".join(
        f'<div class="sb"><span class="sb-v">{_esc(v)}</span><span class="sb-l">{_esc(k)}</span></div>'
        for k, v in sb.items()
    )
    return f'<div class="card"><h2>This week</h2><div class="sb-grid">{tiles}</div></div>'


# --- style + script ------------------------------------------------------------

_STYLE = """
<style>
:root{
  color-scheme:light;
  --page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--mut:#898781;
  --hair:#e1e0d9;--ring:rgba(11,11,11,.10);
  --accent:#0c877c;--accent-track:#d9ece9;--accent-hi:#0a6e65;--accent-lo:#7fbfb8;
  --good:#006300;--warn:#fab219;--warn-track:#f7e8c4;--crit:#d03b3b;--crit-track:#f4dcdc;
  --cat1:#2a78d6;--cat2:#008300;--cat3:#e87ba4;--cat4:#eda100;
  --gone:#c3c2b7;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root:where(:not([data-theme="light"])){
    color-scheme:dark;
    --page:#0d0d0d;--surface:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;--mut:#898781;
    --hair:#2c2c2a;--ring:rgba(255,255,255,.10);
    --accent:#2cb6a5;--accent-track:#12332f;--accent-hi:#6fded0;--accent-lo:#1e7f73;
    --good:#0ca30c;--warn:#fab219;--warn-track:#3a2f10;--crit:#d03b3b;--crit-track:#3a1717;
    --cat1:#3987e5;--cat2:#008300;--cat3:#d55181;--cat4:#c98500;
    --gone:#52514e;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#0d0d0d;--surface:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;--mut:#898781;
  --hair:#2c2c2a;--ring:rgba(255,255,255,.10);
  --accent:#2cb6a5;--accent-track:#12332f;--accent-hi:#6fded0;--accent-lo:#1e7f73;
  --good:#0ca30c;--warn:#fab219;--warn-track:#3a2f10;--crit:#d03b3b;--crit-track:#3a1717;
  --cat1:#3987e5;--cat2:#008300;--cat3:#d55181;--cat4:#c98500;
  --gone:#52514e;
}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:14px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
button{font:inherit;color:inherit;background:none;border:none;padding:0;cursor:pointer}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
.wrap{max-width:1080px;margin:0 auto;padding:clamp(16px,3vw,36px) clamp(12px,3vw,28px) 72px}

header{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:18px;flex-wrap:wrap}
.eyebrow{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:0 0 4px}
h1{font-size:clamp(20px,3vw,26px);margin:0;letter-spacing:-.01em}
.stamp{color:var(--ink2);font-size:13px;margin-top:2px}
#themeBtn{font-size:12px;padding:5px 12px;border-radius:8px;border:1px solid var(--hair);background:var(--surface);color:var(--ink2)}

.banner{background:var(--crit-track);border:1px solid var(--crit);border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:13.5px}
.banner strong{color:var(--crit)}
.banner ul{margin:6px 0 0;padding-left:18px}
.banner li{margin:2px 0}
.allclear{color:var(--good);font-size:13px;margin-bottom:14px}

.summary{display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:stretch;margin-bottom:20px}
@media (max-width:680px){.summary{grid-template-columns:1fr}}
.hero{background:var(--surface);border:1px solid var(--hair);border-radius:14px;padding:18px 26px;display:flex;flex-direction:column;justify-content:center;min-width:190px}
.hero-v{font-size:52px;font-weight:650;line-height:1.05;letter-spacing:-.02em}
.hero-l{font-size:14px;color:var(--ink2);margin-top:2px}
.hero-s{font-size:12px;color:var(--mut);margin-top:6px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.tile{background:var(--surface);border:1px solid var(--hair);border-radius:12px;padding:12px 14px;text-align:left;display:flex;flex-direction:column;gap:1px;transition:border-color .12s}
.tile:hover{border-color:var(--accent)}
.tile-v{font-size:24px;font-weight:650}
.tile-l{font-size:12.5px;color:var(--ink2)}
.tile-s{font-size:11px;color:var(--mut)}

.tabs{display:flex;gap:4px;border-bottom:1px solid var(--hair);margin-bottom:16px}
.tab{padding:9px 16px;font-size:13.5px;color:var(--ink2);border-bottom:2px solid transparent;margin-bottom:-1px}
.tab[aria-selected="true"]{color:var(--ink);font-weight:600;border-bottom-color:var(--accent)}
.tab:hover{color:var(--ink)}
[role="tabpanel"][hidden]{display:none}

.card{background:var(--surface);border:1px solid var(--hair);border-radius:14px;padding:16px 18px;margin-bottom:14px}
.card h2{margin:0 0 12px;font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--ink2);font-weight:650}
.card h3{margin:14px 0 6px;font-size:12px;color:var(--mut);font-weight:600}
.card h3:first-of-type{margin-top:0}
.foot{font-size:12px;color:var(--mut);margin:10px 0 0}
.mut{color:var(--mut);font-weight:400}
.empty{color:var(--mut);font-size:13px;font-style:italic;margin:2px 0}

.meter-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.meter{border:1px solid var(--hair);border-radius:12px;padding:12px 14px}
.m-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.m-label{font-weight:650;font-size:13.5px}
.m-num{font-size:22px;font-weight:650}
.m-den{font-size:13px;color:var(--mut);font-weight:400}
.m-addr{font-size:11.5px;color:var(--mut);margin:1px 0 9px;word-break:break-all}
.track{height:8px;border-radius:5px;overflow:hidden;background:var(--accent-track)}
.track .fill{height:100%;border-radius:0 4px 4px 0;background:var(--accent)}
.track.warn{background:var(--warn-track)}.track.warn .fill{background:var(--warn)}
.track.over{background:var(--crit-track)}.track.over .fill{background:var(--crit)}
.track.unknown{background:repeating-linear-gradient(45deg,var(--hair),var(--hair) 6px,var(--page) 6px,var(--page) 12px)}
.m-state{display:block;font-size:12px;color:var(--ink2);margin-top:6px}
.warn-t{color:var(--warn)}.crit-t{color:var(--crit);font-weight:600}
.m-ramp{font-size:11.5px;color:var(--mut);margin-top:8px;padding-top:8px;border-top:1px dashed var(--hair)}

.rows{list-style:none;margin:0;padding:0}
.rows li{padding:9px 2px;border-bottom:1px solid var(--hair);display:flex;flex-direction:column;gap:1px}
.rows li:last-child{border-bottom:none}
.r-main{font-weight:600;font-size:13.5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.r-sub{font-size:12.5px;color:var(--ink2)}
.pill{font-size:11px;font-weight:600;padding:1px 8px;border-radius:20px;background:var(--accent-track);color:var(--accent);white-space:nowrap}
.mut-pill{background:transparent;border:1px solid var(--hair);color:var(--mut)}

.f-row{display:grid;grid-template-columns:minmax(110px,160px) 1fr 40px;align-items:center;gap:10px;padding:3px 0;border-radius:6px}
.f-row:hover .f-fill{filter:brightness(1.12)}
.f-label{font-size:12.5px;color:var(--ink2)}
.f-track{height:18px;background:transparent}
.f-fill{height:100%;border-radius:0 4px 4px 0;min-width:1px}
.f-fill.flow{background:var(--accent)}
.f-fill.gone{background:var(--gone)}
.f-fill.a-hi{background:var(--accent-hi)}
.f-fill.a-mid{background:var(--accent)}
.f-fill.a-lo{background:var(--accent-lo)}
.f-val{font-size:13px;font-weight:600;text-align:right;font-variant-numeric:tabular-nums}
.f-sep{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--mut);margin:10px 0 4px}

.cal-head{display:flex;align-items:center;justify-content:space-between;gap:10px}
.cal-head h2{margin:0}
.cal-nav{display:flex;gap:6px}
.cal-nav button{border:1px solid var(--hair);border-radius:8px;padding:4px 12px;font-size:13px;color:var(--ink2);background:var(--surface)}
.cal-nav button:hover{border-color:var(--accent);color:var(--ink)}
.cal-legend{display:flex;flex-wrap:wrap;gap:14px;margin:10px 0 12px;font-size:12px;color:var(--ink2)}
.lg{display:inline-flex;align-items:center;gap:6px}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;box-shadow:0 0 0 2px var(--surface)}
.k-touch{background:var(--cat1)}.k-send{background:var(--cat2)}.k-other{background:var(--cat3)}.k-ramp{background:var(--cat4)}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}
.cal-dow{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);text-align:center;padding:4px 0}
.cal-day{min-height:58px;border:1px solid var(--hair);border-radius:9px;padding:5px 6px;display:flex;flex-direction:column;gap:4px;align-items:flex-start;background:var(--surface);transition:border-color .12s}
.cal-day:hover{border-color:var(--accent)}
.cal-day.blank{border-color:transparent;background:transparent;pointer-events:none}
.cal-day.today{border-color:var(--accent);border-width:2px;padding:4px 5px}
.cal-day.sel{background:var(--accent-track)}
.cal-num{font-size:12px;font-weight:600;color:var(--ink2)}
.cal-day.today .cal-num{color:var(--accent)}
.cal-dots{display:flex;gap:3px;align-items:center;flex-wrap:wrap}
.cal-more{font-size:10px;color:var(--mut)}
.cal-detail{margin-top:14px;border-top:1px solid var(--hair);padding-top:10px}
@media (max-width:560px){.cal-day{min-height:44px}}

.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{font-size:12.5px;padding:4px 11px;border-radius:20px;border:1px solid var(--hair)}
.sb-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}
.sb{border:1px solid var(--hair);border-radius:12px;padding:12px;text-align:center}
.sb-v{display:block;font-size:26px;font-weight:650}
.sb-l{display:block;font-size:11.5px;color:var(--mut);margin-top:2px}

#tip{position:fixed;z-index:10;pointer-events:none;background:var(--ink);color:var(--page);font-size:12px;padding:5px 9px;border-radius:7px;max-width:260px;display:none}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
"""

_SCRIPT = """
<script>
(function(){
  "use strict";
  var payload = JSON.parse(document.getElementById("dash-data").textContent);
  var EVENTS = payload.events || [];
  var TODAY = payload.today || "";

  /* theme toggle — the stamp must beat the OS preference both ways */
  var tb = document.getElementById("themeBtn");
  if (tb) tb.addEventListener("click", function () {
    var r = document.documentElement, cur = r.getAttribute("data-theme");
    if (!cur) cur = (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
    r.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
  });

  /* tabs */
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
  function selectTab(id){
    tabs.forEach(function(t){
      var on = t.dataset.tab === id;
      t.setAttribute("aria-selected", on ? "true" : "false");
      document.getElementById("panel-" + t.dataset.tab).hidden = !on;
    });
  }
  tabs.forEach(function(t){ t.addEventListener("click", function(){ selectTab(t.dataset.tab); }); });

  /* summary tiles jump to their section on the Today tab */
  Array.prototype.forEach.call(document.querySelectorAll(".tile[data-jump]"), function(tile){
    tile.addEventListener("click", function(){
      selectTab("today");
      var el = document.getElementById(tile.dataset.jump);
      if (el) el.scrollIntoView({behavior:"smooth", block:"start"});
    });
  });

  /* hover/focus tooltip for bar rows (values are also visible inline) */
  var tip = document.createElement("div");
  tip.id = "tip";
  document.body.appendChild(tip);
  function showTip(text, x, y){
    tip.textContent = text;
    tip.style.display = "block";
    var pad = 12, w = tip.offsetWidth;
    tip.style.left = Math.min(x + pad, window.innerWidth - w - pad) + "px";
    tip.style.top = (y + pad) + "px";
  }
  document.addEventListener("pointermove", function(e){
    var row = e.target.closest ? e.target.closest("[data-tip]") : null;
    if (row) showTip(row.dataset.tip, e.clientX, e.clientY);
    else tip.style.display = "none";
  });
  document.addEventListener("focusin", function(e){
    var row = e.target.closest ? e.target.closest("[data-tip]") : null;
    if (row){ var r = row.getBoundingClientRect(); showTip(row.dataset.tip, r.left, r.bottom); }
  });
  document.addEventListener("focusout", function(){ tip.style.display = "none"; });

  /* calendar — month grid built from EVENTS; "today" is the snapshot's Dubai
     day, never the viewer's clock, so the page shows its own refresh truth */
  var byDay = {};
  EVENTS.forEach(function(ev){ (byDay[ev.date] = byDay[ev.date] || []).push(ev); });
  var MONTHS = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"];
  var DOWS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  var base = TODAY ? TODAY.split("-").map(Number) : [2026, 1, 1];
  var view = { y: base[0], m: base[1] - 1 };
  var selected = TODAY;

  function iso(y, m, d){
    return y + "-" + String(m + 1).padStart(2, "0") + "-" + String(d).padStart(2, "0");
  }
  function renderDetail(){
    var list = document.getElementById("cal-detail-list");
    var title = document.getElementById("cal-detail-title");
    while (list.firstChild) list.removeChild(list.firstChild);
    title.textContent = selected + (selected === TODAY ? " (today)" : "");
    var evs = byDay[selected] || [];
    if (!evs.length){
      var li = document.createElement("li");
      li.className = "empty";
      li.textContent = "Nothing on this day.";
      list.appendChild(li);
      return;
    }
    evs.forEach(function(ev){
      var li = document.createElement("li");
      var main = document.createElement("span");
      main.className = "r-main";
      var dot = document.createElement("span");
      dot.className = "dot k-" + ev.kind;
      main.appendChild(dot);
      main.appendChild(document.createTextNode(ev.label));  /* untrusted → text node */
      li.appendChild(main);
      list.appendChild(li);
    });
  }
  function renderGrid(){
    var grid = document.getElementById("cal-grid");
    while (grid.firstChild) grid.removeChild(grid.firstChild);
    document.getElementById("cal-title").textContent = MONTHS[view.m] + " " + view.y;
    DOWS.forEach(function(d){
      var h = document.createElement("div");
      h.className = "cal-dow"; h.textContent = d;
      grid.appendChild(h);
    });
    var first = new Date(view.y, view.m, 1);
    var lead = (first.getDay() + 6) % 7;               /* Monday-start week */
    var days = new Date(view.y, view.m + 1, 0).getDate();
    for (var i = 0; i < lead; i++){
      var b = document.createElement("div");
      b.className = "cal-day blank";
      grid.appendChild(b);
    }
    for (var d = 1; d <= days; d++){
      (function(d){
        var key = iso(view.y, view.m, d);
        var cell = document.createElement("button");
        cell.className = "cal-day" + (key === TODAY ? " today" : "") + (key === selected ? " sel" : "");
        cell.setAttribute("aria-label", key);
        var num = document.createElement("span");
        num.className = "cal-num"; num.textContent = d;
        cell.appendChild(num);
        var evs = byDay[key] || [];
        if (evs.length){
          var dots = document.createElement("span");
          dots.className = "cal-dots";
          evs.slice(0, 3).forEach(function(ev){
            var dot = document.createElement("span");
            dot.className = "dot k-" + ev.kind;
            dots.appendChild(dot);
          });
          if (evs.length > 3){
            var more = document.createElement("span");
            more.className = "cal-more"; more.textContent = "+" + (evs.length - 3);
            dots.appendChild(more);
          }
          cell.appendChild(dots);
        }
        cell.addEventListener("click", function(){ selected = key; renderGrid(); renderDetail(); });
        grid.appendChild(cell);
      })(d);
    }
  }
  var prev = document.getElementById("cal-prev"), next = document.getElementById("cal-next"),
      home = document.getElementById("cal-today");
  if (prev) prev.addEventListener("click", function(){ view.m--; if (view.m < 0){ view.m = 11; view.y--; } renderGrid(); });
  if (next) next.addEventListener("click", function(){ view.m++; if (view.m > 11){ view.m = 0; view.y++; } renderGrid(); });
  if (home) home.addEventListener("click", function(){ view = { y: base[0], m: base[1] - 1 }; selected = TODAY; renderGrid(); renderDetail(); });
  if (document.getElementById("cal-grid")){ renderGrid(); renderDetail(); }
})();
</script>
"""


def render_html(snapshot: dict, title: str = "Funnel Auditor — Command Center") -> str:
    """Render the full self-contained dashboard fragment from a snapshot.

    Validates the load-bearing core first (so a broken skeleton fails loudly),
    then draws the summary band, the three tabs, and the calendar data — each
    panel degrading to an empty state when its skill-filled data is still null.
    No external assets: Artifact-ready and browser-openable.
    """
    validate_snapshot(snapshot)

    header = (
        '<header><div>'
        '<p class="eyebrow">UAE lead pipeline · snapshot</p>'
        f'<h1>{_esc(title)}</h1>'
        f'<div class="stamp">As of {_esc(_human_stamp(snapshot.get("generated_at")))}</div>'
        '</div><button id="themeBtn">◐ Theme</button></header>'
    )

    tabs = (
        '<div class="tabs" role="tablist">'
        '<button class="tab" role="tab" data-tab="today" aria-selected="true">Today</button>'
        '<button class="tab" role="tab" data-tab="calendar" aria-selected="false">Calendar</button>'
        '<button class="tab" role="tab" data-tab="pipeline" aria-selected="false">Pipeline</button>'
        '</div>'
    )
    panels = (
        f'<div id="panel-today" role="tabpanel">{_today_tab(snapshot)}</div>'
        f'<div id="panel-calendar" role="tabpanel" hidden>{_calendar_tab()}</div>'
        f'<div id="panel-pipeline" role="tabpanel" hidden>'
        f'{_funnel(snapshot)}{_price_discovery(snapshot)}{_scoreboard(snapshot)}</div>'
    )

    # Embedded data for the client-side calendar. The "<" escape prevents a
    # label containing "</script>" from terminating the data block early.
    payload = {"today": snapshot.get("generated_day"), "events": build_events(snapshot)}
    data_json = json.dumps(payload).replace("<", "\\u003c")
    data_tag = f'<script type="application/json" id="dash-data">{data_json}</script>'

    return (
        f"<title>{_esc(title)}</title>\n{_STYLE}\n"
        f'<div class="wrap">{header}{_alert_banner(snapshot)}{_summary(snapshot)}{tabs}{panels}</div>\n'
        f"{data_tag}\n{_SCRIPT}"
    )
