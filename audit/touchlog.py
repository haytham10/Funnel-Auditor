"""
Touch-log grammar — the machine-readable page-body format for a lead's Email
Thread Log, Money section, and sourcing line (docs/uae-track/log-grammar.md).

Why this exists: Wave 1 of the Notion -> Airtable migration (122 leads) cost
almost all of its effort in one place — turning free-form prose sends into
structured Touches/Offers rows. 40 of 243 sends (16%) were missing from
their thread logs and had to be recovered from Gmail; 8 are permanently
unrecoverable; reply TYPE (the one number Phase 10 exists to produce) was
never data anywhere. The fix is not a bigger recovery job, it's writing the
log in a shape a parser can walk without a human (or a Claude session)
reading every lead. This module IS that shape:

  TOUCH: n=2 dir=out date=2026-07-28 inbox="Inbox 1" seq=cold subject="..." \
         thread=<id> gate=PASS
  ````
  [verbatim body]
  ````

One sentinel keyword per record (`TOUCH:` / `OFFER:` / `SOURCE:`), one
logical record per physical line, `key=value` tokens (quoted when the value
has a space, `=`, or `"`), and a four-backtick fenced block immediately
after a TOUCH: line holding the verbatim body byte for byte. `render_*`
builds a valid line from structured input — it is the ONLY sanctioned way
to write one (nothing hand-types a sentinel line); `parse_body` extracts
records back out, tolerant of the LEGACY pre-2026-07-27 format
(`[date] — Touch #N — Subject: "..." — Sent`) so it works on the 122
already-migrated leads without rewriting a single one of them; `validate`
is the rule set `log-lint` runs.

Zero third-party dependencies (stdlib regex/dataclasses only) — this must
import cleanly on a machine with no Playwright, no Pillow, no Firecrawl,
exactly like `audit.crm_gate` does today. It reuses `crm_gate.parse_findings_bank`
(read-only) to cross-check a `finding=N` token against the row's Findings
Bank, and `audit.inboxes.is_registered` to cross-check an `inbox=` token —
neither of those modules is modified.

This module never talks to Notion or Airtable. Python has no Notion
credentials anywhere in this repo (grep audit/*.py — every "notion" hit is
prose, not a client call); the skill layer fetches fresh via the Notion MCP
and hands this module a plain row dict + a plain body string, same trust
model as every other gate here ("fetch fresh, pipe verbatim, quote the
literal output line").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from audit import inboxes
from audit.crm_gate import parse_findings_bank

# ---------------------------------------------------------------------------
# Enums (mirrors docs/uae-track/log-grammar.md — that file and this module
# must never disagree; this module is the parser, that file is the reference
# a human reads).
# ---------------------------------------------------------------------------

DIRECTIONS = ("out", "in")
SEQUENCES = ("cold", "warm")

# Canonical touch 2/3+ carriers. `loom-offer` and `leak-fix-offer` are the
# deprecated aliases for `call-ask`, same precedent as audit/crm_gate.py's
# CARRIERS/DEPRECATED_CARRIERS split — kept OUT of CARRIERS so validation
# messages only ever advertise the current name, but still accepted as input so
# historical logs keep parsing. (`loom-offer` → `leak-fix-offer` 2026-07-24,
# both → `call-ask` 2026-07-27 with The First Five.)
CARRIERS = (
    "opener", "second-finding", "call-ask", "disambiguating-question",
    "price-discovery", "money-email", "objection-reply", "reactivation",
)
DEPRECATED_CARRIERS = {"loom-offer": "call-ask", "leak-fix-offer": "call-ask"}
CARRIER_CHOICES = CARRIERS + tuple(DEPRECATED_CARRIERS)

REPLY_TYPES = ("Interested", "Price question", "Brush-off", "Logistics", "Blunt", "Decline")

# "First Five" is the live offer. "Leak Fix" and "Sprint" are RETIRED but stay
# in the enum: `parse_body` has to keep reading the OFFER: lines already written
# into 100+ lead page bodies, and a migration that can't parse its own history
# is the failure this grammar exists to prevent.
OFFER_TYPES = ("First Five", "Fewer Calls", "Setup Deferred", "Custom",
               "Leak Fix", "Sprint", "The Minimum", "Payment Plan", "Funnel Watch")
OFFER_STATUSES = ("Proposed", "Accepted", "Declined", "Paid", "Refunded")
DOWNSELL_RUNGS = ("0", "1", "2")
PAYMENT_TERMS = ("pay after", "50% deposit", "plan", "full up front")

# Every token name this module understands, across all three sentinel kinds.
# A key outside this set is preserved (never dropped) but reported as a WARN
# "unknown token key" — see validate().
_KNOWN_TOUCH_KEYS = {
    "n", "dir", "date", "inbox", "seq", "carries", "finding", "subject",
    "thread", "gate", "bounce", "auto", "type", "reply_to",
}
_KNOWN_OFFER_KEYS = {"type", "amount", "currency", "date", "status", "rung", "objection", "terms"}
_KNOWN_SOURCE_KEYS = {"channel", "query", "date"}

_TOUCH_ORDER = ("n", "dir", "date", "inbox", "seq", "carries", "finding",
                "subject", "thread", "gate", "bounce", "auto", "type", "reply_to")
_OFFER_ORDER = ("type", "amount", "currency", "date", "status", "rung", "objection", "terms")
_SOURCE_ORDER = ("channel", "query", "date")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NO_REPLY = {"no reply", "-", ""}


@dataclass
class Problem:
    """One lint finding. `level` is ERROR (fails closed) or WARN (reported,
    never blocks)."""
    level: str      # "ERROR" | "WARN"
    message: str

    def __str__(self) -> str:
        return f"{self.level}: {self.message}"


# ---------------------------------------------------------------------------
# Tokenizer — the one place that knows how to read `key=value key2="a b"`.
# ---------------------------------------------------------------------------

def _tokenize(s: str) -> tuple[dict, list[str]]:
    """Parse a `key=value key2="quoted value"` string into (tokens, errors).

    Quoted values may contain spaces, `=`, and an escaped `\\"` for a literal
    quote (and `\\\\` for a literal backslash — the exact inverse of
    `_format_value`'s escaping, so render -> parse round-trips byte for
    byte). A bare word with no `=` is a grammar violation (B.5: "Bare `key`
    with no `=` is invalid") and is reported as an error, not silently
    skipped, so a malformed line can't quietly lose a token.
    """
    tokens: dict[str, str] = {}
    errors: list[str] = []
    i, n = 0, len(s)
    while i < n:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break
        start = i
        while i < n and (s[i].isalnum() or s[i] == "_"):
            i += 1
        key = s[start:i]
        if not key or i >= n or s[i] != "=":
            while i < n and not s[i].isspace():
                i += 1
            errors.append(f"bare token {s[start:i]!r} has no `key=value` form")
            continue
        i += 1  # skip '='
        if i < n and s[i] == '"':
            i += 1
            chars = []
            closed = False
            while i < n:
                c = s[i]
                if c == "\\" and i + 1 < n:
                    chars.append(s[i + 1])
                    i += 2
                    continue
                if c == '"':
                    closed = True
                    i += 1
                    break
                chars.append(c)
                i += 1
            if not closed:
                errors.append(f"unterminated quoted value for {key!r}")
            tokens[key] = "".join(chars)
        else:
            vstart = i
            while i < n and not s[i].isspace():
                i += 1
            tokens[key] = s[vstart:i]
    return tokens, errors


_NEEDS_QUOTE = re.compile(r'[\s"=]')


def _format_value(value) -> str:
    s = str(value)
    if s == "" or _NEEDS_QUOTE.search(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _render_sentinel(keyword: str, tokens: dict, order: tuple[str, ...]) -> str:
    parts = [f"{keyword}:"]
    seen = set()
    for k in order:
        if k in tokens:
            parts.append(f"{k}={_format_value(tokens[k])}")
            seen.add(k)
    for k in sorted(tokens):
        if k not in seen:
            parts.append(f"{k}={_format_value(tokens[k])}")
    return " ".join(parts)


def _fence(body: str) -> str:
    return f"````\n{body}\n````"


# ---------------------------------------------------------------------------
# render_* — the only sanctioned way to write a sentinel line.
# ---------------------------------------------------------------------------

def _canonical_carrier(carries: str | None) -> str | None:
    if carries is None:
        return None
    return DEPRECATED_CARRIERS.get(carries, carries)


def _touch_token_errors(tokens: dict) -> list[str]:
    """Hard requirements for one TOUCH record's tokens, independent of
    direction-specific business context (Findings Bank, inbox registry —
    those are cross-checks `validate()` runs against a live row, not
    something a bare render can know). Returns [] when clean."""
    errors = []

    direction = tokens.get("dir")
    if direction not in DIRECTIONS:
        errors.append(f'dir={direction!r} must be one of {DIRECTIONS}')

    n_raw = tokens.get("n")
    if n_raw is None or not re.match(r"^\d+$", str(n_raw)):
        errors.append(f'n={n_raw!r} must be a positive integer')

    date_raw = tokens.get("date")
    if not date_raw or not _DATE_RE.match(date_raw):
        errors.append(f'date={date_raw!r} must be YYYY-MM-DD')

    if not tokens.get("thread"):
        errors.append("thread is required")

    if direction == "out":
        if not tokens.get("inbox"):
            errors.append("inbox is required on dir=out")
        if tokens.get("seq") not in SEQUENCES:
            errors.append(f'seq={tokens.get("seq")!r} must be one of {SEQUENCES} on dir=out')
        if not tokens.get("subject"):
            errors.append("subject is required on dir=out")
        if not tokens.get("gate"):
            errors.append("gate is required on dir=out")
        try:
            n_int = int(n_raw)
        except (TypeError, ValueError):
            n_int = None
        if n_int is not None and n_int >= 2:
            carries_raw = tokens.get("carries")
            canonical = _canonical_carrier(carries_raw)
            if canonical not in CARRIERS:
                errors.append(
                    f'carries={carries_raw!r} is required on touch n>=2 and must be one '
                    f'of {CARRIER_CHOICES}'
                )
            elif canonical == "second-finding" and not tokens.get("finding"):
                errors.append('finding=<rank> is required when carries=second-finding')

    elif direction == "in":
        bounce = str(tokens.get("bounce", "")).strip().lower() == "true"
        auto = str(tokens.get("auto", "")).strip().lower() == "true"
        if not bounce and not auto:
            reply_type = tokens.get("type")
            if not reply_type or reply_type.strip().lower() not in {t.lower() for t in REPLY_TYPES}:
                errors.append(
                    f'type={reply_type!r} is required on every inbound touch that is not '
                    f'bounce=true/auto=true, and must be one of {REPLY_TYPES}'
                )

    return errors


def render_touch(**fields) -> str:
    """Build a valid `TOUCH:` block (sentinel line + fenced body, if given).

    `body` is popped out of `fields` and fenced separately; every other
    kwarg becomes a token (None/empty values are omitted, not emitted as
    `key=`). Raises ValueError — printing nothing — on any hard grammar
    violation (missing required token, bad enum), so a caller (the
    `touch-log render` CLI) can fail closed rather than emit a half-valid
    block, which is worse than none because it looks logged.
    """
    body = fields.pop("body", None)
    tokens = {k: str(v) for k, v in fields.items() if v is not None and v != ""}
    errors = _touch_token_errors(tokens)
    if errors:
        raise ValueError("invalid TOUCH block: " + "; ".join(errors))
    line = _render_sentinel("TOUCH", tokens, _TOUCH_ORDER)
    return line if body is None else line + "\n" + _fence(body)


def _offer_token_errors(tokens: dict) -> list[str]:
    errors = []
    if tokens.get("type") not in OFFER_TYPES:
        errors.append(f'type={tokens.get("type")!r} must be one of {OFFER_TYPES}')
    amount = tokens.get("amount")
    if amount is None or not re.match(r"^\d+(\.\d+)?$", str(amount)):
        errors.append(f'amount={amount!r} must be a plain number, no currency symbol')
    if tokens.get("currency") != "AED":
        errors.append(f'currency={tokens.get("currency")!r} must be "AED"')
    if not tokens.get("date") or not _DATE_RE.match(tokens["date"]):
        errors.append(f'date={tokens.get("date")!r} must be YYYY-MM-DD')
    if tokens.get("status") not in OFFER_STATUSES:
        errors.append(f'status={tokens.get("status")!r} must be one of {OFFER_STATUSES}')
    if "rung" in tokens and tokens["rung"] not in DOWNSELL_RUNGS:
        errors.append(f'rung={tokens.get("rung")!r} must be one of {DOWNSELL_RUNGS}')
    if "terms" in tokens and tokens["terms"] not in PAYMENT_TERMS:
        errors.append(f'terms={tokens.get("terms")!r} must be one of {PAYMENT_TERMS}')
    return errors


def render_offer(**fields) -> str:
    """Build a valid `OFFER:` line. Never has a body — see B.3. A status
    change is a NEW call with the same `type`, never an edit of a prior
    line; this function only builds one line, the append-not-overwrite
    discipline is the caller's job (same as the Findings Bank rule)."""
    tokens = {k: str(v) for k, v in fields.items() if v is not None and v != ""}
    errors = _offer_token_errors(tokens)
    if errors:
        raise ValueError("invalid OFFER line: " + "; ".join(errors))
    return _render_sentinel("OFFER", tokens, _OFFER_ORDER)


def render_source(**fields) -> str:
    """Build a valid `SOURCE:` line (B.4) — channel + query + date."""
    tokens = {k: str(v) for k, v in fields.items() if v is not None and v != ""}
    errors = []
    for req in _KNOWN_SOURCE_KEYS:
        if not tokens.get(req):
            errors.append(f"{req} is required")
    if tokens.get("date") and not _DATE_RE.match(tokens["date"]):
        errors.append(f'date={tokens.get("date")!r} must be YYYY-MM-DD')
    if errors:
        raise ValueError("invalid SOURCE line: " + "; ".join(errors))
    return _render_sentinel("SOURCE", tokens, _SOURCE_ORDER)


# ---------------------------------------------------------------------------
# parse_body — the inverse. Tolerant of the legacy pre-2026-07-27 format so
# it works unmodified on the 122 already-migrated lead pages.
# ---------------------------------------------------------------------------

_SENTINEL_RE = re.compile(r"^(TOUCH|OFFER|SOURCE):\s*(.*)$")
_FENCE_RE = re.compile(r"^````\s*$")

# A real legacy Email Thread Log touch header, e.g.:
#   \[2026-07-20\] — Touch #2 — Subject: "..." — Sent
#   2026-07-25 — Touch #2 — Subject: "..." — Sent via Inbox 1 (...) to ...
# The negative lookahead excludes a bounced attempt ("Touch #1 attempt ...
# BOUNCED") from THIS number's block — same precedent as
# crm_gate._TOUCH_BLOCK. Brackets may be Notion-markdown-escaped (`\[`/`\]`)
# or bare; both are tolerated.
_LEGACY_HEADER = re.compile(
    r"^\s*\\?\[?(?P<date>\d{4}-\d{2}-\d{2})\\?\]?\s*[—-]\s*"
    r"Touch\s*#(?P<n>\d+)(?!\s*attempt)\b.*?[—-]\s*Subject:\s*\"(?P<subject>[^\"]*)\"\s*[—-]\s*"
    r"(?P<status>Sent|BOUNCED)",
    re.IGNORECASE,
)
_LEGACY_REPLY = re.compile(r"^\s*Reply:\s*(.*)$", re.IGNORECASE)
_LEGACY_NEXT = re.compile(r"^\s*Next:\s*", re.IGNORECASE)
_LEGACY_HEADING = re.compile(r"^\s*##\s")


def _to_bool(v) -> bool:
    return str(v).strip().lower() == "true"


def _finalize_touch(tokens: dict, body: str | None) -> dict:
    rec = dict(tokens)
    rec["format"] = "v2"
    rec["body"] = body
    if "n" in rec:
        try:
            rec["n"] = int(rec["n"])
        except ValueError:
            pass
    if "finding" in rec:
        try:
            rec["finding"] = int(rec["finding"])
        except ValueError:
            pass
    rec["bounce"] = _to_bool(rec.get("bounce", "false"))
    rec["auto"] = _to_bool(rec.get("auto", "false"))
    if "carries" in rec:
        rec["carries"] = _canonical_carrier(rec["carries"])
    if "reply_to" in rec:
        try:
            rec["reply_to"] = int(rec["reply_to"])
        except ValueError:
            pass
    return rec


def _finalize_offer(tokens: dict) -> dict:
    rec = dict(tokens)
    if "amount" in rec:
        try:
            rec["amount"] = float(rec["amount"]) if "." in rec["amount"] else int(rec["amount"])
        except ValueError:
            pass
    return rec


def _finalize_source(tokens: dict) -> dict:
    return dict(tokens)


def parse_body(text: str) -> dict:
    """Extract `{touches: [...], offers: [...], source: {...} | None,
    warnings: [...]}` from a page body.

    Each touch/offer dict carries `format: "v2" | "legacy"` so callers (and
    `log-lint`) can measure adoption of the new grammar without treating a
    not-yet-touched historical lead as broken. Legacy touches are always
    `dir="out"` (the old format never logged a machine-typed reply); a
    non-"No reply" `Reply:` line under a legacy block is surfaced as its own
    synthetic `dir="in"` legacy record with `type=None` (legacy never
    captured reply type — that's exactly the gap this migration closes going
    forward, not something to fabricate retroactively).
    """
    lines = text.splitlines()
    touches: list[dict] = []
    offers: list[dict] = []
    source: dict | None = None
    warnings: list[str] = []

    i, n = 0, len(lines)
    while i < n:
        raw_line = lines[i]
        line = raw_line.strip()

        m = _SENTINEL_RE.match(line)
        if m:
            keyword, rest = m.group(1), m.group(2)
            tokens, tok_errors = _tokenize(rest)
            for e in tok_errors:
                warnings.append(f"line {i + 1}: {e}")

            body = None
            j = i + 1
            if keyword == "TOUCH" and j < n and _FENCE_RE.match(lines[j].strip()):
                body_lines = []
                k = j + 1
                closed = False
                while k < n:
                    if _FENCE_RE.match(lines[k].strip()):
                        closed = True
                        break
                    body_lines.append(lines[k])
                    k += 1
                if not closed:
                    warnings.append(f"line {j + 1}: unterminated fenced block")
                    i = k
                    continue
                body = "\n".join(body_lines)
                i = k + 1
            else:
                i = j

            if keyword == "TOUCH":
                touches.append(_finalize_touch(tokens, body))
            elif keyword == "OFFER":
                offers.append(_finalize_offer(tokens))
            else:
                source = _finalize_source(tokens)
            continue

        lm = _LEGACY_HEADER.match(raw_line)
        if lm:
            touch_date, touch_n, subject, status = (
                lm.group("date"), int(lm.group("n")), lm.group("subject"), lm.group("status"),
            )
            j = i + 1
            body_lines: list[str] = []
            reply_idx = None
            while j < n:
                if _LEGACY_HEADER.match(lines[j]) or _LEGACY_HEADING.match(lines[j]):
                    break
                if _LEGACY_REPLY.match(lines[j]):
                    reply_idx = j
                    break
                body_lines.append(lines[j])
                j += 1
            body_text = "\n".join(body_lines).strip() or None
            touches.append({
                "format": "legacy", "n": touch_n, "dir": "out", "date": touch_date,
                "subject": subject, "bounce": status.upper() == "BOUNCED", "auto": False,
                "body": body_text,
            })

            if reply_idx is not None:
                reply_m = _LEGACY_REPLY.match(lines[reply_idx])
                reply_lines = [reply_m.group(1)]
                k = reply_idx + 1
                while k < n and not (
                    _LEGACY_NEXT.match(lines[k]) or _LEGACY_HEADER.match(lines[k])
                    or _LEGACY_HEADING.match(lines[k])
                ):
                    reply_lines.append(lines[k])
                    k += 1
                reply_text = "\n".join(reply_lines).strip()
                if reply_text.strip('"').strip().lower() not in _NO_REPLY:
                    touches.append({
                        "format": "legacy", "n": touch_n, "dir": "in", "date": None,
                        "reply_to": touch_n, "type": None, "bounce": False, "auto": False,
                        "body": reply_text,
                    })
                i = k
            else:
                i = j
            continue

        i += 1

    return {"touches": touches, "offers": offers, "source": source, "warnings": warnings}


# ---------------------------------------------------------------------------
# validate — the log-lint rule set, run against a live row + fresh body.
# ---------------------------------------------------------------------------

def _norm(v) -> str:
    return str(v).strip() if v is not None else ""


def validate(row: dict | None, page_body: str, *, today: date | None = None) -> list[Problem]:
    """The full `log-lint` rule set (docs/uae-track/log-grammar.md,
    Part C.2). `row` is a fresh flat Notion property dump (same shape
    `crm_gate` takes) or None when linting a bare archive file with no
    live row to cross-check (`--slug`) — Touch # reconciliation is skipped
    in that case, everything else still runs.
    """
    today = today or date.today()
    problems: list[Problem] = []
    parsed = parse_body(page_body)

    for w in parsed["warnings"]:
        problems.append(Problem("ERROR" if "unterminated" in w else "WARN", w))

    v2_touches = [t for t in parsed["touches"] if t["format"] == "v2"]
    all_touches = parsed["touches"]

    # --- per-record token/enum checks (v2 only — legacy is never held to the
    # new grammar's required-token shape, that's the whole point of "tolerant") --
    for t in v2_touches:
        raw_tokens = {k: v for k, v in t.items() if k not in ("format", "body")}
        # _touch_token_errors wants string-typed tokens (n/finding get
        # coerced back to int by _finalize_touch); re-stringify for the check.
        str_tokens = {k: str(v) for k, v in raw_tokens.items() if v is not None and v != ""}
        for e in _touch_token_errors(str_tokens):
            problems.append(Problem("ERROR", f'touch n={t.get("n")} dir={t.get("dir")}: {e}'))

        for key in raw_tokens:
            if key not in _KNOWN_TOUCH_KEYS:
                problems.append(Problem("WARN", f'touch n={t.get("n")}: unknown token key {key!r}'))

        if not t.get("bounce") and not t.get("body"):
            problems.append(Problem("WARN", f'touch n={t.get("n")} dir={t.get("dir")}: empty body'))

        if t.get("dir") == "out" and t.get("inbox") and not inboxes.is_registered(t["inbox"]):
            problems.append(Problem(
                "ERROR",
                f'touch n={t.get("n")}: inbox={t["inbox"]!r} is not a registered inbox '
                f'(known: {", ".join(inboxes.labels())})',
            ))

        if t.get("carries") == "second-finding" and row is not None:
            bank = parse_findings_bank(row.get("Findings Bank"))
            ranks = {e["rank"] for e in bank}
            if t.get("finding") not in ranks:
                problems.append(Problem(
                    "ERROR",
                    f'touch n={t.get("n")}: carries=second-finding but finding={t.get("finding")!r} '
                    f"is not a real rank in this lead's Findings Bank (ranks present: "
                    f"{sorted(ranks) or 'none'})",
                ))

        date_raw = t.get("date")
        if date_raw and _DATE_RE.match(str(date_raw)):
            try:
                if date.fromisoformat(date_raw) > today:
                    problems.append(Problem("ERROR", f'touch n={t.get("n")}: date {date_raw} is in the future'))
            except ValueError:
                pass

    # --- inbound date must not precede the out touch it replies to ---------
    by_n_out = {t["n"]: t for t in all_touches if t.get("dir") == "out" and isinstance(t.get("n"), int)}
    for t in all_touches:
        if t.get("dir") != "in":
            continue
        reply_to = t.get("reply_to")
        in_date, out_touch = t.get("date"), by_n_out.get(reply_to)
        if in_date and out_touch and out_touch.get("date"):
            try:
                if date.fromisoformat(in_date) < date.fromisoformat(out_touch["date"]):
                    problems.append(Problem(
                        "ERROR",
                        f"inbound reply_to={reply_to} dated {in_date} is earlier than the "
                        f'touch it replies to ({out_touch["date"]})',
                    ))
            except ValueError:
                pass

    # --- n contiguity / duplication, v2 + legacy combined, non-bounce out --
    out_non_bounce = sorted(
        t["n"] for t in all_touches
        if t.get("dir") == "out" and not t.get("bounce") and isinstance(t.get("n"), int)
    )
    if out_non_bounce:
        expected = set(range(1, max(out_non_bounce) + 1))
        found_set = set(out_non_bounce)
        missing = sorted(expected - found_set)
        if missing:
            problems.append(Problem("ERROR", f"missing touch number(s) {missing} — n is not contiguous from 1"))
        dupes = sorted({n for n in out_non_bounce if out_non_bounce.count(n) > 1})
        if dupes:
            problems.append(Problem("ERROR", f"duplicate touch number(s) {dupes} in the out direction"))

    # --- Touch # property reconciliation (needs a live row) ----------------
    if row is not None:
        expected_touch = row.get("Touch #")
        expected_touch = int(expected_touch) if expected_touch not in (None, "") else 0
        found_set = set(out_non_bounce)
        expected_set = set(range(1, expected_touch + 1))
        missing = sorted(expected_set - found_set)
        if missing:
            problems.append(Problem(
                "ERROR",
                f"Touch # = {expected_touch} but the log has no block for touch "
                f"{', '.join(str(n) for n in missing)}",
            ))
        extra = sorted(n for n in found_set if n > expected_touch)
        if extra:
            problems.append(Problem(
                "ERROR",
                f"the log has a touch {max(extra)} block but Touch # is only {expected_touch}",
            ))

        last_reply_type = _norm(row.get("Last Reply Type"))
        inbound_v2 = [t for t in v2_touches if t.get("dir") == "in" and t.get("type")]
        if inbound_v2:
            most_recent = max(inbound_v2, key=lambda t: (t.get("date") or "", t.get("n") or 0))
            if last_reply_type and most_recent["type"].strip().lower() != last_reply_type.strip().lower():
                problems.append(Problem(
                    "WARN",
                    f'Last Reply Type = "{last_reply_type}" disagrees with the most recent '
                    f'logged inbound type "{most_recent["type"]}"',
                ))

    # --- offers: enum errors + status-transition-without-Proposed WARN -----
    seen_proposed_types: set[str] = set()
    for o in parsed["offers"]:
        for e in _offer_token_errors(o):
            problems.append(Problem("ERROR", f'offer type={o.get("type")} date={o.get("date")}: {e}'))
        status = o.get("status")
        otype = o.get("type")
        if status == "Proposed" and otype:
            seen_proposed_types.add(otype)
        elif status and otype and otype not in seen_proposed_types:
            problems.append(Problem(
                "WARN",
                f'offer type={otype} status={status} has no earlier Proposed line for the same type',
            ))

    return problems
