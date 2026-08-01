"""The ledger: what a retrieval cost, and whether we paid for it twice.

Run: python -m pytest tests/test_ledger.py -q
 or: python tests/test_ledger.py

Three behaviours here are the opposite of what the rest of this repo does, and
each is pinned because the obvious "fix" would undo the reason it exists.

`append` never raises. Every other check fails closed; an observer that can halt
the run it is observing is worse than no observer, and P0 of the retrieval
proposal is defined as changing no behaviour. So a broken ledger loses lines and
nothing else.

A *missing* ledger is exit 2. Same asymmetry as the dedupe wall — a missing wall
must never read as "nobody has been contacted", a missing ledger must never read
as "this batch cost nothing".

A verify may re-fetch. The duplicate check exists to catch the research stage and
the hook stage paying twice for the same LinkedIn profile; the verifier's second
fetch of the same URL is the product, not the defect, and exempting it is the
whole reason `purpose` is on the record at all.
"""

import json
import os
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Standalone runs get no conftest, so redirect the ledger before anything can
# append a test line to the repo's real record of what a batch cost.
os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

from outbound import ledger

BATCH = "test-batch"


def entry(**overrides) -> ledger.Retrieval:
    fields = {"lead_key": "a@b.com", "stage": "research", "platform": "linkedin",
              "url": "https://linkedin.com/in/x", "retrieved_by": "apify:li_posts",
              "cost_usd": 0.01, "secs": 4.0, "outcome": "ok", "purpose": "observe"}
    fields.update(overrides)
    return ledger.Retrieval(**fields)


# ------------------------------------------------------------ write and read


def test_a_retrieval_round_trips_as_one_json_line():
    with tempfile.TemporaryDirectory() as tmp:
        assert ledger.append(entry(), batch=BATCH, root=tmp)
        raw = ledger.path(BATCH, tmp).read_text(encoding="utf-8")
        assert raw.count("\n") == 1, "one record is one line, never pretty-printed"
        records, malformed = ledger.read(BATCH, tmp)
        assert malformed == 0
        assert records[0].url == "https://linkedin.com/in/x"
        assert records[0].cost_usd == 0.01


def test_append_stamps_the_time_it_happened():
    """Written as the run proceeds, so a batch that dies in stage 3 still
    leaves its accounting — which needs each line to say when it landed."""
    with tempfile.TemporaryDirectory() as tmp:
        ledger.append(entry(), batch=BATCH, root=tmp)
        records, _ = ledger.read(BATCH, tmp)
        assert records[0].at, "a record with no time cannot be ordered"


def test_append_never_raises_when_it_cannot_write():
    """The one fail-open in this repo. A ledger write must not be able to kill
    a batch that was otherwise going to ship, so a failure is a False return
    and nothing else."""
    with tempfile.TemporaryDirectory() as tmp:
        blocked = Path(tmp) / "wall"
        blocked.write_text("not a directory", encoding="utf-8")
        assert ledger.append(entry(), batch=BATCH, root=blocked) is False


def test_concurrent_appends_do_not_interleave():
    """`batch_fetch` reads eight sites at a time. A half-written line from one
    thread inside another's would corrupt both, and the ledger would be least
    trustworthy on exactly the biggest batches."""
    with tempfile.TemporaryDirectory() as tmp:
        def write(i):
            ledger.append(entry(url=f"https://x/{i}"), batch=BATCH, root=tmp)

        threads = [threading.Thread(target=write, args=(i,)) for i in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        records, malformed = ledger.read(BATCH, tmp)
        assert malformed == 0, "a torn line means the lock is not holding"
        assert len({r.url for r in records}) == 40


def test_a_half_written_line_does_not_lose_the_rest():
    """A run killed mid-append legitimately leaves a partial last line. Losing
    the other 400 records to it would defeat writing them as we go."""
    with tempfile.TemporaryDirectory() as tmp:
        ledger.append(entry(), batch=BATCH, root=tmp)
        with ledger.path(BATCH, tmp).open("a", encoding="utf-8") as handle:
            handle.write('{"lead_key": "b@c.com", "url": "htt')
        records, malformed = ledger.read(BATCH, tmp)
        assert len(records) == 1
        assert malformed == 1


def test_a_missing_ledger_is_unreadable_not_empty():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            ledger.read("never-ran", tmp)
        except ledger.LedgerUnreadable as exc:
            assert "zero-cost" in str(exc)
        else:
            raise AssertionError("a missing ledger must not read as no spend")


# ------------------------------------------------------------- the invariant


def test_the_same_page_fetched_twice_is_a_duplicate():
    """F1: research-worker and hook-worker both run li-posts on the same
    profile. li_posts is the one actor that provably cannot be batched, so this
    is the single most expensive call in the machine, made twice."""
    records = [entry(stage="research"), entry(stage="hook")]
    found = ledger.duplicates(records)
    assert len(found) == 1
    assert found[0]["url"] == "https://linkedin.com/in/x"
    assert "research" in found[0]["first"] and "hook" in found[0]["again"]


def test_a_verifier_refetching_the_same_page_is_not_a_duplicate():
    """The verifier reading the cache instead of the page would be certifying
    that we copied a string correctly, not that the words are on the page. Its
    second fetch is the product."""
    records = [entry(stage="research"), entry(stage="verify", purpose="verify")]
    assert ledger.duplicates(records) == []


def test_two_leads_on_the_same_url_are_not_a_duplicate():
    """The unit is (lead, source), not source. Two coaches at one agency's
    site is two retrievals of two different things."""
    records = [entry(lead_key="a@b.com"), entry(lead_key="c@d.com")]
    assert ledger.duplicates(records) == []


def test_a_search_query_counts_as_a_source():
    """`google_search` has no fetched URL, so the query goes in under a
    `google:` prefix. Running the same query twice for one lead is exactly the
    waste this is looking for, so it must not be exempt for lacking a scheme."""
    records = [entry(url="google:jane coach dubai", platform="web"),
               entry(url="google:jane coach dubai", platform="web")]
    assert len(ledger.duplicates(records)) == 1


# ---------------------------------------------------------------- the report


def test_the_report_names_what_could_not_be_priced():
    """A compute-billed actor is unpriceable on purpose — the cost gate's own
    distinction. Folding that into $0.00 would report the two site crawlers as
    free, which is the most expensive thing this machine can ask for."""
    records = [entry(cost_usd=None, retrieved_by="apify:site_render")]
    line = ledger.report(records, batch=BATCH)
    assert "could not be priced" in line
    assert "compute-billed" in line


def test_the_report_names_a_run_the_cost_gate_refused():
    """A batch that quietly stopped at the threshold looks identical, in every
    other record this machine keeps, to a batch that found nothing."""
    line = ledger.report([entry(outcome="blocked", cost_usd=0.4)], batch=BATCH)
    assert "BLOCKED" in line


def test_cost_per_lead_uses_the_batch_size_not_the_fetched_count():
    """Nine leads of ten needing no paid call is the good outcome. Dividing the
    bill by the one that did would report ten times the real cost per lead."""
    line = ledger.report([entry(cost_usd=0.10)], batch=BATCH, leads=10)
    assert "$0.0100/lead" in line, line


def test_a_clean_batch_says_so_rather_than_printing_nothing():
    """An absent DUPLICATE line and a checked-and-clean one look identical to a
    reader. Saying it is what makes the check quotable."""
    line = ledger.report([entry()], batch=BATCH)
    assert "no duplicate fetch" in line


def test_the_summary_totals_cost_and_time_by_source():
    records = [entry(retrieved_by="tier0", cost_usd=0.0, secs=1.0),
               entry(retrieved_by="apify:li_posts", cost_usd=0.02, secs=9.0,
                     url="https://linkedin.com/in/y")]
    stats = ledger.summarise(records)
    assert stats["cost_usd"] == 0.02
    assert stats["secs"] == 10.0
    assert stats["by_source"]["apify:li_posts"]["n"] == 1
    assert stats["by_source"]["tier0"]["cost_usd"] == 0.0


# --------------------------------------------------------------- the context


def test_the_caller_outranks_the_ambient_context():
    """The context is a default, not an override. A stage label set once at the
    top of a command would otherwise outrank the truth at the call site."""
    with tempfile.TemporaryDirectory() as tmp:
        ledger.clear_context()
        ledger.set_context(lead_key="a@b.com", stage="research")
        try:
            ledger.record(batch=BATCH, root=tmp, stage="verify",
                          url="https://x/1", retrieved_by="webfetch")
            records, _ = ledger.read(BATCH, tmp)
            assert records[0].lead_key == "a@b.com", "context fills what is unset"
            assert records[0].stage == "verify", "the call site wins"
        finally:
            ledger.clear_context()


def test_a_blank_context_value_does_not_erase_one_already_set():
    ledger.clear_context()
    try:
        ledger.set_context(lead_key="a@b.com")
        ledger.set_context(lead_key="")
        assert ledger.get_context()["lead_key"] == "a@b.com"
    finally:
        ledger.clear_context()


def test_the_batch_label_defaults_to_the_environment_then_today():
    saved = os.environ.pop("OUTBOUND_BATCH", None)
    try:
        assert ledger.batch_label("explicit") == "explicit"
        os.environ["OUTBOUND_BATCH"] = "from-env"
        assert ledger.batch_label() == "from-env"
        del os.environ["OUTBOUND_BATCH"]
        from datetime import date
        assert ledger.batch_label() == date.today().isoformat()
    finally:
        if saved is not None:
            os.environ["OUTBOUND_BATCH"] = saved


def test_the_ledger_root_can_be_redirected_out_of_the_repo():
    """What keeps a test run out of the record of what a real batch cost."""
    saved = os.environ.get("OUTBOUND_LEDGER_ROOT")
    try:
        os.environ["OUTBOUND_LEDGER_ROOT"] = "/somewhere/else"
        assert ledger.path("b") == Path("/somewhere/else/data/runs/b.jsonl")
    finally:
        if saved is not None:
            os.environ["OUTBOUND_LEDGER_ROOT"] = saved


def test_an_unknown_field_in_a_stored_line_is_ignored():
    """The ledger is append-only and lives across versions. A line written by a
    future field must not crash a reader that predates it."""
    with tempfile.TemporaryDirectory() as tmp:
        target = ledger.path(BATCH, tmp)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"url": "https://x/1", "rung": 4}) + "\n",
                          encoding="utf-8")
        records, malformed = ledger.read(BATCH, tmp)
        assert malformed == 0
        assert records[0].url == "https://x/1"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)
