"""An enriched list cut into the chunks a batch runs.

Run: python -m pytest tests/test_chunk.py -q
 or: python tests/test_chunk.py

Four failures this file exists to make impossible.

**The biased halving.** Resetting the alternation counter inside each stratum is
the obvious implementation, and every odd-sized stratum then hands its extra
lead to the same half. On the live 124 it produced 67/57. Two halves of
different sizes and different composition make chunk 1's yield a number that
predicts nothing, which is the entire reason for halving rather than taking the
first 62.

**The silent hold-out.** A lead the enrichment does not carry and a lead
deliberately held out look identical in the output. One is a decision and one is
a join failure, so the unjoined case exits 1 and names them.

**The unreadable enrichment read as an empty list.** The wall's asymmetry, a
third time: a file nobody could open is not a list of zero coaches. Exit 2.

**The held-out file that loads as leads.** A held-out lead is a decision, not an
input, and a file shaped like a leads file is a file somebody eventually runs.
"""

import csv
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))
os.environ.setdefault("OUTBOUND_COPY_SOURCE", "csv")

from outbound import chunk                                    # noqa: E402
from outbound.normalize import Lead                           # noqa: E402


# ------------------------------------------------------------------ fixtures

def row(email, *, status="PASS", linkedin="", instagram="", listed="",
        found="", dedupe="clear", credential="PCC", emirate="Dubai"):
    return {"Email": email, "Email status": status, "LinkedIn URL": linkedin,
            "Instagram URL": instagram, "Website (listed)": listed,
            "Website (found)": found, "Dedupe": dedupe,
            "Credential": credential, "Emirate": emirate}


def lead(email, name="A Coach"):
    return Lead(name=name, email=email, slug=name.lower().replace(" ", "-"))


def strong(n, **kw):
    """n leads that belong in the two halves, spread across strata."""
    creds = ("MCC", "PCC", "ACC")
    out = []
    for i in range(n):
        out.append(row(f"s{i}@example.com",
                       linkedin=f"https://linkedin.com/in/s{i}",
                       credential=creds[i % 3],
                       emirate="Dubai" if i % 4 else "Abu Dhabi",
                       listed="https://s.example.com" if i % 5 == 0 else "",
                       instagram="https://instagram.com/s" if i % 7 == 0 else "",
                       **kw))
    return out


# ------------------------------------------------------------------ the rules

def test_a_pass_address_and_a_linkedin_is_the_strong_pool():
    assert chunk.tier(row("a@x.com", linkedin="https://linkedin.com/in/a"))[0] \
        == "strong"


def test_a_warn_address_with_a_linkedin_is_the_weak_pool():
    name, reason = chunk.tier(
        row("a@x.com", status="WARN", linkedin="https://linkedin.com/in/a"))
    assert name == "weak"
    assert "not both" in reason


def test_a_pass_address_with_only_a_site_is_the_weak_pool():
    assert chunk.tier(row("a@x.com", listed="https://a.com"))[0] == "weak"


def test_a_dead_address_is_held_out_whatever_channels_it_has():
    name, reason = chunk.tier(
        row("a@x.com", status="FAIL", linkedin="https://linkedin.com/in/a",
            instagram="https://instagram.com/a", listed="https://a.com"))
    assert name == chunk.HELD
    assert reason == chunk.DEAD


def test_no_channel_is_held_out_even_on_a_verified_address():
    name, reason = chunk.tier(row("a@x.com"))
    assert name == chunk.HELD
    assert reason == chunk.NO_CHANNEL


def test_a_walled_lead_is_held_out_before_anything_else_is_read():
    """The wall outranks the verifier: a walled lead with a dead address reads
    as walled, because that is the reason that would still hold if the address
    were fixed."""
    name, reason = chunk.tier(
        row("a@x.com", status="FAIL", dedupe="ALREADY CONTACTED — do not send"))
    assert name == chunk.HELD
    assert reason == chunk.WALLED


def test_a_found_website_counts_as_somewhere_to_look():
    """`icf-export` writes the found site only when it is not a copy of the
    listed one. For 'is there anywhere to look' the two columns are one fact."""
    assert chunk.tier(row("a@x.com", found="https://a.com"))[0] == "weak"


# ---------------------------------------------------------------- the halving

def test_the_halves_are_equal_on_an_even_pool():
    left, right = chunk.halve(strong(124), seed=1)
    assert (len(left), len(right)) == (62, 62)


def test_the_halves_differ_by_at_most_one_on_an_odd_pool():
    left, right = chunk.halve(strong(63), seed=1)
    assert abs(len(left) - len(right)) == 1
    assert len(left) + len(right) == 63


def test_the_alternation_carries_across_strata_rather_than_resetting():
    """The regression that produced 67/57 on the live list.

    Every stratum here holds exactly one lead, so a counter that resets inside
    each stratum sends all of them to the same half. One that carries alternates.
    """
    rows = [row(f"a{i}@x.com", linkedin="https://l/in/a", credential=f"C{i}")
            for i in range(10)]
    left, right = chunk.halve(rows, seed=1)
    assert (len(left), len(right)) == (5, 5)


def test_the_halves_match_on_the_strata_they_are_balanced_for():
    left, right = chunk.halve(strong(124), seed=7)
    for column in ("Credential", "Emirate"):
        for value in {r[column] for r in strong(124)}:
            a = sum(1 for r in left if r[column] == value)
            b = sum(1 for r in right if r[column] == value)
            assert abs(a - b) <= 1, f"{column}={value} split {a}/{b}"


def test_the_same_seed_gives_the_same_two_halves():
    assert chunk.halve(strong(60), seed=3) == chunk.halve(strong(60), seed=3)


def test_a_different_seed_gives_a_different_split():
    a, _ = chunk.halve(strong(60), seed=3)
    b, _ = chunk.halve(strong(60), seed=4)
    assert [r["Email"] for r in a] != [r["Email"] for r in b]


def test_arrival_order_does_not_change_the_halves():
    """Sorted before shuffling, so the seed is the only source of order."""
    rows = strong(40)
    assert chunk.halve(rows, seed=5) == chunk.halve(list(reversed(rows)), seed=5)


# -------------------------------------------------------------------- the join

def test_every_lead_lands_in_exactly_one_group():
    rows = strong(20) + [row("h@x.com"), row("d@x.com", status="FAIL",
                                             linkedin="https://l/in/d")]
    enriched = {r["Email"]: r for r in rows}
    leads = [lead(r["Email"]) for r in rows]
    groups, reasons, unjoined = chunk.assign(leads, enriched, seed=1)
    assert not unjoined
    assert sum(len(v) for v in groups.values()) == len(rows)
    keys = [l.email for v in groups.values() for l in v]
    assert sorted(keys) == sorted(r["Email"] for r in rows)


def test_a_lead_the_enrichment_does_not_carry_is_returned_unjoined():
    enriched = {r["Email"]: r for r in strong(4)}
    leads = [lead(e) for e in [r["Email"] for r in strong(4)] + ["ghost@x.com"]]
    _, _, unjoined = chunk.assign(leads, enriched, seed=1)
    assert [l.email for l in unjoined] == ["ghost@x.com"]


def test_an_unreadable_enrichment_raises_rather_than_reading_as_empty():
    try:
        chunk.load_enriched("/nonexistent/enriched.csv")
    except chunk.ChunkError as exc:
        assert "could not read" in str(exc)
    else:
        raise AssertionError("a file nobody could open is not zero coaches")


def test_a_missing_column_names_itself():
    path = Path(tempfile.mkdtemp()) / "e.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Email", "Dedupe"])
        writer.writeheader()
        writer.writerow({"Email": "a@x.com", "Dedupe": "clear"})
    try:
        chunk.load_enriched(path)
    except chunk.ChunkError as exc:
        assert "Email status" in str(exc)
    else:
        raise AssertionError("a missing column must not tier every lead as held")


def test_an_empty_enrichment_raises():
    path = Path(tempfile.mkdtemp()) / "e.csv"
    path.write_text("Email,Dedupe\n", encoding="utf-8")
    try:
        chunk.load_enriched(path)
    except chunk.ChunkError as exc:
        assert "no rows" in str(exc)
    else:
        raise AssertionError("no rows must not read as a clean cut of nobody")


# ---------------------------------------------------------------- the held file

def test_every_held_lead_carries_a_reason():
    rows = [row("h@x.com"), row("d@x.com", status="FAIL")]
    enriched = {r["Email"]: r for r in rows}
    groups, reasons, _ = chunk.assign([lead(r["Email"]) for r in rows],
                                      enriched, seed=1)
    records = chunk.held_records(groups[chunk.HELD], reasons)
    assert len(records) == 2
    assert all(r["reason"] for r in records)


def test_the_held_file_is_not_shaped_like_a_leads_file():
    """A file that loads as leads is a file somebody eventually runs."""
    rows = [row("h@x.com")]
    enriched = {r["Email"]: r for r in rows}
    groups, reasons, _ = chunk.assign([lead("h@x.com")], enriched, seed=1)
    record = chunk.held_records(groups[chunk.HELD], reasons)[0]
    assert set(record) == {"lead_key", "name", "email", "reason"}


# ------------------------------------------------------------------ the report

def test_the_report_names_every_group_and_breaks_out_the_held_reasons():
    rows = strong(10) + [row("h@x.com"), row("d@x.com", status="FAIL")]
    enriched = {r["Email"]: r for r in rows}
    groups, reasons, _ = chunk.assign([lead(r["Email"]) for r in rows],
                                      enriched, seed=1)
    text = chunk.report(groups, reasons, enriched)
    for name in chunk.GROUPS:
        assert name in text
    assert chunk.NO_CHANNEL[:20] in text
    assert chunk.DEAD[:20] in text


def test_the_report_counts_every_lead_it_was_given():
    rows = strong(12)
    enriched = {r["Email"]: r for r in rows}
    groups, reasons, _ = chunk.assign([lead(r["Email"]) for r in rows],
                                      enriched, seed=1)
    assert chunk.report(groups, reasons, enriched).startswith("CHUNK: 12 lead(s)")


def test_write_puts_four_files_down_and_names_them():
    rows = strong(8) + [row("h@x.com")]
    enriched = {r["Email"]: r for r in rows}
    groups, reasons, _ = chunk.assign([lead(r["Email"]) for r in rows],
                                      enriched, seed=1)
    out = Path(tempfile.mkdtemp())
    written = chunk.write(groups, reasons, out, prefix="t")
    assert len(written) == 4
    assert all(Path(p).exists() for p in written)
    assert any("held-out" in p for p in written)


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
