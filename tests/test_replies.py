"""The Smartlead join — the one bridge to data this repo does not own.

Run: python -m pytest tests/test_replies.py -q

Nothing here has ever seen a real Smartlead export, which is exactly why these
tests are written the way they are. The property they protect: **a column this
could not identify must never produce a zero reply rate.** A zero would read as
"the campaign did nothing" when the truth is "the question could not be asked",
and that is the dedupe wall's asymmetry in a third costume.

The second property: a pre-filtered export (every row IS a reply) and a full
export whose reply column went unrecognised look identical and differ by the
whole answer. That is never guessed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from outbound import replies as rep


SENT = [
    {"email": "a@x.ae", "hook_type": "WORK",
     "hook_source_url": "https://linkedin.com/posts/a-1"},
    {"email": "b@x.ae", "hook_type": "LIFE",
     "hook_source_url": "https://bcoach.ae/about"},
]


# ------------------------------------------------------- identifying columns


def test_the_common_header_spellings_are_found():
    for header in ("Email", "lead_email", "Lead Email", "email_address",
                   "Prospect Email", "recipient"):
        assert rep.find_column([header, "Campaign"], rep.EMAIL_HEADERS) == header


def test_an_exact_match_beats_a_substring():
    """A file carrying both `email` and `email_body` must pick the address, not
    the body."""
    assert rep.find_column(["email_body", "email"], rep.EMAIL_HEADERS) == "email"


def test_an_unfindable_email_column_names_the_headers_it_saw():
    """Readable failure, not a traceback and not a zero."""
    with pytest.raises(rep.RepliesUnreadable) as exc:
        rep.load_export("prospect,outcome\na@x.ae,7\n")
    assert "prospect" in str(exc.value) and "outcome" in str(exc.value)
    assert "--email-column" in str(exc.value)


def test_an_unfindable_reply_column_refuses_rather_than_assuming():
    """**The second property.** A pre-filtered file and an unrecognised column
    are indistinguishable, and guessing between them is the difference between a
    6% reply rate and a 100% one."""
    with pytest.raises(rep.RepliesUnreadable) as exc:
        rep.load_export("email,first_name\na@x.ae,Amina\n")
    assert "--all-replied" in str(exc.value)
    assert "differ by the whole answer" in str(exc.value)


def test_all_replied_is_the_way_a_filtered_export_is_read():
    out = rep.load_export("email,first_name\na@x.ae,Amina\n", all_replied=True)
    assert out["replies"] == {"a@x.ae": True}
    assert "pre-filtered" in out["replied_column"]


def test_an_override_beats_the_sniff():
    out = rep.load_export("prospect,outcome\na@x.ae,replied\n",
                          email_column="prospect", replied_column="outcome")
    assert out["replies"] == {"a@x.ae": True}


# ------------------------------------------------------------ reading a cell


def test_an_empty_cell_is_never_a_reply():
    """The common encoding for "no event yet"."""
    for blank in ("", "   ", "0", "false", "No", "none", "-"):
        assert rep.is_reply(blank)[0] is False


def test_the_known_affirmatives_are_replies():
    for yes in ("REPLIED", "Replied", "reply", "responded", "true", "1"):
        assert rep.is_reply(yes)[0] is True


def test_another_status_is_not_a_reply():
    """**The bug the first cut had.** `SENT`, `OPENED` and `BOUNCED` are the
    ordinary contents of a status column, and reading them as replies inflates
    the rate of whichever hook type happened to be in front of them."""
    for other in ("SENT", "OPENED", "BOUNCED", "unsubscribed", "in_progress"):
        assert rep.is_reply(other, "status")[0] is False


def test_an_ordinary_status_is_not_reported_as_unrecognised():
    """A note that cries wolf on every run is a note nobody reads by the third
    one — which would waste the only mechanism for surfacing a spelling that
    really is a reply."""
    for ordinary in ("SENT", "opened", "Bounced", "unsubscribed"):
        assert rep.is_reply(ordinary, "status")[1] == ""
    assert rep.is_reply("WARMED", "status")[1] == "warmed"


def test_the_column_kind_decides_how_a_cell_is_read():
    assert rep.column_kind("Lead Status") == "status"
    assert rep.column_kind("replied_at") == "timestamp"
    assert rep.column_kind("reply_time") == "timestamp"
    assert rep.column_kind("reply_count") == "count"


def test_a_timestamp_column_reads_any_value_as_the_event():
    """There is no `SENT` to mistake for a reply in a column of dates."""
    assert rep.is_reply("2026-08-01T09:14:00Z", "timestamp")[0] is True
    assert rep.is_reply("", "timestamp")[0] is False


def test_a_count_column_reads_the_number():
    assert rep.is_reply("2", "count")[0] is True
    assert rep.is_reply("0", "count")[0] is False


def test_an_unrecognised_status_is_surfaced_rather_than_swallowed():
    """Counted as not-a-reply, and named — so a spelling this does not know
    reaches the person who can add it."""
    export = rep.load_export("email,status\na@x.ae,WARMED\n")
    out = rep.join(SENT, export)
    assert out.replied == 0
    assert any("unrecognised value" in n and "warmed" in n for n in out.notes)


# ------------------------------------------------------------------ the join


def test_replies_are_attributed_to_the_hook_that_earned_them():
    export = rep.load_export(
        "Lead Email,Lead Status\na@x.ae,REPLIED\nb@x.ae,SENT\n")
    out = rep.join(SENT, export, batch="demo")
    assert (out.sent, out.replied) == (2, 1)
    assert out.reply_rate == 0.5
    assert out.by_hook_type["WORK"] == {"sent": 1, "replied": 1, "rate": 1.0}
    assert out.by_hook_type["LIFE"] == {"sent": 1, "replied": 0, "rate": 0.0}
    assert out.by_rung["li_posts"]["replied"] == 1
    assert out.by_rung["about"]["replied"] == 0


def test_a_lead_listed_twice_replied_if_either_row_says_so():
    """An export with one line per sequence step is a shape this must not read
    as two leads."""
    export = rep.load_export(
        "email,status\na@x.ae,SENT\na@x.ae,REPLIED\na@x.ae,SENT\n")
    out = rep.join(SENT[:1], export)
    assert (out.sent, out.replied) == (1, 1)


def test_rows_outside_the_batch_are_named_not_counted():
    """An export covering several uploads is the expected case, not an error."""
    export = rep.load_export(
        "email,status\na@x.ae,REPLIED\nzz@other.com,REPLIED\n")
    out = rep.join(SENT, export)
    assert out.sent == 1                  # only a@ matched; b@ is not in the file
    assert out.unmatched_rows == 1
    assert out.unmatched_leads == 1
    assert any("not in this batch" in n for n in out.notes)


def test_the_report_refuses_to_draw_a_conclusion():
    """One batch is a handful of samples per bucket. The difference between
    1 of 1 and 0 of 1 is noise wearing a percentage."""
    export = rep.load_export("email,status\na@x.ae,REPLIED\n")
    text = rep.report(rep.join(SENT, export))
    assert "NOT A VERDICT" in text
    assert "accumulates" in text


def test_an_empty_export_is_unreadable_not_a_zero_reply_rate():
    with pytest.raises(rep.RepliesUnreadable):
        rep.load_export("email,status\n")
    with pytest.raises(rep.RepliesUnreadable):
        rep.load_export("email,status\n,\n")


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
