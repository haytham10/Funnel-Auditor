"""Pull the hand-written lines out of Airtable, and refuse the bad ones.

Airtable exists so Haytham can change a line without touching code. That is
only safe if editing a line cannot break an email, so this module is a **gate,
not a copier**. A line that would fail the linter is rejected here, loudly, at
sync time, rather than silently reaching a stranger's inbox two stages later.

What it checks, beyond the obvious required fields:

- **Every number in every line traces to `copy/results.csv`.** Same check the
  drafted email gets. If a line cites AED 91,500, no such client result exists,
  and the sync fails naming the line.
- **No number sits next to a segment it doesn't belong to.** Widening a Business
  result to "coaches here" is fine; calling it a health coach's is not.
- **Weights are sane.** A weight is one number that cannot be wrong on its own,
  which is why it replaced hand-maintained roll ranges: under ranges, adding a
  fifth offer line meant renumbering the other four so the spans stayed
  contiguous, and a slip failed the whole sync. Blank means "equal share".
- **A generic (`Any`) identity line exists.** It is the fallback for every lead
  whose segment is unknown, and without one they draw from an empty pool.

On success it writes two things: a snapshot JSON that `anchors.py` reads, and a
regenerated set of `copy/*.csv` so the committed fallback never drifts from what
Airtable says. On failure it writes nothing at all.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

COPY_DIR = Path(__file__).resolve().parent.parent / "copy"
SNAPSHOT = COPY_DIR / "_airtable.json"

BEATS = ("identity", "offer", "cta", "ps")
WEIGHTED_BEATS = ("offer", "cta", "ps")
COACH_TYPES = ("Business", "Leadership", "Life", "Mindset", "Career",
               "Health", "Fitness", "Executive", "Any")
SELLS_TO = ("corporates", "individuals", "any", "")

# Airtable field name -> our key. Accepts the display names the base actually
# uses; anything else in the record is ignored rather than guessed at.
FIELD_MAP = {
    "Line ID": "id",
    "Beat": "beat",
    "Line": "line",
    "Coach Type": "coach_type",
    "Sells To": "sells_to",
    "Shape": "shape",
    "Claim": "claim",
    "Weight": "weight",
    "Active": "active",
}


@dataclass
class SyncResult:
    lines: list[dict] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def report(self) -> str:
        head = (f"COPY-SYNC: {'PASS' if self.ok else 'FAIL'} — "
                f"{len(self.lines)} line(s) accepted, "
                f"{len(self.problems)} problem(s), {len(self.skipped)} skipped")
        out = [head]
        for problem in self.problems:
            out.append(f"  FAIL  {problem}")
        for note in self.skipped:
            out.append(f"  skip  {note}")
        if self.ok:
            by_beat = {b: sum(1 for l in self.lines if l["beat"] == b) for b in BEATS}
            out.append("  " + ", ".join(f"{b}={n}" for b, n in by_beat.items()))
        return "\n".join(out)


def _truthy_active(value) -> bool:
    """An Airtable checkbox, read safely in every shape it arrives in.

    True / "true" / "yes" / 1 are live. None (the field omitted, which is what
    Airtable sends for unchecked) and False are not. A string that is present
    but empty is not either.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "yes", "y", "1", "checked")


def normalize_records(records: list[dict]) -> tuple[list[dict], list[str]]:
    """Airtable records -> our line shape. Inactive rows are skipped, not failed.

    Accepts either the MCP's `{"fields": {...}}` envelope or a bare field dict,
    because the two paths into this module return different shapes and making
    the caller remember which is a bug waiting to happen.
    """
    lines, skipped, generated = [], [], []
    for record in records:
        fields = record.get("fields", record) if isinstance(record, dict) else {}
        row = {our: fields.get(theirs) for theirs, our in FIELD_MAP.items()}

        beat_name = (row.get("beat") or "").strip().lower()
        line_id = (row.get("id") or "").strip()
        if not line_id:
            # Generated rather than refused. A Line ID is bookkeeping, and
            # making someone invent a unique string by hand before their new
            # line can exist is exactly the friction this table should not have.
            # Derived from the line text, so the same line always gets the same
            # id and re-syncing does not churn it.
            digest = hashlib.sha256(
                f"{beat_name}|{(row.get('line') or '').strip()}".encode()
            ).hexdigest()[:6]
            line_id = f"{beat_name or 'line'}-{digest}"
            generated.append(f"{line_id} (auto, no Line ID given)")
        # Airtable OMITS an unchecked checkbox from `fields`, so an unticked
        # Active arrives as absent, not False — and `is False` never fired.
        # Unchecking a line to retire it did nothing at all, and the line kept
        # being dealt. Absent now means inactive, which is also the safer
        # default: a row that does not say it is live is not dealt.
        if not _truthy_active(row.get("active")):
            skipped.append(f"{line_id}: Active unchecked")
            continue

        lines.append({
            "id": line_id,
            "beat": beat_name,
            "line": (row.get("line") or "").strip(),
            "meta": {
                "coach_type": (row.get("coach_type") or "").strip(),
                "sells_to": (row.get("sells_to") or "").strip(),
                "shape": (row.get("shape") or "").strip(),
                "claim": (row.get("claim") or "").strip(),
                "weight": str(row.get("weight") or "").strip(),
            },
        })

    # Sorted by (beat, id), always. Airtable returns records in whatever order
    # its view happens to be in, and `draw_identity` indexes into the list — so
    # without a canonical order, the same lead draws a DIFFERENT line depending
    # on which source the bank was loaded from, and "deterministic" quietly
    # becomes false. Caught by round-tripping the committed CSVs through a live
    # fetch and diffing.
    lines.sort(key=lambda l: (l["beat"], l["id"]))
    return lines, skipped + generated


def _check_weights(lines: list[dict], beat: str) -> list[str]:
    """A weight is a non-negative number, or blank for an equal share.

    There is deliberately nothing else to get wrong. The gap-and-overlap class
    of failure disappeared with the ranges it belonged to: shares are derived
    from weights at load time, so they always sum to one.
    """
    problems = []
    positive = 0
    for line in lines:
        raw = str(line["meta"].get("weight", "") or "").strip()
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            problems.append(f"{beat} line {line['id']}: weight {raw!r} is not a number")
            continue
        if value < 0:
            problems.append(f"{beat} line {line['id']}: weight {value} is negative")
        elif value > 0:
            positive += 1

    if positive and positive != len([l for l in lines if str(l["meta"].get("weight", "") or "").strip()]):
        pass  # mixed blank and set is fine: blanks simply score zero share
    return problems


from outbound.lint import MIN_HOOK_WORDS  # noqa: E402  (one home for the floor)

BEATS = ("identity", "offer", "cta", "ps")


def _check_hook_room(lines: list[dict]) -> list[str]:
    """Every line must be dealable in SOME combination that leaves a hook room.

    This used to test the worst case — the longest line in each beat, summed —
    and reject the whole bank when those four collided. That was the wrong
    question, and it made length a copy problem: the only way to satisfy it was
    to trim a good sentence until it read like a robot wrote it, to fix a
    collision the allocator had no reason to ever hand anybody.

    The allocator now refuses to deal a combination with no room for a hook
    (`anchors._resolve_length`), the same way it already refuses to deal a
    combination that repeats a phrase. So the worst case is not a thing that
    ships, and the bank does not need to be short enough to survive it.

    What is still worth failing on is a line that can never be dealt at all:
    one long enough that even paired with the shortest line in every other beat
    it leaves no hook. That is dead copy — it sits in the table looking live,
    draws a weight, and silently never reaches a reader. Same failure `ps-01`
    had under the echo rule, found the same way.

    Feasibility per line does not prove the allocator can satisfy a whole batch
    at once; nothing here claims it does. `deal` reports what it actually had
    to move, and an email that still comes out long is refused by the linter.
    Fail-closed in both directions.
    """
    from outbound import lint

    shortest = {}
    for beat in BEATS:
        beat_lines = [l for l in lines if l["beat"] == beat]
        if not beat_lines:
            return []                        # a missing beat is already reported
        shortest[beat] = min(beat_lines, key=lambda l: lint.word_count(l["line"]))

    problems = []
    for line in sorted(lines, key=lambda l: (l["beat"], l["id"])):
        if line["beat"] not in BEATS:
            continue
        # The most room this line can possibly get: the shortest line in each
        # of the other three beats.
        best = {b: (line["line"] if b == line["beat"] else shortest[b]["line"])
                for b in BEATS}
        room = lint.hook_room(best)
        if room >= MIN_HOOK_WORDS:
            continue
        partners = " + ".join(f"{shortest[b]['id']} ({lint.word_count(shortest[b]['line'])}w)"
                              for b in BEATS if b != line["beat"])
        problems.append(
            f"{line['beat']} line {line['id']} ({lint.word_count(line['line'])}w) "
            f"can never be dealt: even with the shortest line in every other "
            f"beat ({partners}) it leaves {room} word{'' if room == 1 else 's'} "
            f"for the hook, and a hook needs {MIN_HOOK_WORDS}")
    return problems


def _check_claim(line: dict, facts) -> list[str]:
    """Rule A: an identity line must declare a Claim, the Claim must resolve,
    and the line must satisfy it.

    The same `check_identity_claim` the drafted email gets, run against the
    hand-written line at sync time. That is the point: a bank line that cannot
    pass its own claim condemns every email dealt it, and the drafter is then
    asked to satisfy something impossible with one rewrite pass.

    Caught two live lines on its first run. `id-fit-2` said "closed AED 36k in 6
    weeks" against a Fitness row whose close_period is 45 days, and `id-any-4`
    counted "the last 4 coaches", which is not a count of anything. Both had
    been shipping.

    Hard-fail rather than warn. A blocked line costs one person one minute with
    the line in front of them, which is the cheapest possible place to pay, and
    copy-sync output is mostly green so a warning here is one nobody reads.
    """
    from outbound import anchors, lint

    line_id = line["id"]
    raw = (line["meta"].get("claim") or "").strip()
    if not raw:
        return [f"{line_id}: no Claim. An identity line with no Claim is a line "
                f"whose figures nothing checks — name the results.csv row and "
                f"columns it draws from, e.g. Business:meetings,period,clients"]
    try:
        spec = anchors.claim_for(anchors.Line(line_id, line["line"], {"claim": raw}), facts)
    except anchors.ClaimError as exc:
        return [f"{line_id}: {exc}"]
    return [f"{line_id}: {problem}" for problem in
            lint.check_identity_claim(line["line"], spec)]


# Rule B. A totaliser governing the meetings asserts a property of ALL of them,
# and that property has to come from somewhere.
_TOTALISER_RE = re.compile(
    r"\b(all|every one|every single|each one|each of them)\b", re.I)


def _check_totaliser(line: dict) -> list[str]:
    """Rule B: a claim about every meeting needs a column behind it.

    `id-lead-1` shipped "8 meetings in 30 days, all with prospects ready to say
    yes" — a sales-desk flourish asserting prospect intent, which nothing in
    this operation measures. Rule A cannot see it, because it carries no figure.

    The qualifier vocabulary rather than a phrase blocklist, because the naive
    version of this rule kills three good lines: `id-biz-2`, `id-exec-1` and
    `id-lead-4` all said "every one with somebody who could sign off", and two
    of them are backed by their row's `sells_to = corporates`.

    Be honest about how weak this is. It is a heuristic over English. It will
    flag a future totaliser backed by evidence not yet in the vocabulary — the
    fix being one commit adding the entry, or a reword. It will MISS any
    flourish phrased without a totaliser ("prospects who were already looking").
    And it cannot judge truth, only sourcing. It is the weakest check in this
    file and it still earns its place, because the thing it catches went out to
    real people.
    """
    from outbound import anchors

    match = _TOTALISER_RE.search(line["line"])
    if not match:
        return []
    raw = (line["meta"].get("claim") or "").strip()
    try:
        qualifier = anchors.parse_claim(raw).qualifier if raw else ""
    except anchors.ClaimError:
        return []            # Rule A already reported the unreadable Claim
    if qualifier:
        return []
    return [f'{line["id"]}: "{match.group(0)}" claims something about every '
            f"meeting, and the Claim names no qualifier that a column backs. "
            f"Either declare one (+{'/+'.join(sorted(anchors.CLAIM_QUALIFIERS))}) "
            f"or drop the clause — a property of the meetings that no column "
            f"records is a flourish, and it reads as one"]


def validate(lines: list[dict], facts=None) -> list[str]:
    """Everything that must hold before a line is allowed to draw."""
    from audit.draft_lint import EM_DASH
    from outbound import anchors, lint

    facts = facts or anchors.load_facts()
    widened = anchors.all_numbers(facts)
    problems: list[str] = []

    seen: dict[str, str] = {}
    for line in lines:
        line_id, beat, text = line["id"], line["beat"], line["line"]

        if line_id in seen:
            problems.append(f"duplicate Line ID {line_id}")
        seen[line_id] = beat

        if beat not in BEATS:
            problems.append(f"{line_id}: Beat {beat!r} is not one of {BEATS}")
        if not text:
            problems.append(f"{line_id}: Line is empty")
            continue

        if EM_DASH in text:
            problems.append(f"{line_id}: em-dash in the line")
        for message in lint.check_numbers(text, widened):
            problems.append(f"{line_id}: {message}")
        for message in lint.check_attribution(text, facts):
            problems.append(f"{line_id}: {message}")

        # An offer/cta/ps line must carry its own beat's claim tokens. Those
        # beats are re-voiced lightly or not at all, so a line missing a claim
        # is a line that can never ship: `check_claims` will reject every email
        # it is dealt to, and the drafting model would have to INVENT the
        # missing promise to get past it. Found live — `cta-02` made no "why
        # these ten" claim at all and `b4-04` never said "names", so between
        # them they silently condemned a share of every batch.
        #
        # Identity is excluded on purpose: its bridge rule is the model's job by
        # design, and 22 of 31 identity lines open on a bare stat that the model
        # is expected to turn toward the reader.
        if beat in lint.CLAIM_TOKENS and beat != "identity":
            for label, pattern in lint.CLAIM_TOKENS[beat]:
                if not pattern.search(text):
                    problems.append(
                        f"{line_id}: makes no {label!r} claim, so every email "
                        f"dealt this line fails the lint")

        # "No gendered pronoun in an identity line" is a copy rule, not a
        # re-voicing task, and it is a one-word fix at the source. Eight of the
        # thirty-one live identity lines carried "her" or "him", so a quarter of
        # the identity bank could not ship as written and every drafter dealt
        # one had to notice and silently rewrite it. The bridge rule stays the
        # model's job; this one belongs to the line.
        if beat == "identity":
            for message in lint.check_identity_pronouns(text):
                problems.append(f"{line_id}: {message}")

        if beat == "identity":
            coach_type = line["meta"].get("coach_type", "")
            sells_to = line["meta"].get("sells_to", "")
            if coach_type not in COACH_TYPES:
                problems.append(f"{line_id}: Coach Type {coach_type!r} is not a segment")
            if sells_to not in SELLS_TO:
                problems.append(f"{line_id}: Sells To {sells_to!r} is not valid")
            problems.extend(_check_claim(line, facts))
            problems.extend(_check_totaliser(line))

    for beat in BEATS:
        if not [l for l in lines if l["beat"] == beat]:
            problems.append(f"no {beat} lines at all — every email needs one")

    for beat in WEIGHTED_BEATS:
        beat_lines = [l for l in lines if l["beat"] == beat]
        if beat_lines:
            problems.extend(_check_weights(beat_lines, beat))

    problems.extend(_check_hook_room(lines))

    identity = [l for l in lines if l["beat"] == "identity"]
    if identity and not [l for l in identity if l["meta"].get("coach_type") == "Any"]:
        problems.append(
            "no generic (Coach Type = Any) identity line — it is the fallback "
            "for every lead whose segment is unknown, and without it they draw "
            "from an empty pool"
        )

    return problems


# CSV column order per beat, matching the committed files exactly so a
# regenerated file diffs cleanly against a hand-edited one.
# `weight` is on EVERY beat, identity included. It was omitted from identity on
# the assumption that identity is matched on segment rather than weighted — but
# `anchors.weight_of` reads it for any line, and the Airtable field accepts it,
# so a weight set on an identity line survived into the live bank and the
# snapshot and vanished from the regenerated CSV. That is a bank whose draw
# depends on which rung of the three-source ladder answered, which is the exact
# failure the canonical id sort was added to kill.
CSV_COLUMNS = {
    "identity": ["id", "coach_type", "sells_to", "shape", "claim", "weight",
                 "line", "word_count"],
    "offer": ["id", "line", "weight", "word_count"],
    "cta": ["id", "line", "weight", "word_count"],
    "ps": ["id", "line", "weight", "word_count"],
}


def _row_for(line: dict, beat: str) -> dict:
    """One CSV row. `word_count` is always computed, never carried.

    It used to be a field someone typed into Airtable, which meant it could
    disagree with the line sitting next to it and nothing would notice. It is a
    function of the line, so it is derived here.
    """
    meta = line["meta"]
    word_count = str(len(line["line"].split()))
    if beat == "identity":
        # `weight` is in CSV_COLUMNS above and was NOT being written — the
        # column was added and the writer was not, so DictWriter filled it with
        # its blank default on every row. An identity weight set in Airtable
        # survived into the live bank and the snapshot and vanished from the
        # CSVs, which is a bank whose draw depends on which rung of the source
        # ladder answered. That is precisely what the comment above CSV_COLUMNS
        # says this column was added to stop.
        return {
            "id": line["id"], "coach_type": meta.get("coach_type", ""),
            "sells_to": meta.get("sells_to", "") or "any",
            "shape": meta.get("shape", ""),
            "claim": meta.get("claim", ""),
            "weight": str(meta.get("weight", "") or "").strip(),
            "line": line["line"], "word_count": word_count,
        }
    return {
        "id": line["id"], "line": line["line"],
        "weight": str(meta.get("weight", "") or "").strip(),
        "word_count": word_count,
    }


def render_csv(lines: list[dict], beat: str) -> str:
    """One beat's CSV as text, exactly as `write_csvs` would write it.

    Split out from the writer so `check` can compare a committed file against
    what Airtable says without writing anything. A comparison that had to write
    first would be a check with a side effect, which is the one thing a check
    must not have.
    """
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS[beat],
                            lineterminator="\r\n")
    writer.writeheader()
    for line in [l for l in lines if l["beat"] == beat]:
        writer.writerow(_row_for(line, beat))
    return buffer.getvalue()


def write_csvs(lines: list[dict], copy_dir: Path | None = None) -> list[str]:
    """Regenerate copy/*.csv so the committed fallback never drifts."""
    copy_dir = copy_dir or COPY_DIR
    written = []
    for beat in BEATS:
        if not [l for l in lines if l["beat"] == beat]:
            continue
        path = copy_dir / f"{beat}.csv"
        with open(path, "w", newline="", encoding="utf-8") as handle:
            handle.write(render_csv(lines, beat))
        written.append(str(path))
    return written


def write_snapshot(lines: list[dict], source: str,
                   path: Path | None = None) -> str:
    path = path or SNAPSHOT
    path.write_text(json.dumps({
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "lines": lines,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def load_snapshot(path: Path | None = None) -> list[dict] | None:
    path = path or SNAPSHOT
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("lines") or None
    except (json.JSONDecodeError, OSError):
        return None


def snapshot_meta(path: Path | None = None) -> dict | None:
    """When the snapshot was written, and from which path in.

    Separate from `load_snapshot` because a warning needs the date and the draw
    needs the lines, and a caller that wanted the date used to have to re-read
    and re-parse the file itself.
    """
    path = path or SNAPSHOT
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return {"synced_at": payload.get("synced_at", ""),
            "source": payload.get("source", ""),
            "lines": len(payload.get("lines") or [])}


def sync(records: list[dict], *, source: str = "mcp",
         write: bool = True, copy_dir: Path | None = None) -> SyncResult:
    """Validate, then write. Nothing is written if anything fails."""
    lines, skipped = normalize_records(records)
    result = SyncResult(lines=lines, skipped=skipped)
    result.problems = validate(lines)

    if result.ok and write:
        write_snapshot(lines, source, (copy_dir or COPY_DIR) / "_airtable.json")
        write_csvs(lines, copy_dir)
    return result


# ------------------------------------------------------------------- the check


@dataclass
class CheckResult:
    """Whether the copy a batch would draw is the copy Airtable holds."""
    live: int = 0                       # active lines the table returned
    problems: list[str] = field(default_factory=list)   # lint failures, live
    drift: list[str] = field(default_factory=list)      # cache != table
    blocked: str = ""                   # could not run at all, with the reason
    snapshot: bool = False              # a snapshot exists and was compared

    @property
    def exit_code(self) -> int:
        if self.blocked:
            return 2
        return 1 if (self.problems or self.drift) else 0

    def report(self) -> str:
        if self.blocked:
            return (f"COPY-CHECK: BLOCKED — {self.blocked}\n"
                    f"  A check that cannot run is not a pass. Set "
                    f"AIRTABLE_API_KEY, or accept that this batch draws from "
                    f"the committed cache and say so.")
        if self.exit_code == 0:
            cached = ("copy/*.csv and copy/_airtable.json match it"
                      if self.snapshot else
                      "copy/*.csv match it (no snapshot on disk, which is "
                      "normal — it is gitignored)")
            return (f"COPY-CHECK: PASS — {self.live} live line(s) from Copy "
                    f"Assets; {cached}")
        out = [f"COPY-CHECK: FAIL — {len(self.problems)} lint problem(s), "
               f"{len(self.drift)} drift(s) against the live table"]
        for problem in self.problems:
            out.append(f"  LINT  {problem}")
        for item in self.drift:
            out.append(f"  DRIFT {item}")
        if self.drift and not self.problems:
            out.append("  Fix: python main.py copy-sync --live, then commit "
                       "copy/*.csv")
        if self.problems:
            out.append("  Fix: correct the line in Airtable. Nothing here can "
                       "fix it, and nothing should: the table is the authority.")
        return "\n".join(out)


def check(copy_dir: Path | None = None) -> CheckResult:
    """Assert that Airtable is what a batch would actually draw from.

    The three ways the machine could quietly draft from stale copy, in the order
    they matter:

    1. **The live lines fail the lint.** Airtable is reachable, somebody's edit
       is live there, and `anchors.CopyBank.load` refuses it and falls through
       to the cache. The edit looks applied and is not. Exit 1.
    2. **The cache disagrees with the table.** Everything works today and the
       first run without a key silently drafts from month-old lines. Exit 1,
       fixed by `copy-sync --live`.
    3. **Nothing could be fetched.** No key, no network, or the bank is pinned
       offline. Exit 2 — a check that cannot run is a failure, never a pass.

    It never writes. `copy-sync` is the thing that writes; this only reports,
    so it is safe to run at the top of a batch and again after a fix.
    """
    import os

    from audit import airtable

    copy_dir = copy_dir or COPY_DIR
    result = CheckResult()

    forced = os.environ.get("OUTBOUND_COPY_SOURCE", "").strip().lower()
    if forced in ("csv", "snapshot"):
        result.blocked = (f"OUTBOUND_COPY_SOURCE={forced} pins the copy bank "
                          f"offline, so there is nothing to compare against")
        return result
    if not airtable.available():
        result.blocked = ("no AIRTABLE_API_KEY, so the live Copy Assets table "
                          "cannot be read")
        return result

    try:
        records = airtable.copy_assets()
    except Exception as exc:
        result.blocked = f"{type(exc).__name__}: {exc}"
        return result

    lines, _ = normalize_records(records)
    result.live = len(lines)
    if not lines:
        # Never a pass. An authority that answers "nothing" reading as "the
        # cache is fine" is the same failure as an unreadable dedupe wall
        # reading as "nobody has been contacted".
        result.problems = ["Copy Assets returned no active lines — every row is "
                           "unchecked, or the table is empty"]
        return result

    result.problems = validate(lines)
    if result.problems:
        # The cache comparison is meaningless while the table is unshippable:
        # `copy-sync` would refuse to write anyway, so reporting drift here
        # would name a second fix that does not exist.
        return result

    for beat in BEATS:
        path = copy_dir / f"{beat}.csv"
        expected = render_csv(lines, beat)
        try:
            # `newline=""` disables universal-newline translation. Without it
            # every committed file read back with `\n` against a rendering with
            # `\r\n` and all four beats reported drift with zero rows edited.
            with path.open(newline="", encoding="utf-8-sig") as handle:
                actual = handle.read()
        except OSError as exc:
            result.drift.append(f"copy/{beat}.csv: cannot read it ({exc})")
            continue
        if actual != expected:
            result.drift.append(
                f"copy/{beat}.csv differs from Copy Assets "
                f"({_row_delta(actual, expected)})")

    # A MISSING snapshot is not drift. It is gitignored, so a fresh clone never
    # has one and a run with no key falls to the committed CSVs — which the
    # loop above just proved match the table. Only a snapshot that exists and
    # disagrees is a problem, because that one is what actually gets drawn from.
    snapshot = load_snapshot(copy_dir / "_airtable.json")
    result.snapshot = snapshot is not None
    if snapshot is not None and snapshot != lines:
        meta = snapshot_meta(copy_dir / "_airtable.json") or {}
        result.drift.append(
            f"copy/_airtable.json differs from Copy Assets (synced "
            f"{meta.get('synced_at') or 'unknown'}, {len(snapshot)} line(s) "
            f"against {len(lines)} live)")
    return result


def _row_delta(actual: str, expected: str) -> str:
    """A one-phrase description of how two renderings of a beat differ.

    Enough to tell "a line was edited" from "a line was added" without printing
    a diff nobody asked for; `copy-sync --live` is the fix either way.
    """
    left = [r for r in actual.splitlines() if r.strip()]
    right = [r for r in expected.splitlines() if r.strip()]
    if not left:
        return "the cached file is empty"
    if len(left) != len(right):
        # Row counts exclude the header, which both renderings always carry.
        return f"{len(left) - 1} row(s) cached against {len(right) - 1} live"
    changed = sum(1 for a, b in zip(left, right) if a != b)
    return f"{changed} row(s) edited"
