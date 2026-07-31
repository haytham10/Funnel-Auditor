"""The upload file, and what it refuses to write.

Run: python -m pytest tests/test_export.py -q
 or: python tests/test_export.py

One rule carries most of these: a lead whose lint failed does not appear in
leads.csv. Not flagged in a column, not marked for review — absent. A failing
email sitting in an upload file is an email that gets sent by accident, and the
whole point of ending the machine at a file is that the file is trustworthy.
"""

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import anchors, export, lint

FACTS = anchors.load_facts()
ALLOWED = anchors.all_numbers(FACTS)


def beats(identity=None):
    return {
        "hook": ("You wrote that you couldn't contain the excitement of "
                 "uncovering a solution for yourself."),
        "identity": identity or (
            "My job is finding your next client. A health coach in Dubai "
            "closed AED 78,000 over 2 months from prospects I put in front "
            "of them."),
        "offer": ("I pulled 10 names for you before writing this. Not a "
                  "scraped list, people I'd actually start with."),
        "cta": ("15 minutes and they're yours the same day. I'll tell you why "
                "these 10 and not the other 40."),
        "ps": "ps: not a list. If the timing's wrong that's a fine answer.",
    }


def draft(slug="sarah", name="Sarah Khan", subject="your Hashimoto post",
          identity=None):
    body = export.assemble_body(beats(identity), greeting_name=name.split()[0])
    return export.Draft(
        slug=slug, name=name, first_name=name.split()[0], email=f"{slug}@site.ae",
        subject=subject, body=body, beats=beats(identity),
        anchor_ids={"identity": "id-health-2", "offer": "b4-01",
                    "cta": "cta-01", "ps": "ps-01"},
        coach_type="Health", sells_to="individuals", city="Dubai")


def lint_all(drafts):
    return {d.slug: lint.check_email(name=d.name, subject=d.subject, body=d.body,
                                     beats=d.beats, allowed_numbers=ALLOWED,
                                     facts=FACTS)
            for d in drafts}


# ------------------------------------------------------------------- assembly


def test_the_body_keeps_the_beat_order():
    body = export.assemble_body(beats(), greeting_name="Sarah")
    positions = [body.index(beats()[b][:20])
                 for b in ("hook", "identity", "offer", "cta")]
    assert positions == sorted(positions)


def test_the_sign_off_sits_before_the_ps():
    body = export.assemble_body(beats(), greeting_name="Sarah")
    assert body.index("\nHaytham") < body.index("ps:")


def test_a_missing_beat_does_not_leave_a_blank_gap():
    body = export.assemble_body({**beats(), "ps": ""}, greeting_name="Sarah")
    assert not body.endswith("\n\n")
    assert body.rstrip().endswith("Haytham")


# --------------------------------------------------------------------- writing


def test_a_passing_draft_is_written():
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp,
                                 batch="2026-07-31")
        assert out["written"] == 1
        rows = list(csv.DictReader(open(Path(tmp) / "leads.csv", encoding="utf-8")))
        assert len(rows) == 1
        assert rows[0]["email"] == "sarah@site.ae"
        assert "15 minutes" in rows[0]["body"]
        assert rows[0]["batch"] == "2026-07-31"


def test_a_failing_draft_is_absent_from_the_csv():
    """The rule that matters. Not a flag in a column — absent."""
    with tempfile.TemporaryDirectory() as tmp:
        good, bad = draft("good", "Good Coach"), draft(
            "bad", "Bad Coach", subject="second subject",
            identity="9 meetings in 6 weeks for a health coach in Dubai.")
        drafts = [good, bad]
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp)
        assert out["written"] == 1 and out["rejected"] == 1
        rows = list(csv.DictReader(open(Path(tmp) / "leads.csv", encoding="utf-8")))
        assert [r["slug"] for r in rows] == ["good"]


def test_an_unlinted_draft_is_refused():
    """Absence of a verdict is not a pass. A draft that was never checked is
    treated exactly like one that failed."""
    with tempfile.TemporaryDirectory() as tmp:
        out = export.write_batch([draft()], {}, out_dir=tmp)
        assert out["written"] == 0
        assert "never linted" in Path(tmp, "rejected.txt").read_text()


def test_rejections_are_written_with_their_reasons():
    with tempfile.TemporaryDirectory() as tmp:
        bad = draft("bad", identity="9 meetings in 6 weeks for a health coach.")
        export.write_batch([bad], lint_all([bad]), out_dir=tmp)
        text = Path(tmp, "rejected.txt").read_text()
        assert "Sarah Khan" in text and "turns to the reader" in text


def test_a_failing_batch_check_blocks_the_whole_file():
    """Every batch-level failure is about the set. Writing "most of it" would
    not fix the thing that failed."""
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft("a", "A Coach"), draft("b", "B Coach")]
        batch_result = lint.check_batch(
            [{"subject": d.subject, "body": d.body, "beats": d.beats} for d in drafts])
        assert not batch_result.passed, "identical subjects should fail the batch"
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp,
                                 batch_result=batch_result)
        assert out["blocked"]
        assert not Path(tmp, "leads.csv").exists()


def test_the_report_points_at_the_preview():
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp)
        assert "READ" in out["report"] and "preview.txt" in out["report"]


def test_every_column_is_present_even_when_empty():
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        export.write_batch(drafts, lint_all(drafts), out_dir=tmp)
        with open(Path(tmp) / "leads.csv", encoding="utf-8") as handle:
            assert next(csv.reader(handle)) == export.COLUMNS


def test_subject_and_body_are_the_only_content_columns():
    """Smartlead stitches nothing. The beats ride along for analysis, but what
    sends is one assembled subject and one assembled body."""
    assert "subject" in export.COLUMNS and "body" in export.COLUMNS
    assert not any(c in export.COLUMNS for c in ("hook", "identity", "offer", "cta"))


# --------------------------------------------------------------------- preview


def test_the_preview_shows_the_whole_email():
    text = export.preview([draft()])
    assert "Subject: your Hashimoto post" in text
    assert "15 minutes" in text and "Haytham" in text


def test_the_preview_names_the_drawn_lines():
    assert "id-health-2" in export.preview([draft()])


def test_an_empty_batch_writes_nothing_and_does_not_crash():
    with tempfile.TemporaryDirectory() as tmp:
        out = export.write_batch([], {}, out_dir=tmp)
        assert out["written"] == 0 and not out["blocked"]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
