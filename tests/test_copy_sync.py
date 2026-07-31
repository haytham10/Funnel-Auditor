"""The Airtable read path, and the gate on it.

Run: python -m pytest tests/test_copy_sync.py -q
 or: python tests/test_copy_sync.py

Airtable exists so a line can change without touching code. That is only safe
because the sync rejects a line that would fail the linter, at sync time, rather
than letting it reach a stranger's inbox two stages later. These tests are that
promise.

The live-fetch path is exercised with a stub rather than a real key: the tests
must pass on any machine, and a suite that silently skips its most consequential
path is worse than one that doesn't have it.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import anchors, copy_sync


def record(line_id, beat, line, **meta):
    """One Airtable record, in the envelope the MCP returns."""
    fields = {"Line ID": line_id, "Beat": beat, "Line": line, "Active": True}
    fields.update({
        "Coach Type": meta.get("coach_type", ""),
        "Sells To": meta.get("sells_to", ""),
        "Shape": meta.get("shape", ""),
        "Weight": meta.get("weight"),
    })
    return {"id": f"rec{line_id}", "fields": fields}


def good_set():
    """A minimal valid bank: one segment line, one Any line, full roll cover."""
    return [
        record("id-health-x", "identity",
               "Your next client is the job. A health coach in Dubai closed AED 78,000.",
               coach_type="Health", sells_to="any", shape="matched-revenue"),
        record("id-any-x", "identity",
               "Your next client is the whole job. 67 meetings and 30 signed this year.",
               coach_type="Any", sells_to="any", shape="aggregate"),
        record("b4-x", "offer", "I pulled 10 names for you before writing this.",
               weight=50),
        record("b4-y", "offer", "I already found 10 names, picked one at a time.",
               weight=100),
        record("cta-x", "cta",
               "15 minutes and they're yours the same day, plus why these 10 and not the other 40.",
               weight=100),
        record("ps-x", "ps", "ps: a no here costs you nothing.", weight=100),
    ]


# ------------------------------------------------------------------- shaping


def test_the_mcp_envelope_and_a_bare_dict_both_work():
    """The two paths into this module return different shapes, and making the
    caller remember which is a bug waiting to happen."""
    enveloped, _ = copy_sync.normalize_records(good_set())
    bare, _ = copy_sync.normalize_records([r["fields"] for r in good_set()])
    assert [l["id"] for l in enveloped] == [l["id"] for l in bare]


def test_an_inactive_row_is_skipped_not_failed():
    records = good_set()
    records[0]["fields"]["Active"] = False
    lines, skipped = copy_sync.normalize_records(records)
    assert len(lines) == len(records) - 1
    assert any("Active unchecked" in s for s in skipped)


def test_a_row_with_no_line_id_gets_one_generated():
    """A Line ID is bookkeeping. Making someone invent a unique string before
    their new line can exist is exactly the friction this table should not have."""
    records = good_set() + [{"fields": {"Beat": "ps", "Line": "ps: a costless no.",
                                        "Active": True}}]
    lines, notes = copy_sync.normalize_records(records)
    assert len(lines) == len(good_set()) + 1
    assert any("auto" in n for n in notes)
    generated = [l for l in lines if l["id"].startswith("ps-") and l["id"] != "ps-x"]
    assert len(generated) == 1


def test_a_generated_line_id_is_stable_across_syncs():
    """Derived from the text, so re-syncing does not churn it."""
    row = [{"fields": {"Beat": "ps", "Line": "ps: a costless no.", "Active": True}}]
    first, _ = copy_sync.normalize_records(row)
    again, _ = copy_sync.normalize_records(row)
    assert first[0]["id"] == again[0]["id"]


# ------------------------------------------------------------------ the gate


def test_a_clean_set_validates():
    lines, _ = copy_sync.normalize_records(good_set())
    assert copy_sync.validate(lines) == []


def test_an_invented_number_is_rejected():
    """The whole point. Edit a line in Airtable, cite a number no client result
    supports, and it never reaches an inbox."""
    records = good_set()
    records[0]["fields"]["Line"] = (
        "Your next client is the job. A health coach in Dubai closed AED 91,500.")
    lines, _ = copy_sync.normalize_records(records)
    problems = copy_sync.validate(lines)
    assert any("91,500" in p and "invented" in p for p in problems)


def test_a_relabelled_number_is_rejected():
    """120,000 is real, but it is Business's. Next to "health coach" it is a lie
    that surfaces the moment two coaches compare emails."""
    records = good_set()
    records[0]["fields"]["Line"] = (
        "Your next client is the job. A health coach in Dubai closed AED 120,000.")
    lines, _ = copy_sync.normalize_records(records)
    assert any("relabelled" in p for p in copy_sync.validate(lines))


def test_an_em_dash_is_rejected():
    records = good_set()
    records[5]["fields"]["Line"] = "ps: a no here costs you nothing — really."
    lines, _ = copy_sync.normalize_records(records)
    assert any("em-dash" in p for p in copy_sync.validate(lines))


def test_a_duplicate_line_id_is_rejected():
    records = good_set()
    records[3]["fields"]["Line ID"] = records[2]["fields"]["Line ID"]
    lines, _ = copy_sync.normalize_records(records)
    assert any("duplicate Line ID" in p for p in copy_sync.validate(lines))


def test_a_missing_beat_is_rejected():
    records = [r for r in good_set() if r["fields"]["Beat"] != "ps"]
    lines, _ = copy_sync.normalize_records(records)
    assert any("no ps lines at all" in p for p in copy_sync.validate(lines))


def test_an_unknown_beat_is_rejected():
    records = good_set()
    records[5]["fields"]["Beat"] = "postscript"
    lines, _ = copy_sync.normalize_records(records)
    assert any("is not one of" in p for p in copy_sync.validate(lines))


def test_a_bad_coach_type_is_rejected():
    records = good_set()
    records[0]["fields"]["Coach Type"] = "Wellness"
    lines, _ = copy_sync.normalize_records(records)
    assert any("is not a segment" in p for p in copy_sync.validate(lines))


# ----------------------------------------------------------------- weights


def test_a_non_numeric_weight_is_rejected():
    records = good_set()
    records[2]["fields"]["Weight"] = "lots"
    lines, _ = copy_sync.normalize_records(records)
    assert any("not a number" in p for p in copy_sync.validate(lines))


def test_a_negative_weight_is_rejected():
    records = good_set()
    records[2]["fields"]["Weight"] = -5
    lines, _ = copy_sync.normalize_records(records)
    assert any("negative" in p for p in copy_sync.validate(lines))


def test_blank_weights_are_fine():
    """Blank means an equal share. Adding a line without deciding its weight
    must not fail the sync — that was the old roll-range friction."""
    records = good_set()
    for record in records:
        record["fields"].pop("Weight", None)
    lines, _ = copy_sync.normalize_records(records)
    assert copy_sync.validate(lines) == []


def test_there_is_no_gap_or_overlap_left_to_get_wrong():
    """The whole failure class went with the ranges. Adding a fifth offer line
    used to mean renumbering the other four; now it means typing one number."""
    records = good_set() + [record("b4-z", "offer",
                                   "I already pulled 10 names, one at a time.",
                                   weight=40)]
    lines, _ = copy_sync.normalize_records(records)
    assert copy_sync.validate(lines) == []


# ------------------------------------------------------ unshippable copy lines


def test_a_cta_line_that_makes_no_why_these_ten_claim_is_rejected():
    """Found live: `cta-02` promised the 10 and a clock but never said why
    those 10. `check_claims` then rejected every email dealt that line, and
    nothing upstream knew — the line sat in Airtable silently condemning a
    share of every batch. offer/cta/ps are re-voiced lightly or not at all, so
    a claim missing from the line is a claim the model would have to invent."""
    records = good_set() + [record(
        "cta-z", "cta",
        "Give me 15 minutes this week and the 10 are in your inbox that day.",
        weight=10)]
    lines, _ = copy_sync.normalize_records(records)
    problems = copy_sync.validate(lines)
    assert any("cta-z" in p and "why these ten" in p for p in problems), problems


def test_an_offer_line_that_never_says_names_is_rejected():
    records = good_set() + [record(
        "b4-z", "offer",
        "I went and found 10 already. People here who'd be worth the meeting.",
        weight=10)]
    lines, _ = copy_sync.normalize_records(records)
    assert any("b4-z" in p and "ten names" in p for p in copy_sync.validate(lines))


def test_an_identity_line_opening_on_a_bare_stat_is_still_allowed():
    """Identity is exempt. Its bridge is the drafting model's job by design —
    22 of 31 identity lines open on a bare stat the model turns toward the
    reader, and failing them here would empty the bank."""
    records = good_set() + [record(
        "id-z", "identity",
        "9 meetings in 6 weeks for the last health coach I worked with in Dubai.",
        coach_type="Health", sells_to="any", weight=10)]
    lines, _ = copy_sync.normalize_records(records)
    assert not any("id-z" in p for p in copy_sync.validate(lines))


def test_a_line_long_enough_to_crowd_out_the_hook_is_rejected():
    """A lengthened line is invisible on its own row and only bites in
    combination. Four anchors totalling 84 words leave 11 for the hook against
    a 95-word ceiling, and the rejection then points at the draft rather than
    at the line that caused it."""
    records = good_set()
    for rec in records:
        if rec["fields"].get("Beat") == "cta":
            rec["fields"]["Line"] = " ".join(["word"] * 60)
    lines, _ = copy_sync.normalize_records(records)
    problems = copy_sync.validate(lines)
    assert any("leaving only" in p and "for the hook" in p for p in problems), problems


def test_the_live_bank_leaves_room_for_a_hook():
    """The worst case, not the average — the draw picks the combination and
    nobody gets to avoid it."""
    bank = anchors.CopyBank.from_csv()
    lines = [{"id": l.id, "beat": beat, "line": l.line, "meta": l.meta}
             for beat in ("identity", "offer", "cta", "ps")
             for l in getattr(bank, beat)]
    assert copy_sync._check_hook_room(lines) == []


# ---------------------------------------------------------- the generic fallback


def test_removing_the_last_generic_identity_line_is_rejected():
    """It is the fallback for every lead whose segment is unknown. Without one
    they draw from an empty pool, which is a crash, not a degradation."""
    records = [r for r in good_set() if r["fields"].get("Coach Type") != "Any"]
    lines, _ = copy_sync.normalize_records(records)
    assert any("generic" in p for p in copy_sync.validate(lines))


# -------------------------------------------------------------- writing


def test_the_live_copy_files_pass_their_own_gate():
    """The committed CSVs must satisfy the rules the sync enforces. If they ever
    stop, Airtable and the repo have diverged and one of them is shipping."""
    bank = anchors.CopyBank.from_csv()
    records = []
    for beat, lines in (("identity", bank.identity), ("offer", bank.offer),
                        ("cta", bank.cta), ("ps", bank.ps)):
        for line in lines:
            records.append(record(
                line.id, beat, line.line,
                coach_type=line.meta.get("coach_type", ""),
                sells_to=line.meta.get("sells_to", ""),
                shape=line.meta.get("shape", ""),
                weight=line.meta.get("weight", "")))
    lines, _ = copy_sync.normalize_records(records)
    assert copy_sync.validate(lines) == []


def test_nothing_is_written_when_validation_fails():
    """A failed sync must leave the previous good state alone."""
    with tempfile.TemporaryDirectory() as tmp:
        copy_dir = Path(tmp)
        records = good_set()
        records[0]["fields"]["Line"] = "A health coach closed AED 91,500."
        result = copy_sync.sync(records, copy_dir=copy_dir)
        assert not result.ok
        assert not list(copy_dir.iterdir())


def test_a_good_sync_writes_the_snapshot_and_the_csvs():
    with tempfile.TemporaryDirectory() as tmp:
        copy_dir = Path(tmp)
        result = copy_sync.sync(good_set(), copy_dir=copy_dir)
        assert result.ok, result.problems
        snapshot = json.loads((copy_dir / "_airtable.json").read_text())
        assert len(snapshot["lines"]) == 6
        assert snapshot["source"] == "mcp"
        for beat in ("identity", "offer", "cta", "ps"):
            assert (copy_dir / f"{beat}.csv").exists()


def test_a_dry_run_writes_nothing():
    with tempfile.TemporaryDirectory() as tmp:
        copy_dir = Path(tmp)
        result = copy_sync.sync(good_set(), copy_dir=copy_dir, write=False)
        assert result.ok
        assert not list(copy_dir.iterdir())


def test_regenerated_csvs_round_trip_back_through_the_bank():
    with tempfile.TemporaryDirectory() as tmp:
        copy_dir = Path(tmp)
        copy_sync.sync(good_set(), copy_dir=copy_dir)
        rows = (copy_dir / "offer.csv").read_text()
        assert "id,line,weight,word_count" in rows
        assert "b4-x" in rows
        # word_count is computed from the line, never carried from Airtable
        assert rows.rstrip().endswith(("9", "10", "11", "12"))


# -------------------------------------------------- the load ladder, stubbed


class _StubAirtable:
    """Stands in for `audit.airtable` so the live path is tested without a key."""

    def __init__(self, records, *, raises=False):
        self.records = records
        self.raises = raises
        self.calls = 0

    def available(self):
        return True

    def copy_assets(self):
        self.calls += 1
        if self.raises:
            raise RuntimeError("Airtable unreachable")
        return self.records


def _with_stub(monkey_env, stub):
    """Install the stub and clear the cache and the CSV pin."""
    import audit
    anchors.reset_cache()
    original = sys.modules.get("audit.airtable")
    sys.modules["audit.airtable"] = stub
    audit.airtable = stub
    monkey_env.pop("OUTBOUND_COPY_SOURCE", None)
    return original


def _restore(original, previous_source):
    import audit
    import os
    if original is not None:
        sys.modules["audit.airtable"] = original
        audit.airtable = original
    if previous_source is not None:
        os.environ["OUTBOUND_COPY_SOURCE"] = previous_source
    anchors.reset_cache()


def test_a_live_fetch_is_preferred_and_labelled():
    import os
    previous = os.environ.get("OUTBOUND_COPY_SOURCE")
    stub = _StubAirtable(good_set())
    original = _with_stub(os.environ, stub)
    try:
        bank = anchors.CopyBank.load(refresh=True)
        assert bank.source == "airtable"
        assert len(bank.identity) == 2
    finally:
        _restore(original, previous)


def test_the_bank_is_cached_so_a_batch_makes_one_request():
    """5 draws used to make 5 HTTP requests. A 200-lead batch would have made
    200 and tripped Airtable's rate limit."""
    import os
    previous = os.environ.get("OUTBOUND_COPY_SOURCE")
    stub = _StubAirtable(good_set())
    original = _with_stub(os.environ, stub)
    try:
        anchors.CopyBank.load(refresh=True)
        for i in range(20):
            anchors.draw(f"c{i}@x.ae", coach_type="Health", sells_to="any")
        assert stub.calls == 1, f"{stub.calls} requests for 20 draws"
    finally:
        _restore(original, previous)


def test_invalid_live_data_falls_through_instead_of_shipping():
    """Better a slightly stale line than an unchecked one."""
    import os
    previous = os.environ.get("OUTBOUND_COPY_SOURCE")
    bad = good_set()
    bad[0]["fields"]["Line"] = "A health coach closed AED 91,500."
    stub = _StubAirtable(bad)
    original = _with_stub(os.environ, stub)
    try:
        bank = anchors.CopyBank.load(refresh=True)
        assert bank.source != "airtable"
    finally:
        _restore(original, previous)


def test_a_dead_airtable_falls_through_rather_than_stopping_the_run():
    import os
    previous = os.environ.get("OUTBOUND_COPY_SOURCE")
    stub = _StubAirtable(good_set(), raises=True)
    original = _with_stub(os.environ, stub)
    try:
        bank = anchors.CopyBank.load(refresh=True)
        assert bank.source in ("snapshot", "csv")
        assert bank.identity, "fell through to an empty bank"
    finally:
        _restore(original, previous)


def test_forcing_csv_skips_the_network_entirely():
    import os
    previous = os.environ.get("OUTBOUND_COPY_SOURCE")
    stub = _StubAirtable(good_set())
    original = _with_stub(os.environ, stub)
    try:
        os.environ["OUTBOUND_COPY_SOURCE"] = "csv"
        bank = anchors.CopyBank.load(refresh=True)
        assert bank.source == "csv"
        assert stub.calls == 0
    finally:
        _restore(original, previous)


def test_every_source_draws_the_same_line_for_the_same_lead():
    """The bug this catches, found by round-tripping the real CSVs through a
    live fetch: Airtable returns rows in view order, `draw_identity` indexes
    into the list, so the same lead drew a DIFFERENT line depending on which
    source the bank loaded from. "Deterministic" was quietly false across
    sources while being true within one. Canonical sort-by-id fixes it, and
    this test is what keeps it fixed."""
    import os
    previous = os.environ.get("OUTBOUND_COPY_SOURCE")
    stub = _StubAirtable(good_set())
    original = _with_stub(os.environ, stub)
    try:
        anchors.CopyBank.load(refresh=True)
        from_airtable = anchors.draw("sarah@example.ae", coach_type="Health",
                                     sells_to="any")

        # The same lines, shuffled the way a different Airtable view would.
        shuffled = list(reversed(good_set()))
        stub.records = shuffled
        anchors.CopyBank.load(refresh=True)
        from_shuffled = anchors.draw("sarah@example.ae", coach_type="Health",
                                     sells_to="any")

        assert (from_airtable.identity.id == from_shuffled.identity.id
                and from_airtable.offer.id == from_shuffled.offer.id), (
            "record order changed the draw")
    finally:
        _restore(original, previous)


def test_normalize_sorts_regardless_of_input_order():
    forward, _ = copy_sync.normalize_records(good_set())
    backward, _ = copy_sync.normalize_records(list(reversed(good_set())))
    assert [l["id"] for l in forward] == [l["id"] for l in backward]


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
