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
        # NOT ps-01 ("not a list"): the offer beat says "Not a scraped
        # list", and check_echo rejects that pair.
        "ps": "ps: a no here costs you nothing and costs me nothing.",
    }


def draft(slug="sarah", name="Sarah Khan", subject="your Hashimoto post",
          identity=None):
    body = export.assemble_body(beats(identity), greeting_name=name.split()[0])
    return export.Draft(
        slug=slug, name=name, first_name=name.split()[0],
        last_name=name.split()[-1], email=f"{slug}@site.ae",
        subject=subject, body=body, beats=beats(identity),
        anchor_ids={"identity": "id-health-2", "offer": "b4-01",
                    "cta": "cta-01", "ps": "ps-03"},
        coach_type="Health", sells_to="individuals", city="Dubai",
        website="https://sarahcoaching.ae",
        linkedin_url="https://linkedin.com/in/sarah")


def lint_all(drafts):
    # Keyed by email, matching `write_batch`. Keying by slug is the collision
    # bug: two coaches both called "Sarah Ahmed" share one slug.
    return {d.email: lint.check_email(name=d.name, subject=d.subject, body=d.body,
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
        assert rows[0]["first_name"] == "Sarah"
        assert rows[0]["location"] == "Dubai"
        assert "15 minutes" in rows[0]["body"]


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
        assert [r["email"] for r in rows] == ["good@site.ae"]


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


def test_the_upload_file_is_exactly_the_agreed_columns():
    """Eight, in this order. Adding an analytical column here would create a
    Smartlead custom field that never gets used and clutters every lead view;
    that data belongs in Airtable, where it can be grouped and filtered."""
    assert export.COLUMNS == [
        "email", "first_name", "last_name", "website",
        "linkedin_profile", "location", "subject", "body",
    ]


def test_the_linkedin_column_uses_smartleads_own_field_name():
    """`linkedin_profile`, per Smartlead's API reference. `linkedin_url` still
    imports, which is exactly why it needs pinning: it lands as a custom
    variable instead of the native LinkedIn column, and nothing says so."""
    assert "linkedin_profile" in export.COLUMNS
    assert "linkedin_url" not in export.COLUMNS


def test_no_analytical_column_leaks_into_the_upload_file():
    for column in ("coach_type", "sells_to", "hook_type", "hook_source_url",
                   "identity_line_id", "slug", "batch", "company"):
        assert column not in export.COLUMNS, column


def test_a_lead_with_no_linkedin_still_writes_a_row():
    """"linkedin (if present)" — absent is an empty cell, never a dropped row."""
    with tempfile.TemporaryDirectory() as tmp:
        d = draft()
        d.linkedin_url = ""
        out = export.write_batch([d], lint_all([d]), out_dir=tmp)
        assert out["written"] == 1
        rows = list(csv.DictReader(open(Path(tmp) / "leads.csv", encoding="utf-8")))
        assert rows[0]["linkedin_profile"] == ""


# ----------------------------------------------------------------- the wall


def test_wall_additions_are_written_but_not_applied():
    """Nothing has been sent at export time. Walling a lead who never received
    anything would silently exclude her from every future batch."""
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp)
        rows = list(csv.DictReader(
            open(Path(tmp) / "wall-additions.csv", encoding="utf-8")))
        assert len(rows) == 1
        assert rows[0]["name"] == "Sarah Khan"
        assert rows[0]["warm"] == "no"
        assert rows[0]["track"] == "Outbound"
        assert out["wall_additions"].endswith("wall-additions.csv")


def test_a_rejected_lead_never_reaches_the_wall_additions():
    """She got no email, so she must stay eligible for the next batch."""
    with tempfile.TemporaryDirectory() as tmp:
        good = draft("good", "Good Coach")
        bad = draft("bad", "Bad Coach", subject="second subject",
                    identity="9 meetings in 6 weeks for a health coach in Dubai.")
        export.write_batch([good, bad], lint_all([good, bad]), out_dir=tmp)
        rows = list(csv.DictReader(
            open(Path(tmp) / "wall-additions.csv", encoding="utf-8")))
        assert [r["name"] for r in rows] == ["Good Coach"]


def test_the_wall_row_carries_a_registrable_domain():
    d = draft()
    d.website = "https://www.sarahcoaching.ae/about"
    assert d.wall_row()["domain"] == "sarahcoaching.ae"


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


# ------------------------------------------------------- anchor drift


def dealt_for(drafts):
    return {d.email: {beat: {"id": d.anchor_ids[beat], "line": "x"}
                      for beat in ("identity", "offer", "cta", "ps")}
            for d in drafts}


def test_a_draft_matching_the_deal_is_written():
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp,
                                 dealt=dealt_for(drafts))
        assert out["written"] == 1


def test_a_drafter_that_drew_its_own_line_is_rejected():
    """The failure this catches is invisible in the email: the drafter runs
    `main.py anchors` instead of using the dealt line, gets the single-lead
    draw, and silently undoes the batch balancing while the CRM records a line
    the reader never saw."""
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        dealt = dealt_for(drafts)
        dealt[drafts[0].email]["offer"]["id"] = "b4-99"
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp, dealt=dealt)
        assert out["written"] == 0 and out["rejected"] == 1
        assert "drew its own" in Path(tmp, "rejected.txt").read_text()


def test_a_lead_absent_from_the_deal_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp, dealt={})
        assert out["written"] == 0
        assert "not in the batch deal" in Path(tmp, "rejected.txt").read_text()


def test_without_a_deal_the_check_is_skipped_not_failed():
    """`outbound-draft` writes one email with no batch behind it."""
    with tempfile.TemporaryDirectory() as tmp:
        drafts = [draft()]
        out = export.write_batch(drafts, lint_all(drafts), out_dir=tmp)
        assert out["written"] == 1


def test_a_reported_id_that_disagrees_with_the_written_text_is_caught():
    """The id is self-reported. A drafter can name the assigned line and write a
    different one — the email reads fine, and the usage counts plus the CRM row
    then describe an email nobody received."""
    with tempfile.TemporaryDirectory() as tmp:
        bank = anchors.CopyBank.from_csv()
        assigned, other = bank.offer[0], bank.offer[1]
        d = draft()
        d.anchor_ids["offer"] = assigned.id
        d.beats = dict(d.beats)
        d.beats["offer"] = other.line          # wrong line, right id
        d.body = export.assemble_body(d.beats, greeting_name="Sarah")
        dealt = dealt_for([d])
        dealt[d.email]["offer"]["id"] = assigned.id
        out = export.write_batch([d], lint_all([d]), out_dir=tmp,
                                 dealt=dealt, bank=bank)
        assert out["written"] == 0, "wrong line shipped"
        assert "disagree" in Path(tmp, "rejected.txt").read_text()


def test_revoicing_the_assigned_line_is_still_allowed():
    """Re-voicing is the whole design. Only a verbatim match to a DIFFERENT
    line is evidence of the wrong line."""
    with tempfile.TemporaryDirectory() as tmp:
        bank = anchors.CopyBank.from_csv()
        d = draft()
        d.anchor_ids["offer"] = bank.offer[0].id
        dealt = dealt_for([d])
        dealt[d.email]["offer"]["id"] = bank.offer[0].id
        out = export.write_batch([d], lint_all([d]), out_dir=tmp,
                                 dealt=dealt, bank=bank)
        assert out["written"] == 1, Path(tmp, "rejected.txt").read_text()


def test_two_coaches_with_the_same_name_do_not_share_one_verdict():
    """`slug` comes from the NAME, so two different women both called "Sarah
    Ahmed" collapse to one key and whichever draft is processed last overwrites
    the other's lint verdict — in either direction. Here the broken one is
    second, so slug keying would hand the clean verdict to the failing email
    and write it into leads.csv."""
    with tempfile.TemporaryDirectory() as tmp:
        clean = draft(slug="sarah", name="Sarah Ahmed")
        broken = draft(slug="sarah", name="Sarah Ahmed")
        broken.email = "sarah@othersite.ae"          # a different person
        broken.beats = dict(broken.beats)
        broken.beats["identity"] = ("My job is finding your next client. A "
                                    "coach here closed AED 91,500 from "
                                    "prospects I put in front of them.")
        broken.body = export.assemble_body(broken.beats, greeting_name="Sarah")

        assert clean.slug == broken.slug, "the collision this test is about"
        assert clean.email != broken.email

        out = export.write_batch([clean, broken], lint_all([clean, broken]),
                                 out_dir=tmp)
        rows = list(csv.DictReader(open(Path(tmp) / "leads.csv", encoding="utf-8")))
        assert [r["email"] for r in rows] == ["sarah@site.ae"]
        assert out["written"] == 1 and out["rejected"] == 1


def test_a_draft_with_no_lint_entry_is_refused_not_written():
    """The other half of the same rule: an unlinted draft must never ship on
    the assumption that a missing entry means nothing was wrong."""
    with tempfile.TemporaryDirectory() as tmp:
        d = draft()
        out = export.write_batch([d], {}, out_dir=tmp)
        assert out["written"] == 0
        assert "never linted" in Path(tmp, "rejected.txt").read_text()


def test_an_invented_address_is_flagged_but_not_dropped():
    """Three of eleven drafting workers on the first real batch returned an
    address that did not exist, because their return block asked for one. The
    block no longer asks; this is the belt. It WARNS rather than rejects,
    because the obvious rule kills real people: cheryl@cherylnankoo.com against
    a site of thenankoo.com is one person with two domains, which is ordinary."""
    with tempfile.TemporaryDirectory() as tmp:
        d = draft()
        d.email = "sarah@somewhere-else.ae"
        d.website = "https://sarahcoaching.ae"
        out = export.write_batch([d], {d.email: lint_all([d])[d.email]}, out_dir=tmp)
        assert out["written"] == 1, "a domain mismatch must not drop a lead"
        assert "check it is really theirs" in out["report"]


def test_a_free_provider_address_never_warns():
    with tempfile.TemporaryDirectory() as tmp:
        d = draft()
        d.email = "sarah@gmail.com"
        d.website = "https://sarahcoaching.ae"
        out = export.write_batch([d], {d.email: lint_all([d])[d.email]}, out_dir=tmp)
        assert out["written"] == 1
        assert "check it is really theirs" not in out["report"]


def test_a_missing_or_malformed_address_is_fatal():
    """The one address failure that IS unambiguous: there is nothing to send to."""
    for bad in ("", "not-an-address"):
        with tempfile.TemporaryDirectory() as tmp:
            d = draft()
            d.email = bad
            out = export.write_batch([d], {bad: None}, out_dir=tmp)
            assert out["written"] == 0, repr(bad)
            assert out["rejected"] == 1, repr(bad)


def test_a_hook_type_airtable_would_reject_is_flagged():
    """Caught here rather than at the CRM write, which happens AFTER the email
    is in the upload file — at which point the row is missing from the CRM and
    the lead ships anyway with nothing recording that it did."""
    with tempfile.TemporaryDirectory() as tmp:
        d = draft()
        d.hook_type = "about_page"
        out = export.write_batch([d], lint_all([d]), out_dir=tmp)
        assert out["written"] == 1, "a CRM enum is bookkeeping, not a reason to drop"
        assert "WORK/LIFE/METRIC" in out["report"]


def test_a_valid_hook_type_is_silent():
    with tempfile.TemporaryDirectory() as tmp:
        for good in ("WORK", "LIFE", "METRIC", ""):
            d = draft()
            d.hook_type = good
            out = export.write_batch([d], lint_all([d]), out_dir=tmp)
            assert "Airtable will reject" not in out["report"], repr(good)


def test_the_crm_enums_match_the_live_base():
    """These mirror the base schema. If someone edits an option in Airtable and
    not here, the write fails at the CRM step with the email already sent."""
    from audit import airtable
    assert airtable.HOOK_TYPES == ("WORK", "LIFE", "METRIC")
    assert airtable.SELLS_TO == ("corporates", "individuals")
    assert "Held" in airtable.LEAD_STATUSES


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
