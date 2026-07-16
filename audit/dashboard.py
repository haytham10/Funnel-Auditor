"""
The command-center dashboard — deterministic assembly + rendering.

The Notion CRM is the source of truth for pipeline state, but it is hard to
read at a glance and it says nothing about the two sending inboxes or their
ceilings. This module builds ONE fused picture — pipeline (Notion) + sending
reality (Gmail, both inboxes) + the deliverability ceilings (send_cap.json) —
and renders it as a single self-contained HTML page for a Claude Artifact.

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

The output is a self-contained fragment (a `<title>`, an inline `<style>`, and
the page body) — no external assets, matching the Artifact CSP and the existing
`docs/uae-track/pipeline.html` precedent. It works both as an Artifact file and
opened directly in a browser.
"""

from __future__ import annotations

import html
from datetime import datetime

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

# The load-bearing keys build_skeleton() always produces. Panels beyond these
# are skill-filled and may be null; the renderer degrades gracefully.
SNAPSHOT_KEYS = ("generated_at", "generated_day", "inboxes", "cap_total")

# Every panel key the renderer knows how to draw, so the skeleton can seed them
# as null and the skill fills them in place (no key means "awaiting data").
_PANEL_KEYS = (
    "pipeline", "replies", "discovery_ladder", "due_followups",
    "send_queue", "price_discovery", "scoreboard", "hygiene",
)


class DashboardError(ValueError):
    """A snapshot that cannot be rendered (missing load-bearing keys)."""


# ---------------------------------------------------------------------------
# Assembly — the Python-reachable slice
# ---------------------------------------------------------------------------

def _inbox_skeleton(cap_state: send_cap.CapState, ib: inboxes.Inbox, query: str) -> dict:
    """One inbox's meter, with everything Python can settle. The sent-today
    count is filled here ONLY for the direct-API inbox; for a Gmail-MCP inbox
    it stays null and the skill runs `count_query` (plus `in:scheduled`)."""
    ramp = {
        "cap": cap_state.cap,
        "valid": cap_state.valid,
        "problem": cap_state.problem,
        "set_on": str(cap_state.set_on) if cap_state.set_on else None,
        "days_at_cap": cap_state.days_at_cap,
        "step_index": cap_state.step_index if cap_state.valid else None,
        "step_of": len(send_cap.RAMP_STEPS),
        "next_step": cap_state.next_step if cap_state.valid else None,
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
        "sent_today": None,
        "sent_scheduled": None,  # Gmail-MCP only; skill fills in:scheduled due today
        "count_source": None,
    }

    if ib.send_via == "gmail-gethaytham":
        # Direct API — Python can settle this one exactly, same call `inbox
        # counts` uses. Fail closed to null (never a fake 0) if creds/network
        # are unavailable, so the meter shows "unknown", not "empty".
        meter["count_source"] = "python"
        try:
            from audit import gmail_gethaytham as gg
            meter["sent_today"] = gg.count_messages(query)
        except Exception as exc:  # noqa: BLE001 — report, never crash the build
            meter["count_error"] = str(exc)
    else:
        # MCP-only (Gmail connector) — Python can't reach this domain. The skill
        # runs count_query for in:sent and adds in:scheduled due today.
        meter["count_source"] = "gmail-mcp"

    return meter


def build_skeleton(now: datetime | None = None) -> dict:
    """The Python-reachable base snapshot. Notion-sourced and Gmail-MCP fields
    are seeded as null for the /dashboard skill to fill in place."""
    now = now or datetime.now(send_cap.DUBAI_TZ)
    day = now.astimezone(send_cap.DUBAI_TZ).date()
    query = f"in:sent after:{send_cap.dubai_midnight_epoch(day)}"

    caps = send_cap.load_all()
    meters = []
    total = 0
    for ib in inboxes.all_inboxes():
        st = caps.get(ib.label) or send_cap.load_cap(ib.label)
        meters.append(_inbox_skeleton(st, ib, query))
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


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _pct(part: float, whole: float) -> float:
    if not whole:
        return 0.0
    return max(0.0, min(100.0, 100.0 * part / whole))


def _empty(msg: str) -> str:
    return f'<p class="empty">{_esc(msg)}</p>'


def _meter_card(m: dict) -> str:
    label = _esc(m.get("label"))
    address = _esc(m.get("address"))
    cap = m.get("cap") or 0
    sent = m.get("sent_today")
    sched = m.get("sent_scheduled") or 0
    ramp = m.get("ramp") or {}
    primary = " · primary" if m.get("primary") else ""

    if sent is None:
        # Unknown (MCP inbox not yet filled, or a direct-API read failed).
        note = m.get("count_error") or (
            "run the count query via Gmail MCP" if m.get("count_source") == "gmail-mcp"
            else "count unavailable"
        )
        head = f'<span class="meter-num">?<span class="meter-den">/{_esc(cap)}</span></span>'
        bar = '<div class="bar"><div class="bar-fill unknown" style="width:100%"></div></div>'
        sub = f'<span class="warn">sent today unknown — {_esc(note)}</span>'
    else:
        used = sent + sched
        headroom = max(cap - used, 0)
        pct = _pct(used, cap)
        over = used > cap
        sched_str = f" (+{sched} scheduled)" if sched else ""
        head = (f'<span class="meter-num">{_esc(sent)}'
                f'<span class="meter-den">/{_esc(cap)}</span></span>')
        klass = "over" if over else ("high" if pct >= 80 else "ok")
        bar = (f'<div class="bar"><div class="bar-fill {klass}" '
               f'style="width:{pct:.0f}%"></div></div>')
        if over:
            sub = f'<span class="warn">OVER CEILING by {used - cap}{_esc(sched_str)}</span>'
        else:
            sub = f'<span class="muted">{headroom} left today{_esc(sched_str)}</span>'

    # Ramp line: the most informative status line (the reminder if present).
    lines = ramp.get("status_lines") or []
    ramp_line = lines[-1] if len(lines) > 1 else (lines[0] if lines else "")
    valid = ramp.get("valid", True)
    ramp_html = f'<div class="ramp {"bad" if not valid else ""}">{_esc(ramp_line)}</div>'

    return (
        f'<div class="meter">'
        f'<div class="meter-head"><span class="meter-label">{label}<span class="muted">{_esc(primary)}</span></span>{head}</div>'
        f'<div class="meter-addr muted">{address} · {_esc(m.get("send_via"))}</div>'
        f'{bar}<div class="meter-sub">{sub}</div>{ramp_html}'
        f'</div>'
    )


def _meters(snapshot: dict) -> str:
    cards = "".join(_meter_card(m) for m in snapshot.get("inboxes", []))
    total = snapshot.get("cap_total")
    foot = (f'<div class="panel-foot muted">Total system ceiling: {_esc(total)}/day '
            f'across {len(snapshot.get("inboxes", []))} inbox(es) — independent ramps, '
            f'additive capacity.</div>')
    return _panel("Sending inboxes", f'<div class="meter-grid">{cards}</div>{foot}')


def _pipeline(snapshot: dict) -> str:
    pipe = snapshot.get("pipeline")
    if not pipe or not pipe.get("by_status"):
        return _panel("Pipeline", _empty("Awaiting Notion pipeline counts."))
    by_status = pipe["by_status"]
    active = [(s, int(by_status.get(s, 0))) for s in STATUS_ORDER]
    terminal = [(s, int(by_status.get(s, 0))) for s in TERMINAL_STATUSES]
    # Any status the CRM returned that we don't know about — surface it, don't drop.
    known = set(STATUS_ORDER) | set(TERMINAL_STATUSES)
    extra = [(s, int(n)) for s, n in by_status.items() if s not in known]
    peak = max([n for _, n in active + terminal + extra] + [1])

    def row(label, n, klass):
        return (f'<div class="frow"><span class="flabel">{_esc(label)}</span>'
                f'<div class="fbar"><div class="fbar-fill {klass}" style="width:{_pct(n, peak):.0f}%"></div></div>'
                f'<span class="fnum">{_esc(n)}</span></div>')

    body = "".join(row(s, n, "flow") for s, n in active)
    body += '<div class="frow-sep">off-ramps</div>'
    body += "".join(row(s, n, "kill") for s, n in terminal)
    if extra:
        body += "".join(row(s, n, "other") for s, n in extra)
    total_active = sum(n for _, n in active)
    foot = f'<div class="panel-foot muted">{total_active} leads in the active funnel.</div>'
    return _panel("Pipeline", body + foot)


def _table(items, columns) -> str:
    """Generic table. `columns` is a list of (header, key) pairs."""
    head = "".join(f"<th>{_esc(h)}</th>" for h, _ in columns)
    rows = ""
    for it in items:
        cells = "".join(f"<td>{_esc(it.get(k))}</td>" for _, k in columns)
        rows += f"<tr>{cells}</tr>"
    return f'<div class="twrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def _replies(snapshot: dict) -> str:
    replies = snapshot.get("replies")
    if replies is None:
        return _panel("Replies &amp; needs attention", _empty("Awaiting the Gmail reply sweep."), badge="!")
    if not replies:
        return _panel("Replies &amp; needs attention", _empty("No replies waiting."), badge="0")
    body = _table(replies, [("Lead", "name"), ("Status", "status"),
                            ("Last contacted", "last_contacted"), ("Note", "note")])
    return _panel("Replies &amp; needs attention", body, badge=str(len(replies)))


def _discovery(snapshot: dict) -> str:
    lad = snapshot.get("discovery_ladder")
    if not lad:
        return _panel("Discovery ladder", _empty("Awaiting Notion discovery queues."))
    due = lad.get("due_question") or []
    unlocked = lad.get("offer_unlocked") or []
    body = "<h4>Due the discovery question</h4>"
    body += _table(due, [("Lead", "name"), ("Status", "status"), ("Next action", "next_action")]) if due else _empty("None due.")
    body += "<h4>Answer logged · offer unlocked</h4>"
    body += _table(unlocked, [("Lead", "name"), ("Anchor", "anchor"), ("Answer (verbatim)", "answer")]) if unlocked else _empty("None.")
    return _panel("Discovery ladder", body)


def _followups(snapshot: dict) -> str:
    fus = snapshot.get("due_followups")
    if fus is None:
        return _panel("Follow-ups due", _empty("Awaiting Notion due-touch query."))
    if not fus:
        return _panel("Follow-ups due", _empty("Nothing due today."), badge="0")
    body = _table(fus, [("Lead", "name"), ("Touch", "touch"), ("Inbox", "inbox"),
                        ("Carries", "carries"), ("Next action", "next_action")])
    return _panel("Follow-ups due", body, badge=str(len(fus)))


def _send_queue(snapshot: dict) -> str:
    sq = snapshot.get("send_queue")
    if sq is None:
        return _panel("Send queue", _empty("Awaiting the Send Queue view."))
    if not sq:
        return _panel("Send queue", _empty("Empty — do walks before sending."), badge="0")
    # Group by inbox for the per-domain view the ceiling cares about.
    groups: dict[str, list] = {}
    for it in sq:
        groups.setdefault(it.get("inbox") or "Unassigned", []).append(it)
    body = ""
    for inbox_label in sorted(groups):
        rows = groups[inbox_label]
        body += f'<h4>{_esc(inbox_label)} <span class="muted">· {len(rows)}</span></h4>'
        body += _table(rows, [("Lead", "name"), ("Status", "status"),
                              ("Finding", "finding_verified"), ("Email", "email_verified")])
    return _panel("Send queue", body, badge=str(len(sq)))


def _price_discovery(snapshot: dict) -> str:
    pd = snapshot.get("price_discovery")
    if not pd:
        return _panel("Price discovery study", _empty("Awaiting the discovery study query."))
    anchors = pd.get("anchors") or {}
    est = pd.get("est_value") or {}
    peak = max([int(v) for v in anchors.values()] + [1])

    body = "<h4>Anchor distribution</h4>"
    if anchors:
        for a in ANCHOR_ORDER:
            if a not in anchors:
                continue
            n = int(anchors[a])
            klass = "kill" if a.startswith("Below") or a == "Refused to name" else "flow"
            body += (f'<div class="frow"><span class="flabel">{_esc(a)}</span>'
                     f'<div class="fbar"><div class="fbar-fill {klass}" style="width:{_pct(n, peak):.0f}%"></div></div>'
                     f'<span class="fnum">{_esc(n)}</span></div>')
    else:
        body += _empty("No anchors recorded yet.")

    if est:
        body += "<h4>Estimated value</h4><div class=\"chips\">"
        for k, v in est.items():
            body += f'<span class="chip">{_esc(k)} <b>{_esc(v)}</b></span>'
        body += "</div>"
    return _panel("Price discovery study", body)


def _scoreboard(snapshot: dict) -> str:
    sb = snapshot.get("scoreboard")
    if not sb:
        return _panel("Weekly scoreboard", _empty("Awaiting weekly aggregates."))
    tiles = "".join(
        f'<div class="tile"><span class="tile-num">{_esc(v)}</span>'
        f'<span class="tile-lab">{_esc(k)}</span></div>'
        for k, v in sb.items()
    )
    return _panel("Weekly scoreboard", f'<div class="tiles">{tiles}</div>')


def _hygiene(snapshot: dict) -> str:
    alerts = snapshot.get("hygiene")
    if alerts is None:
        return _panel("Hygiene alerts", _empty("Awaiting hygiene checks."))
    if not alerts:
        return _panel("Hygiene alerts", '<p class="ok-note">All clear — no impossible states flagged.</p>', badge="0")
    items = "".join(f"<li>{_esc(a)}</li>" for a in alerts)
    return _panel("Hygiene alerts", f'<ul class="alerts">{items}</ul>', badge=str(len(alerts)))


def _panel(title: str, body: str, badge: str | None = None) -> str:
    badge_html = f'<span class="badge">{_esc(badge)}</span>' if badge is not None else ""
    return (f'<section class="panel"><div class="panel-head"><h3>{title}</h3>{badge_html}</div>'
            f'<div class="panel-body">{body}</div></section>')


_STYLE = """
<style>
:root{
  --bg:#eceff2;--surface:#ffffff;--surface-2:#f4f6f8;--ink:#161c21;
  --ink-soft:#5c6873;--ink-faint:#8b97a1;--hair:#d9dfe4;--hair-strong:#c3cbd2;
  --flow:#0c877c;--flow-soft:#e3f1ef;--kill:#b0473e;--kill-soft:#f4e2e0;
  --warn:#b0473e;--ok:#0c877c;--high:#ab6f16;
  --shadow:0 1px 2px rgba(20,30,40,.05),0 8px 24px -12px rgba(20,30,40,.18);
  --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0b1114;--surface:#131b20;--surface-2:#0e161a;--ink:#e5edf1;
  --ink-soft:#97a4ae;--ink-faint:#64717b;--hair:#253138;--hair-strong:#33424b;
  --flow:#2cb6a5;--flow-soft:#0f2320;--kill:#d47268;--kill-soft:#291613;
  --warn:#d47268;--ok:#2cb6a5;--high:#d79f4c;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
}}
:root[data-theme="light"]{
  --bg:#eceff2;--surface:#ffffff;--surface-2:#f4f6f8;--ink:#161c21;
  --ink-soft:#5c6873;--ink-faint:#8b97a1;--hair:#d9dfe4;--hair-strong:#c3cbd2;
  --flow:#0c877c;--flow-soft:#e3f1ef;--kill:#b0473e;--kill-soft:#f4e2e0;
  --warn:#b0473e;--ok:#0c877c;--high:#ab6f16;
}
:root[data-theme="dark"]{
  --bg:#0b1114;--surface:#131b20;--surface-2:#0e161a;--ink:#e5edf1;
  --ink-soft:#97a4ae;--ink-faint:#64717b;--hair:#253138;--hair-strong:#33424b;
  --flow:#2cb6a5;--flow-soft:#0f2320;--kill:#d47268;--kill-soft:#291613;
  --warn:#d47268;--ok:#2cb6a5;--high:#d79f4c;
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1120px;margin:0 auto;padding:clamp(20px,4vw,44px) clamp(14px,3vw,32px) 72px;}
header{margin-bottom:24px;}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-faint);margin:0 0 8px;}
h1{font-size:clamp(24px,4vw,34px);margin:0 0 6px;letter-spacing:-.02em;}
.stamp{color:var(--ink-soft);font-size:14px;}
.stamp b{color:var(--ink);}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;align-items:start;}
.panel{background:var(--surface);border:1px solid var(--hair);border-radius:14px;box-shadow:var(--shadow);overflow:hidden;}
.panel.wide{grid-column:1/-1;}
.panel-head{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:14px 18px;border-bottom:1px solid var(--hair);background:var(--surface-2);}
.panel-head h3{margin:0;font-size:14px;letter-spacing:.01em;text-transform:uppercase;color:var(--ink-soft);font-weight:650;}
.badge{font-family:var(--mono);font-size:12px;min-width:22px;text-align:center;padding:2px 8px;border-radius:20px;background:var(--flow-soft);color:var(--flow);border:1px solid var(--hair);}
.panel-body{padding:16px 18px;}
.panel-foot{margin-top:12px;font-size:12.5px;}
.muted{color:var(--ink-faint);font-weight:400;}
.warn{color:var(--warn);font-weight:600;}
.empty{color:var(--ink-faint);font-style:italic;margin:2px 0;font-size:14px;}
.ok-note{color:var(--ok);margin:2px 0;font-size:14px;}
h4{margin:16px 0 8px;font-size:12.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink-faint);}
h4:first-child{margin-top:0;}
/* meters */
.meter-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;}
.meter{border:1px solid var(--hair);border-radius:10px;padding:12px 14px;background:var(--surface-2);}
.meter-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px;}
.meter-label{font-weight:650;}
.meter-num{font-family:var(--mono);font-size:22px;font-weight:600;font-variant-numeric:tabular-nums;}
.meter-den{font-size:14px;color:var(--ink-faint);}
.meter-addr{font-size:12px;margin:2px 0 8px;word-break:break-all;}
.meter-sub{font-size:12.5px;margin-top:5px;}
.ramp{font-size:11.5px;color:var(--ink-soft);margin-top:8px;padding-top:8px;border-top:1px dashed var(--hair);font-family:var(--mono);line-height:1.45;}
.ramp.bad{color:var(--warn);}
.bar{height:8px;border-radius:6px;background:var(--hair);overflow:hidden;}
.bar-fill{height:100%;border-radius:6px;}
.bar-fill.ok{background:var(--ok);}
.bar-fill.high{background:var(--high);}
.bar-fill.over{background:var(--kill);}
.bar-fill.unknown{background:repeating-linear-gradient(45deg,var(--hair),var(--hair) 6px,var(--hair-strong) 6px,var(--hair-strong) 12px);}
/* funnel rows */
.frow{display:grid;grid-template-columns:150px 1fr 40px;align-items:center;gap:10px;margin:4px 0;}
.flabel{font-size:13px;color:var(--ink-soft);}
.fbar{height:16px;border-radius:5px;background:var(--surface-2);border:1px solid var(--hair);overflow:hidden;}
.fbar-fill{height:100%;}
.fbar-fill.flow{background:var(--flow);}
.fbar-fill.kill{background:var(--kill);}
.fbar-fill.other{background:var(--high);}
.fnum{font-family:var(--mono);font-size:14px;text-align:right;font-weight:600;font-variant-numeric:tabular-nums;}
.frow-sep{margin:12px 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-faint);}
/* tables */
.twrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:13px;}
th{text-align:left;font-weight:600;color:var(--ink-faint);padding:6px 10px;border-bottom:1px solid var(--hair-strong);white-space:nowrap;}
td{padding:6px 10px;border-bottom:1px solid var(--hair);vertical-align:top;}
tr:last-child td{border-bottom:none;}
/* chips + tiles */
.chips{display:flex;flex-wrap:wrap;gap:8px;}
.chip{font-size:12.5px;padding:4px 10px;border-radius:20px;background:var(--surface-2);border:1px solid var(--hair);}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;}
.tile{border:1px solid var(--hair);border-radius:10px;padding:12px;background:var(--surface-2);text-align:center;}
.tile-num{display:block;font-family:var(--mono);font-size:26px;font-weight:650;font-variant-numeric:tabular-nums;}
.tile-lab{display:block;font-size:12px;color:var(--ink-faint);margin-top:2px;}
.alerts{margin:0;padding-left:18px;}
.alerts li{margin:4px 0;font-size:13.5px;color:var(--warn);}
</style>
"""

# Tiny inline theme toggle: honors the Artifact viewer's data-theme stamp and
# also works standalone. No external assets.
_SCRIPT = """
<script>
(function(){
  var b=document.getElementById('themeBtn');
  if(!b)return;
  b.addEventListener('click',function(){
    var r=document.documentElement;
    var cur=r.getAttribute('data-theme');
    if(!cur){cur=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}
    r.setAttribute('data-theme',cur==='dark'?'light':'dark');
  });
})();
</script>
"""


def render_html(snapshot: dict, title: str = "Funnel Auditor — Command Center") -> str:
    """Render the full self-contained dashboard fragment from a snapshot.

    Validates the load-bearing core first (so a broken skeleton fails loudly),
    then draws every panel — each degrading to an empty state when its
    skill-filled data is still null. No external assets: Artifact-ready and
    browser-openable, matching docs/uae-track/pipeline.html.
    """
    validate_snapshot(snapshot)

    stamp = (f'<span class="stamp">As of <b>{_esc(snapshot.get("generated_at"))}</b> '
             f'· {_esc(snapshot.get("timezone", "Asia/Dubai"))}</span>')
    header = (
        '<header><p class="eyebrow">UAE Lead Pipeline · live snapshot</p>'
        f'<h1>{_esc(title)}</h1>{stamp} '
        '<button id="themeBtn" style="float:right;font:inherit;font-size:12px;'
        'padding:4px 10px;border-radius:8px;border:1px solid var(--hair);'
        'background:var(--surface);color:var(--ink-soft);cursor:pointer;">◐ theme</button>'
        '</header>'
    )

    # Layout: meters + pipeline span the full width up top; the operator panels
    # flow into the auto-fit grid below them.
    wide = "".join(
        panel.replace('<section class="panel">', '<section class="panel wide">', 1)
        for panel in (_meters(snapshot), _pipeline(snapshot))
    )
    regular = (
        _replies(snapshot) + _send_queue(snapshot) + _discovery(snapshot) +
        _followups(snapshot) + _price_discovery(snapshot) + _scoreboard(snapshot) +
        _hygiene(snapshot)
    )
    grid = f'<div class="grid">{wide}{regular}</div>'

    return f"<title>{_esc(title)}</title>\n{_STYLE}\n<div class=\"wrap\">{header}{grid}</div>\n{_SCRIPT}"
