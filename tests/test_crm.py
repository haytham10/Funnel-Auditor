"""The Leads row, and the two ways the hand-written version of it went wrong.

Run: python -m pytest tests/test_crm.py -q
 or: python tests/test_crm.py

Twenty rows went into the CRM on `2026-08-01-q1` with **no First Name, Last
Name, Website, LinkedIn or City on any of them**. They were built from
`work/researched.json` — the research workers' typed output, which has never
carried the intake identity fields; those live on the normalized `Lead`. A
`if v not in (None, "")` filter dropped every empty key before the request, so
there was no error and no warning.

Then the check that "verified" it counted Name, Status, Hook Verified and
Blockers, saw 20/20, and reported the push as cross-checked. **Those are four
fields somebody expected to be populated.** A verification that only looks where
you expect to find something is the writer certifying its own work with extra
steps, which is the one thing this machine's chassis exists to prevent.

Both halves are tested here: the join fails closed, and coverage is reported for
every field rather than the ones anybody thought to check.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

from outbound import crm


def lead(**overrides) -> dict:
    row = {"name": "Nadia Karim", "first_name": "Nadia", "last_name": "Karim",
           "email": "n@x.ae", "site_url": "https://x.ae",
           "linkedin_url": "https://linkedin.com/in/nadia", "city": "Dubai",
           "slug": "nadia-karim"}
    row.update(overrides)
    return row


def research(**overrides) -> dict:
    row = {"name": "Nadia Karim", "email": "n@x.ae",
           "uae_based": "yes", "uae_based_source": "About page names Dubai",
           "is_coach": "yes", "is_coach_source": "About page",
           "active_recent": "unclear", "active_recent_source": "",
           "coach_type": "Business", "sells_to": "individuals", "solo": "yes",
           "email_status": "pass", "hook_verified": "verified",
           "hook": "You wrote that the plan held all the way to the run",
           "hook_type": "WORK", "hook_source_url": "https://x.ae/about",
           "hook_quote": "the plan held all the way to the run",
           "hook_date": "2026-07-20"}
    row.update(overrides)
    return row


def draft(**overrides) -> dict:
    row = {"email": "n@x.ae", "subject": "the plan held",
           "body": "Hey Nadia,\n\nYou wrote the plan finally held.",
           "beats": {"hook": "You wrote the plan finally held."},
           "anchor_ids": {"identity": "id-any-6", "offer": "b4-01"}}
    row.update(overrides)
    return row


# --------------------------------------------------------------------- the join


def test_a_research_object_with_no_lead_behind_it_fails_closed():
    """The defect itself. Building the row anyway is what produced twenty rows
    with five empty columns and no error — the identity fields are not on the
    research object and never have been."""
    built = crm.build([], [research()])
    assert not built.ok
    assert built.rows == []
    assert any("no normalized lead" in p for p in built.problems)
    assert any("First Name" in p for p in built.problems), \
        "it has to name the columns that would have gone in blank"


def test_the_join_pulls_the_identity_fields_off_the_lead():
    built = crm.build([lead()], [research()])
    assert built.ok, built.problems
    row = built.rows[0]
    assert row["First Name"] == "Nadia"
    assert row["Website"] == "https://x.ae"
    assert row["City"] == "Dubai"


def test_a_lead_with_no_key_cannot_be_joined_and_says_so():
    built = crm.build([lead()], [research(email="", slug="")])
    assert not built.ok
    assert any("neither email nor slug" in p for p in built.problems)


# ----------------------------------------------------------------- the coverage


def test_every_field_is_counted_including_the_ones_nobody_expects():
    """The other half. A check that looked at four populated fields called
    twenty broken rows verified, so the report shows all of them — a field
    empty on every row is named whether or not it is required."""
    built = crm.build([lead()], [research()])
    assert "Instagram" in built.coverage and built.coverage["Instagram"] == 0
    assert built.coverage["First Name"] == 1
    text = built.report()
    assert "EMPTY Instagram" in text
    assert "First Name" in text


def test_an_empty_field_is_written_rather_than_filtered_out():
    """The push that went wrong dropped empty keys before the request, so a
    field that should have carried a name and did not was indistinguishable
    from a field nobody meant to send."""
    row = crm.build([lead(city="")], [research()]).rows[0]
    assert "City" in row and row["City"] == ""


def test_a_zero_is_not_reported_as_automatically_wrong():
    """`Instagram 0/20` was correct on that batch and `First Name 0/20` was the
    bug. Only a reader comparing against the source list can tell, so the report
    says so rather than implying a verdict."""
    text = crm.build([lead()], [research()]).report()
    assert "not automatically wrong" in text


# ------------------------------------------------------------------- the values


def test_a_required_field_arriving_empty_is_a_failure():
    built = crm.build([lead(name="")], [research(name="")])
    assert not built.ok
    assert any("Name is empty" in p for p in built.problems)


def test_the_required_list_stays_short_enough_not_to_fail_true_rows():
    """The source CSV carried 11 cities for 20 rows, `Sells To` is collected
    from their own words and never inferred, and Subject/Body exist only for the
    leads that shipped. A longer list fails closed on true rows, which teaches
    people to pass a flag that turns the check off."""
    assert set(crm.REQUIRED) == {"Name", "Email", "Status"}
    built = crm.build([lead(city="", linkedin_url="")],
                      [research(sells_to="", coach_type="")])
    assert built.ok, built.problems


def test_a_value_outside_a_select_is_caught_before_airtable_rejects_it():
    """The write happens AFTER the email is in the upload file, so a rejected
    row means a lead shipped with nothing recording that it did."""
    built = crm.build([lead()], [research(coach_type="Wellness")])
    assert not built.ok
    assert any("Coach Type" in p and "Wellness" in p for p in built.problems)


# --------------------------------------------------------------------- the hook


def test_an_exported_row_records_the_hook_that_shipped():
    """Three of five rows on `2026-08-01-q1` had a `Hook` field naming a
    sentence the reader never saw: it carried the verifier-certified proposal
    while `Body` carried the drafter's rewrite. That is a CRM row describing an
    email nobody received — the failure `export --anchors` catches, one field
    over."""
    row = crm.build([lead()], [research()], [draft()]).rows[0]
    assert row["Hook"] == "You wrote the plan finally held."
    assert row["Hook"] in row["Body"]


def test_the_certified_wording_moves_to_notes_rather_than_being_lost():
    row = crm.build([lead()], [research()], [draft()]).rows[0]
    assert "certified quote" in row["Notes"]
    assert "the plan held all the way to the run" in row["Notes"]
    assert "as proposed before drafting" in row["Notes"]


def test_a_held_lead_still_gets_a_row_with_its_blocker():
    """A lead that vanished with no record is worse than a kill you can read."""
    built = crm.build([lead()], [research(hook_verified="refuted")])
    row = built.rows[0]
    assert row["Status"] == "Drafted" or row["Status"] == "Qualified"
    assert "no verified hook" in row["Blockers"]


def test_a_disqualified_lead_is_disqualified_and_names_the_floor():
    built = crm.build([lead()], [research(
        uae_based="no", uae_based_source="About names Dunbar, Scotland")])
    row = built.rows[0]
    assert row["Status"] == "Disqualified"
    assert row["Failed Floors"] == ["Not UAE-based"]
    assert row["Qualified"] is False
    assert "Dunbar" in row["Evidence"], "a verdict carries the source that settled it"


def test_the_batch_is_reported_and_never_put_in_a_row():
    """`Batch` is a linked-record field. Its value is a Batches record id that
    does not exist until that row is created, so a label here would fail the
    write on every row."""
    built = crm.build([lead()], [research()], batch="2026-08-01-q1")
    assert "Batch" not in built.rows[0]
    assert "2026-08-01-q1" in built.report()


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
