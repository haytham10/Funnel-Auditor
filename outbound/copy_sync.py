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
- **The weighted beats cover 1-100 with no gap and no overlap.** This one is
  invisible until it bites: `offer`, `cta` and `ps` are drawn by rolling 1-100
  and taking the line whose range covers the roll. A gap means some leads draw
  nothing and quietly fall through to a positional fallback; an overlap means
  the declared weights are a fiction.
- **A generic (`Any`) identity line exists.** It is the fallback for every lead
  whose segment is unknown, and without one they draw from an empty pool.

On success it writes two things: a snapshot JSON that `anchors.py` reads, and a
regenerated set of `copy/*.csv` so the committed fallback never drifts from what
Airtable says. On failure it writes nothing at all.
"""

from __future__ import annotations

import csv
import json
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
    "Roll Range": "roll_1_100",
    "Word Count": "word_count",
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


def normalize_records(records: list[dict]) -> tuple[list[dict], list[str]]:
    """Airtable records -> our line shape. Inactive rows are skipped, not failed.

    Accepts either the MCP's `{"fields": {...}}` envelope or a bare field dict,
    because the two paths into this module return different shapes and making
    the caller remember which is a bug waiting to happen.
    """
    lines, skipped = [], []
    for record in records:
        fields = record.get("fields", record) if isinstance(record, dict) else {}
        row = {our: fields.get(theirs) for theirs, our in FIELD_MAP.items()}

        line_id = (row.get("id") or "").strip()
        if not line_id:
            skipped.append("a row with no Line ID")
            continue
        if row.get("active") is False:
            skipped.append(f"{line_id}: Active unchecked")
            continue

        lines.append({
            "id": line_id,
            "beat": (row.get("beat") or "").strip().lower(),
            "line": (row.get("line") or "").strip(),
            "meta": {
                "coach_type": (row.get("coach_type") or "").strip(),
                "sells_to": (row.get("sells_to") or "").strip(),
                "shape": (row.get("shape") or "").strip(),
                "roll_1_100": (row.get("roll_1_100") or "").strip(),
                "word_count": str(row.get("word_count") or ""),
            },
        })

    # Sorted by (beat, id), always. Airtable returns records in whatever order
    # its view happens to be in, and `draw_identity` indexes into the list — so
    # without a canonical order, the same lead draws a DIFFERENT line depending
    # on which source the bank was loaded from, and "deterministic" quietly
    # becomes false. Caught by round-tripping the committed CSVs through a live
    # fetch and diffing.
    lines.sort(key=lambda l: (l["beat"], l["id"]))
    return lines, skipped


def _check_ranges(lines: list[dict], beat: str) -> list[str]:
    """1-100, covered exactly once. A gap or an overlap is a silent bug."""
    spans: list[tuple[int, int, str]] = []
    problems = []
    for line in lines:
        raw = line["meta"].get("roll_1_100", "")
        if "-" not in raw:
            problems.append(f"{beat} line {line['id']} has no Roll Range")
            continue
        low, _, high = raw.partition("-")
        try:
            spans.append((int(low), int(high), line["id"]))
        except ValueError:
            problems.append(f"{beat} line {line['id']}: Roll Range {raw!r} is not a range")
    if problems:
        return problems

    covered = [0] * 101
    for low, high, line_id in spans:
        if not (1 <= low <= high <= 100):
            problems.append(f"{beat} line {line_id}: range {low}-{high} is outside 1-100")
            continue
        for value in range(low, high + 1):
            covered[value] += 1

    gaps = [v for v in range(1, 101) if covered[v] == 0]
    overlaps = [v for v in range(1, 101) if covered[v] > 1]
    if gaps:
        problems.append(
            f"{beat} roll ranges leave {len(gaps)} value(s) uncovered "
            f"(e.g. {gaps[0]}) — those leads draw nothing"
        )
    if overlaps:
        problems.append(
            f"{beat} roll ranges overlap on {len(overlaps)} value(s) "
            f"(e.g. {overlaps[0]}) — the declared weights are not real"
        )
    return problems


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

        if beat == "identity":
            coach_type = line["meta"].get("coach_type", "")
            sells_to = line["meta"].get("sells_to", "")
            if coach_type not in COACH_TYPES:
                problems.append(f"{line_id}: Coach Type {coach_type!r} is not a segment")
            if sells_to not in SELLS_TO:
                problems.append(f"{line_id}: Sells To {sells_to!r} is not valid")

    for beat in BEATS:
        if not [l for l in lines if l["beat"] == beat]:
            problems.append(f"no {beat} lines at all — every email needs one")

    for beat in WEIGHTED_BEATS:
        beat_lines = [l for l in lines if l["beat"] == beat]
        if beat_lines:
            problems.extend(_check_ranges(beat_lines, beat))

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
CSV_COLUMNS = {
    "identity": ["id", "coach_type", "sells_to", "shape", "line", "word_count"],
    "offer": ["id", "line", "weight_pct", "roll_1_100", "word_count"],
    "cta": ["id", "line", "weight_pct", "roll_1_100", "word_count"],
    "ps": ["id", "line", "weight_pct", "roll_1_100", "word_count"],
}


def _row_for(line: dict, beat: str) -> dict:
    meta = line["meta"]
    word_count = meta.get("word_count") or str(len(line["line"].split()))
    if beat == "identity":
        return {
            "id": line["id"], "coach_type": meta.get("coach_type", ""),
            "sells_to": meta.get("sells_to", "") or "any",
            "shape": meta.get("shape", ""), "line": line["line"],
            "word_count": word_count,
        }
    span = meta.get("roll_1_100", "")
    weight = ""
    if "-" in span:
        low, _, high = span.partition("-")
        weight = str(int(high) - int(low) + 1)
    return {
        "id": line["id"], "line": line["line"], "weight_pct": weight,
        "roll_1_100": span, "word_count": word_count,
    }


def write_csvs(lines: list[dict], copy_dir: Path | None = None) -> list[str]:
    """Regenerate copy/*.csv so the committed fallback never drifts."""
    copy_dir = copy_dir or COPY_DIR
    written = []
    for beat in BEATS:
        beat_lines = [l for l in lines if l["beat"] == beat]
        if not beat_lines:
            continue
        path = copy_dir / f"{beat}.csv"
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS[beat])
            writer.writeheader()
            for line in beat_lines:
                writer.writerow(_row_for(line, beat))
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
