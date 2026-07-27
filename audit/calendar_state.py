"""
Calendar-state check — how full is a coach's public booking calendar?

Built 2026-07-27 for The First Five, which sells booked calls. The finding
that opens a cold email had to change with it: a funnel-mechanics defect (a
404, a test SKU, a stale date) is SHALLOW — the coach reads the email, fixes
it herself in five minutes, thanks you and leaves. That is not a theory; it
is 4 of 9 engaged leads (Rita fixed her booking redirect, Avneet fixed her
test-SKU checkout). A calendar with three weeks wide open is the opposite:
verifiable, felt as money not arriving, and NOT fixable by editing a page.

`walk.md` used to list "an empty calendar" as SHALLOW/self-fixable. That
conflated two genuinely different facts, and this module is what makes the
split machine-checkable:

  * `none_published` — the scheduler resolves but publishes zero bookable
    time. That IS a config bug she can fix in five minutes. SHALLOW.
  * `wide_open`     — the scheduler works perfectly and most of the next
    month is free. Nobody is booking her. DEEP, and opener-legal.
  * `partial`       — neither. Not an opener on its own.

WHY THIS IS ALLOWED under the repo's no-login rule: these are the exact
requests the lead's own public booking page fires in any visitor's browser,
GET-only, idempotent, reserving nothing. No key, no token, no cookie, no
account. Calendly literally answers `current_user: {"id": null}`. We read
what her page already publishes to the world, without rendering it.

WHY IT IS NOT A BROWSER JOB: a Calendly booking page is a ~1KB JavaScript
shell, and the widget's slot fetch happens inside an injected iframe, on a
network stack the parent page's networkidle signal never sees. That is the
screenshot blind spot `config.BOOKING_EMBED_HOSTS` already exists to warn
about. Rather than fight it with Playwright, we call the same endpoint the
widget calls: three `requests.get` calls, no browser. (`cta-probe` is the
wrong tool for this and must not be stretched into it — it CLICKS things,
and clicking a live scheduler risks reserving a real slot on a real coach's
calendar.)

THE TRAP THIS MODULE EXISTS TO PREVENT, reproduced live during design:
Calendly answers a transient calendar-sync failure with HTTP 400 and
`{"failure": {"code": "external_calendar_error"}}` — no `days` key at all.
A parser doing `payload.get("days", [])` turns that into "this coach has no
availability", which is a FABRICATED FINDING, and "never invent findings"
is the hardest rule in this repo. So: status code and `failure` are checked
BEFORE anything is counted, and an error always raises instead of returning
an empty result. The same 400 cleared on 4 of 4 retries, which is why a
verdict needs >= 2 consistent reads before it can be banked.

Supported today: Calendly and Cal.com, both confirmed live with
unauthenticated GETs. TidyCal's real routes could not be resolved without a
network capture, and Acuity / SavvyCal / YouCanBook.me are uninvestigated —
all four return `unsupported`, never a guess.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlparse

import requests

# Dubai is the market, and a coach's published availability is in her own
# timezone anyway — this only controls how the API buckets slots into days.
DEFAULT_TIMEZONE = "Asia/Dubai"

# Calendly 400s a range wider than roughly a month, with `failure.code` =
# "general" and the SAME human-readable string it uses for a real calendar
# error. One calendar month per call is what the widget itself requests.
MAX_WINDOW_DAYS = 30

# A verdict is only trustworthy when two independent reads agree. The 400 hit
# during design cleared on every retry, so a single read cannot distinguish a
# real empty calendar from a transient sync failure.
REQUIRED_CONSISTENT_READS = 2

# `wide_open` is the opener-legal state, so its threshold is deliberately
# conservative: most of the bookable week, for weeks. Tunable, but moving it
# down means shipping openers that say "your calendar is empty" to coaches
# whose calendar is merely normal.
WIDE_OPEN_DAY_RATIO = 0.60

_CALENDLY_API = "https://calendly.com/api/booking"
_CALCOM_API = "https://api.cal.com/v2"
_CALCOM_API_VERSION = "2024-09-04"

_UA = "Mozilla/5.0 (compatible; FunnelAuditorCalendarState/1.0)"

# Pulled from config so the booking-host vocabulary has ONE home.
try:  # pragma: no cover - config import is trivial
    from config import BOOKING_EMBED_HOSTS
except ImportError:  # pragma: no cover
    BOOKING_EMBED_HOSTS = (
        "calendly.com", "tidycal.com", "acuityscheduling.com",
        "savvycal.com", "cal.com", "youcanbook.me",
    )


class CalendarStateError(Exception):
    """Any reason we could not establish calendar state with confidence.

    Deliberately raised (never swallowed into an empty result) so a
    transient API failure can never be mistaken for "she has no
    availability" — see the module docstring.
    """


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().lstrip("www.")


def platform_for(url: str) -> str:
    """Which scheduler is this, if any? Returns "" for a non-booking URL."""
    h = _host(url)
    for known in BOOKING_EMBED_HOSTS:
        if h == known or h.endswith("." + known):
            return known
    return ""


def _get(url: str, *, params: dict | None = None, headers: dict | None = None,
         timeout: int = 20) -> Any:
    """GET + JSON, with the status ladder this module's correctness rests on.

    Mirrors `email_verifier`/`apify`: distinguish the failure modes, name
    them, and raise. Never returns a partial or defaulted payload.
    """
    hdrs = {"User-Agent": _UA, "Accept": "application/json"}
    hdrs.update(headers or {})
    try:
        resp = requests.get(url, params=params, headers=hdrs, timeout=timeout)
    except requests.RequestException as exc:
        raise CalendarStateError(f"network error reaching {_host(url)}: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError as exc:
        raise CalendarStateError(
            f"non-JSON response from {_host(url)} ({resp.status_code}): {resp.text[:200]}"
        ) from exc

    # Checked BEFORE the status code: Calendly reports a real calendar-sync
    # failure as 400 + `failure`, and that must never be read as "no slots".
    if isinstance(payload, dict) and payload.get("failure"):
        f = payload["failure"] or {}
        code = f.get("code") or "unknown"
        raise CalendarStateError(
            f"{_host(url)} returned failure.code={code}: {f.get('error') or ''} "
            "— this is an API/calendar-sync error, NOT an empty calendar"
        )

    if resp.status_code == 404:
        raise CalendarStateError(f"404 from {_host(url)} — no such profile or event type")
    if resp.status_code == 429:
        raise CalendarStateError(f"429 rate limited by {_host(url)} — back off and retry")
    if not resp.ok:
        raise CalendarStateError(
            f"{resp.status_code} from {_host(url)}: {str(payload)[:300]}"
        )
    return payload


# --- Calendly -------------------------------------------------------------
# Three public hops. A Calendly page is a JS shell, so there is nothing to
# scrape; the widget builds itself from exactly these.

def _calendly_parts(url: str) -> tuple[str, str]:
    """(profile_slug, event_slug) from a calendly.com URL. Event may be ""."""
    segs = [s for s in urlparse(url).path.split("/") if s]
    if not segs:
        raise CalendarStateError(f"no Calendly profile slug in {url}")
    return segs[0], (segs[1] if len(segs) > 1 else "")


def calendly_state(url: str, *, window_days: int = MAX_WINDOW_DAYS,
                   timezone: str = DEFAULT_TIMEZONE, today: date | None = None) -> dict:
    slug, event_slug = _calendly_parts(url)

    profile = _get(f"{_CALENDLY_API}/profiles/{slug}")
    events = _get(f"{_CALENDLY_API}/profiles/{slug}/event_types")
    if not isinstance(events, list) or not events:
        raise CalendarStateError(f"Calendly profile '{slug}' publishes no event types")

    if event_slug:
        chosen = next((e for e in events if e.get("slug") == event_slug), None)
        if chosen is None:
            raise CalendarStateError(
                f"Calendly event '{event_slug}' not found on '{slug}' "
                f"(available: {', '.join(e.get('slug', '?') for e in events[:8])})"
            )
    else:
        chosen = events[0]

    uuid = chosen.get("uuid")
    if not uuid:
        raise CalendarStateError(f"Calendly event type on '{slug}' has no uuid")

    start = today or date.today()
    payload = _get(
        f"{_CALENDLY_API}/event_types/{uuid}/calendar/range",
        params={
            "timezone": timezone,
            "diagnostics": "false",
            "range_start": start.isoformat(),
            "range_end": (start + timedelta(days=window_days)).isoformat(),
        },
    )

    # `days` omits unavailable days entirely, so its length is the count of
    # BOOKABLE days, not the window width. Still filter on status defensively.
    days = payload.get("days")
    if days is None:
        raise CalendarStateError(
            "Calendly range response has no `days` key and no `failure` — "
            "unexpected shape, refusing to guess at availability"
        )
    open_days = [d for d in days if d.get("status") == "available"]
    slots = sum(len(d.get("spots") or []) for d in open_days)

    return {
        "platform": "calendly",
        "owner": profile.get("name") or slug,
        "event": chosen.get("name") or chosen.get("slug"),
        "event_slug": chosen.get("slug"),
        "available_days": len(open_days),
        "open_slots": slots,
    }


# --- Cal.com --------------------------------------------------------------
# `/v2/slots` is documented as bearer-auth but answers public event types
# unauthenticated. The numeric eventTypeId is required — the
# ?username=&eventTypeSlug= form 404s. Cal.com SSRs its booking page, so
# Firecrawl can already read the id out of the HTML.

_CALCOM_EVENT_ID_RE = re.compile(r'"eventTypeId"\s*:\s*(\d+)')


def _calcom_event_type_id(url: str) -> int:
    try:
        resp = requests.get(url, headers={"User-Agent": _UA}, timeout=20)
    except requests.RequestException as exc:
        raise CalendarStateError(f"network error reaching cal.com: {exc}") from exc
    m = _CALCOM_EVENT_ID_RE.search(resp.text or "")
    if not m:
        raise CalendarStateError(
            f"no eventTypeId found in the cal.com page at {url} — cannot query slots "
            "(the ?username=&eventTypeSlug= form is not supported by the API)"
        )
    return int(m.group(1))


def calcom_state(url: str, *, window_days: int = MAX_WINDOW_DAYS,
                 timezone: str = DEFAULT_TIMEZONE, today: date | None = None) -> dict:
    event_type_id = _calcom_event_type_id(url)
    start = today or date.today()
    payload = _get(
        f"{_CALCOM_API}/slots",
        params={
            "eventTypeId": event_type_id,
            "start": start.isoformat(),
            "end": (start + timedelta(days=window_days)).isoformat(),
            "timeZone": timezone,
        },
        headers={"cal-api-version": _CALCOM_API_VERSION},
    )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise CalendarStateError(
            "cal.com slots response has no `data` object — unexpected shape, "
            "refusing to guess at availability"
        )
    return {
        "platform": "cal.com",
        "owner": urlparse(url).path.strip("/").split("/")[0],
        "event": f"eventTypeId={event_type_id}",
        "event_slug": None,
        "available_days": len([d for d, s in data.items() if s]),
        "open_slots": sum(len(s or []) for s in data.values()),
    }


# --- verdict --------------------------------------------------------------

def _business_days(window_days: int, start: date) -> int:
    return sum(
        1 for i in range(window_days)
        if (start + timedelta(days=i)).weekday() < 5
    )


def classify(available_days: int, open_slots: int, window_days: int,
             start: date) -> tuple[str, str]:
    """(verdict, human detail). See the module docstring for the three states."""
    if open_slots == 0:
        return "none_published", (
            f"the scheduler resolves but publishes no bookable time in the next "
            f"{window_days} days — a configuration problem she can fix herself, "
            "so this is SHALLOW and must not be the opener"
        )
    biz = _business_days(window_days, start) or 1
    ratio = available_days / biz
    if ratio >= WIDE_OPEN_DAY_RATIO:
        return "wide_open", (
            f"{open_slots} open slots across {available_days} of {biz} weekdays in the "
            f"next {window_days} days ({ratio:.0%} of the working month is unbooked) — "
            "she cannot fix this by editing a page, so it is DEEP and opener-legal"
        )
    return "partial", (
        f"{open_slots} open slots across {available_days} of {biz} weekdays "
        f"({ratio:.0%}) — a normally-busy calendar, not an opener on its own"
    )


def check(url: str, *, window_days: int = MAX_WINDOW_DAYS,
          timezone: str = DEFAULT_TIMEZONE, reads: int = REQUIRED_CONSISTENT_READS,
          today: date | None = None) -> dict:
    """Resolve a booking URL's calendar state, confirmed across `reads` reads.

    Raises CalendarStateError on an unsupported platform, an API failure, or
    reads that disagree. It never returns a low-confidence result, because
    the output is destined for a cold email.
    """
    if window_days > MAX_WINDOW_DAYS:
        raise CalendarStateError(
            f"window_days={window_days} exceeds {MAX_WINDOW_DAYS}; wider ranges are "
            "rejected by the API with the same error string it uses for a real "
            "calendar fault, so they are refused here instead"
        )

    platform = platform_for(url)
    if platform == "calendly.com":
        fn = calendly_state
    elif platform == "cal.com":
        fn = calcom_state
    elif platform:
        raise CalendarStateError(
            f"{platform} is a known scheduler but has no verified public availability "
            "endpoint yet — returning nothing rather than guessing"
        )
    else:
        raise CalendarStateError(f"{url} is not a supported booking page")

    start = today or date.today()
    observed = []
    for _ in range(max(1, reads)):
        r = fn(url, window_days=window_days, timezone=timezone, today=start)
        r["verdict"], r["detail"] = classify(
            r["available_days"], r["open_slots"], window_days, start
        )
        observed.append(r)

    verdicts = {o["verdict"] for o in observed}
    if len(verdicts) > 1:
        raise CalendarStateError(
            f"reads disagreed ({', '.join(sorted(verdicts))}) — calendar state is not "
            "stable enough to bank as a finding; re-run later"
        )

    final = observed[-1]
    # `depth` is the Findings Bank DSL tag, so it is only set when there is
    # actually something to bank. `partial` is a normally-busy calendar — not
    # a shallow finding, NOT A FINDING AT ALL — and tagging it SHALLOW would
    # invite a walker to bank it as touch-2 material it has no business being.
    verdict = final["verdict"]
    final.update({
        "url": url,
        "window_days": window_days,
        "range_start": start.isoformat(),
        "range_end": (start + timedelta(days=window_days)).isoformat(),
        "timezone": timezone,
        "reads": len(observed),
        "depth": {"wide_open": "DEEP", "none_published": "SHALLOW"}.get(verdict),
        "bankable": verdict in ("wide_open", "none_published"),
        "opener_legal": verdict == "wide_open",
    })
    return final
