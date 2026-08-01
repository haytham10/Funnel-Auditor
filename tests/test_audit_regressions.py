"""The 16 findings from the adversarial correctness audit, pinned.

Run: python -m pytest tests/test_audit_regressions.py -q

Every test here corresponds to a defect that was REPRODUCED before it was
fixed, and each names the failure mode it belongs to:

  lost      a lead silently killed, dropped, or overwritten
  shipped   the wrong thing reaching a real person
  dead      a gate reporting PASS while checking nothing
  crash     a traceback on realistic input

They are grouped that way rather than by module, because that is the order
they matter in.
"""

import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit import extract
from outbound import anchors, dedupe, lint, normalize, qualify, research

TODAY = date(2026, 7, 31)


# ------------------------------------------------------------------- shipped


def test_a_blank_warm_column_does_not_beat_the_status():
    """`warm is not None` let an empty checkbox override "Reply Received" and
    mark a live thread cold. A loose name match then returns a NameEcho, which
    by design proceeds — a cold opener onto a live conversation, which this
    module calls the only send that destroys rather than wastes."""
    for blank in ("", None):
        wall = dedupe.ContactWall.from_records(
            [{"Name": "A", "Status": "Reply Received", "Warm": blank}])
        assert list(wall.by_name.values())[0].warm is True, repr(blank)


def test_a_cold_status_with_a_blank_warm_column_stays_cold():
    wall = dedupe.ContactWall.from_records(
        [{"Name": "A", "Status": "Outreach Sent", "Warm": ""}])
    assert list(wall.by_name.values())[0].warm is False


def test_a_shared_link_in_bio_host_is_not_an_identity():
    """The live wall had six rows collapsed onto three such hosts, two warm.
    It broke both ways: a new coach on linktr.ee matched Lee Harris and was
    reported "already present", so they were emailed and never walled; and any
    lead carrying stan.store hit a warm row and halted the batch."""
    for shared in ("https://linktr.ee/noura", "https://stan.store/x",
                   "https://beacons.ai/y", "https://instagram.com/z"):
        assert dedupe.domain_key(shared) == "", shared
    assert dedupe.domain_key("https://sarahcoaching.ae") == "sarahcoaching.ae"


def test_a_podcast_host_is_not_an_identity_either():
    """The same collision, latent on a second host list. `spotify.com` was not
    in the set, so `domain_key` of a Spotify show URL WAS indexed and two
    coaches with podcasts collided on the wall exactly as linktr.ee did."""
    for shared in ("https://open.spotify.com/show/abc",
                   "https://podcasts.apple.com/ae/podcast/x/id1",
                   "https://anchor.fm/sarah"):
        assert dedupe.domain_key(shared) == "", shared


def test_the_live_wall_indexes_no_shared_host():
    wall = dedupe.ContactWall.from_csv()
    for host in ("stan.store", "linktr.ee", "beacons.ai"):
        assert host not in wall.by_domain, host


def test_an_unchecked_airtable_box_actually_retires_a_line():
    """Airtable OMITS an unchecked checkbox, so `is False` never fired and
    unticking a line to retire it did nothing at all."""
    from outbound import copy_sync
    records = [
        {"fields": {"Line ID": "ps-off", "Beat": "ps", "Line": "ps: x"}},
        {"fields": {"Line ID": "ps-on", "Beat": "ps", "Line": "ps: y",
                    "Active": True}},
        {"fields": {"Line ID": "ps-no", "Beat": "ps", "Line": "ps: z",
                    "Active": False}},
    ]
    lines, _ = copy_sync.normalize_records(records)
    assert [l["id"] for l in lines] == ["ps-on"]


def test_a_blank_email_cannot_merge_two_leads_in_the_deal():
    """`deal_batch` is keyed by address and `Research.email` defaults to "".
    Three leads went in, two anchors came out, and a Health coach was left
    holding a Business identity line."""
    bank = anchors.CopyBank.from_csv()
    leads = [{"email": "", "coach_type": "Health", "sells_to": "individuals"},
             {"email": "", "coach_type": "Business", "sells_to": "corporates"}]
    try:
        anchors.deal_batch(leads, bank=bank)
    except ValueError as exc:
        assert "no email" in str(exc)
    else:
        raise AssertionError("a blank email must not be dealt")


def test_a_duplicate_email_cannot_silently_take_another_lead_s_lines():
    bank = anchors.CopyBank.from_csv()
    leads = [{"email": "a@x.com", "coach_type": "Health", "sells_to": ""},
             {"email": "a@x.com", "coach_type": "Business", "sells_to": ""}]
    try:
        anchors.deal_batch(leads, bank=bank)
    except ValueError as exc:
        assert "more than once" in str(exc)
    else:
        raise AssertionError("a duplicate address must not be dealt")


def test_an_incidental_ae_or_marina_does_not_pass_the_uae_floor():
    """".ae" was substring-matched over the whole page and the marker scan ran
    BEFORE the stated-residence check, so a Toronto coach with an aeon.co link
    passed the floor and got an identity line whose premise is the UAE."""
    assert qualify.check_uae(
        text="I am a coach based in Toronto. Read my essay at nowhere.aeon.co"
    ).value == qualify.NO
    assert qualify.check_uae(
        text="Based in London. Formerly of Marina Bay, Singapore."
    ).value == qualify.NO
    assert qualify.check_uae(domain="aeon.co").value == qualify.UNCLEAR


def test_the_neighbourhood_fix_survives_the_reordering():
    for place in ("Al Barsha", "Deira", "Mirdif", "The Greens", "DXB"):
        assert qualify.check_uae(text=f"Based in {place}.").value == qualify.YES, place


def test_a_blocked_batch_does_not_leave_the_previous_file_uploadable():
    """The outputs were written only inside `if not batch_blocked and passed`,
    so a blocked run reported "nothing written" over last run's leads.csv,
    still sitting in the same default out/ directory and still uploadable."""
    from outbound import export
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_export import draft, lint_all
    with tempfile.TemporaryDirectory() as tmp:
        first = draft()
        export.write_batch([first], lint_all([first]), out_dir=tmp)
        assert (Path(tmp) / "leads.csv").exists()
        a, b = draft("a", "A Coach"), draft("b", "B Coach")
        batch = lint.check_batch(
            [{"subject": d.subject, "body": d.body, "beats": d.beats} for d in (a, b)])
        out = export.write_batch([a, b], lint_all([a, b]), out_dir=tmp,
                                 batch_result=batch)
        assert out["blocked"]
        assert not (Path(tmp) / "leads.csv").exists()


# ---------------------------------------------------------------------- lost


def test_a_day_first_date_is_not_inverted_into_a_hard_no():
    """dateutil is month-first by default, so UAE/UK "03/07/2026" became 7
    March. `check_active` is a floor where `no` is the only thing that kills,
    and the evidence string read authoritatively."""
    seen, why = qualify.latest_activity_date(
        "Workshop held on 03/07/2026 in Dubai.", today=TODAY)
    assert seen == date(2026, 7, 3), seen
    assert qualify.check_active(last_seen=seen, today=TODAY).value == qualify.YES


def test_the_most_recent_date_survives_a_long_stale_archive():
    """Stale candidates sorted first and the list truncated at 30, and a stale
    candidate needs days_past > 7 — so a recent date always sorted after them
    and fell off the end. The floor then read the oldest date as the newest."""
    archive = "\n".join(
        f"Workshop cohort starts {n} January 2026." for n in range(1, 32))
    seen, _ = qualify.latest_activity_date(
        archive + "\nPosted 28 July 2026.", today=TODAY)
    assert seen == date(2026, 7, 28), seen


def test_ordinary_words_containing_jargon_do_not_drop_an_email():
    """The hook quotes the lead's own words, so a substring test rejected whole
    emails and named a jargon word that was never in them — which the drafter
    cannot act on, because the complaint is not true."""
    for innocent in ("Your post on optimism landed with me.",
                     "Loved your talk in the auditorium last week.",
                     "Saw you were auditioning speakers.",
                     "They moved from Detroit last year.",
                     "A holistic practice, and a specialist listener."):
        failures, _ = lint.check_voice(innocent)
        assert not [f for f in failures if "jargon" in f], innocent


def test_real_jargon_is_still_caught():
    for guilty, word in (("I ran an audit of your funnel.", "audit"),
                         ("Your conversion rate.", "conversion"),
                         ("We can leverage the pipeline.", "leverage"),
                         ("Great ROI on that CRM.", "roi")):
        failures, _ = lint.check_voice(guilty)
        assert any(word in f for f in failures if "jargon" in f), guilty


def test_ordinary_words_containing_an_echo_phrase_do_not_drop_an_email():
    """`"list" in text` fires inside realistic, specialist, listen, holistic."""
    offer = ("I pulled 10 names for you before writing this. Not a scraped "
             "list, people I'd actually start with.")
    for innocent in ("ps: a realistic no here costs you nothing.",
                     "ps: listen, if the timing's wrong that's a fine answer.",
                     "ps: a holistic no costs you nothing."):
        assert not lint.check_echo(
            {"offer": offer, "cta": "15 minutes, same day.", "ps": innocent}), innocent


def test_a_real_echo_is_still_caught():
    offer = ("I pulled 10 names for you before writing this. Not a scraped "
             "list, people I'd actually start with.")
    assert lint.check_echo({"offer": offer, "cta": "15 minutes, same day.",
                            "ps": "ps: not a list. A fine answer."})


def test_two_leads_sharing_a_company_site_get_separate_reads():
    """`batch_fetch` keyed on slug, which comes from the name and falls back to
    the domain; `partition` never dedupes on domain, so nameless rows survive
    to here and one lead's page text fed the other's qualify and hook."""
    from outbound.fetch import _read_key
    a = normalize.map_row({"Website": "https://thecoachhub.ae", "Email": "sara@x.ae"})
    b = normalize.map_row({"Website": "https://thecoachhub.ae", "Email": "mona@x.ae"})
    assert a.slug == b.slug, "the collision this test is about"
    assert _read_key(a) != _read_key(b)


# ---------------------------------------------------------------------- dead


def test_the_real_reply_rate_is_writable():
    """It was computed and then thrown away by `isinstance(n, int)`, while
    `lint._licensed` carried rounding logic that existed only to accept it."""
    facts = anchors.load_facts()
    allowed = anchors.all_numbers(facts)
    rate = round(100 * facts.total_meetings / facts.total_sent, 1)
    assert rate in allowed
    assert not lint.check_numbers(f"We ran a {rate}% reply rate.", allowed)


def test_a_segments_own_send_count_is_citable():
    """The dataclass docstring says every field is citable; `sourced` and
    `sent` were not in the set."""
    facts = anchors.load_facts()
    allowed = anchors.all_numbers(facts)
    business = facts.results["Business"]
    assert business.sent in allowed
    assert business.sourced in allowed


def test_invention_is_still_caught_after_widening_the_set():
    facts = anchors.load_facts()
    assert lint.check_numbers("closed AED 91,500", anchors.all_numbers(facts))


def test_the_subject_whitespace_check_can_actually_fire():
    """`text` was already stripped, so `text != text.strip()` was always False
    and only the ALL CAPS half of the check ran."""
    assert lint.check_subject("  ten names for you  ")
    assert lint.check_subject("TEN NAMES FOR YOU")
    assert not lint.check_subject("ten names for you")


def test_repeated_subjects_report_in_a_stable_order():
    """A set iterates in string-hash order, randomised per process, so the same
    failing batch printed its subjects differently every run — and the design
    says a skill quotes the line verbatim."""
    drafts = [{"subject": "same one", "body": "x", "beats": {}},
              {"subject": "same one", "body": "y", "beats": {}},
              {"subject": "also same", "body": "z", "beats": {}},
              {"subject": "also same", "body": "w", "beats": {}}]
    runs = {tuple(lint.check_batch(drafts).failures) for _ in range(5)}
    assert len(runs) == 1


# --------------------------------------------------------------------- crash


def test_a_json_null_from_a_worker_is_a_schema_violation_not_a_crash():
    """`source.strip()` on a null raised AttributeError, uncaught — turning a
    schema violation into what reads as a crashed gate."""
    obj = research.Research.from_dict(
        {"name": "A", "uae_based": "yes", "uae_based_source": None,
         "site_emails": None})
    problems = research.validate(obj)
    assert any("no source" in p for p in problems)
    assert isinstance(research.report(obj), str)


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
