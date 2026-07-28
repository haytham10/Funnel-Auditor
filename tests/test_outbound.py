"""Tests for outbound/main.py — the test-scale Smartlead pipeline.

Covers exactly the five things the spec asks for, and nothing else:

  1. the seeded roll is reproducible for the same email (and differs between
     emails) — this is what guarantees a re-run produces the identical email
     and that the export always matches the log.
  2. both cold-read skip rules fire: `mindset-cert-flood` on a lead who runs a
     certification, `mindset-reach-without-buyers` on a blank or sub-20,000
     audience.
  3. weighted selection lands in the right bucket across 1,000 rolls, for both
     weighted files (offer.csv and cta.csv).
  4. an empty hook renders without a double blank line — the paragraph has to
     collapse entirely, not leave a gap.
  5. dropped rows do not reach the export.

Hermetic: no network, no model calls. Tests 1-4 are pure functions. Test 5
drives the real `assemble` → `export` commands against a temporary
leads/ directory, so it exercises the actual file I/O rather than a stand-in.

Run: python -m pytest tests/test_outbound.py -q
     (or plain `python tests/test_outbound.py` for the no-pytest path)
"""

import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from outbound import main as ob


# --- helpers ---------------------------------------------------------------

@contextmanager
def temp_leads():
    """Point the module's leads/ paths at a throwaway directory, so a test run
    never touches the committed campaign files."""
    saved = (ob.LEADS_DIR, ob.RAW_CSV, ob.ENRICHED_CSV, ob.SMARTLEAD_CSV, ob.PREVIEW_TXT)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ob.LEADS_DIR = root
        ob.RAW_CSV = root / "raw.csv"
        ob.ENRICHED_CSV = root / "enriched.csv"
        ob.SMARTLEAD_CSV = root / "smartlead.csv"
        ob.PREVIEW_TXT = root / "preview.txt"
        try:
            yield root
        finally:
            (ob.LEADS_DIR, ob.RAW_CSV, ob.ENRICHED_CSV,
             ob.SMARTLEAD_CSV, ob.PREVIEW_TXT) = saved


def lead(**overrides):
    row = {c: "" for c in ob.ENRICHED_COLUMNS}
    row.update({
        "name": "Sarah Nolan",
        "email": "sarah@example.ae",
        "site_url": "https://example.ae",
        "uae_based": "yes",
        "active_30d": "yes",
        "solo": "yes",
        "coach_type": "Mindset",
    })
    row.update(overrides)
    return row


# --- 1. the seeded roll is reproducible ------------------------------------

def test_seeded_rng_is_reproducible_for_the_same_email():
    draws = lambda: [ob.seeded_rng("Sarah@Example.AE").randint(1, 100) for _ in range(5)]
    assert draws() == draws()


def test_seeded_rng_ignores_case_and_surrounding_space():
    a = ob.seeded_rng("  Sarah@Example.AE ").randint(1, 100)
    b = ob.seeded_rng("sarah@example.ae").randint(1, 100)
    assert a == b


def test_seeded_rng_differs_between_emails():
    seq = lambda email: [ob.seeded_rng(email).randint(1, 100) for _ in range(1)]
    distinct = {tuple(seq(f"lead{i}@example.ae")) for i in range(20)}
    assert len(distinct) > 1, "every lead drew the same roll — the seed is not varying"


def test_assemble_row_is_reproducible():
    copy = ob.load_copy()
    row = lead(audience_size="50000")
    assert ob.assemble_row(row, copy) == ob.assemble_row(row, copy)


# --- 2. both cold-read skip rules fire -------------------------------------

def test_cert_flood_is_skipped_for_a_certification_seller():
    cold_reads = ob.load_copy()["cold_reads"]

    kept = ob.eligible_cold_reads(cold_reads, "Mindset", "no", "50000")
    assert ob.CERT_SKIP_ID in {r["id"] for r in kept}

    skipped = ob.eligible_cold_reads(cold_reads, "Mindset", "yes", "50000")
    assert ob.CERT_SKIP_ID not in {r["id"] for r in skipped}


def test_reach_without_buyers_needs_a_genuinely_large_audience():
    cold_reads = ob.load_copy()["cold_reads"]
    ids = lambda audience: {
        r["id"] for r in ob.eligible_cold_reads(cold_reads, "Mindset", "no", audience)
    }

    assert ob.REACH_SKIP_ID not in ids(""), "blank audience must skip it"
    assert ob.REACH_SKIP_ID not in ids("19999"), "sub-threshold audience must skip it"
    assert ob.REACH_SKIP_ID in ids("20000"), "the threshold itself is eligible"
    assert ob.REACH_SKIP_ID in ids("120000")


def test_cold_reads_are_filtered_to_the_coach_type_plus_general():
    cold_reads = ob.load_copy()["cold_reads"]
    eligible = ob.eligible_cold_reads(cold_reads, "Fitness", "no", "")
    types = {r["coach_type"] for r in eligible}
    assert types == {"Fitness", "General"}


def test_other_coach_type_falls_through_to_general_only():
    copy = ob.load_copy()
    assert {r["coach_type"] for r in
            ob.eligible_cold_reads(copy["cold_reads"], "Other", "no", "")} == {"General"}
    assert {r["coach_type"] for r in
            ob.eligible_identities(copy["identity"], "Other")} == {"Any"}


# --- 3. weighted selection lands in the right bucket -----------------------

def test_weighted_selection_lands_in_the_right_bucket_across_1000_rolls():
    copy = ob.load_copy()
    for name in ("offer", "cta"):
        rows = copy[name]
        for roll in range(1, 101):
            picked = ob.weighted_pick(rows, roll)
            assert picked is not None, f"{name}: roll {roll} matched no row"
            lo, hi = ob.parse_roll_range(picked["roll_1_100"])
            assert lo <= roll <= hi, f"{name}: roll {roll} landed in {lo}-{hi}"

    # 1,000 real assembly rolls, each checked against the range it claims.
    rows = copy["offer"]
    for i in range(1000):
        roll = ob.seeded_rng(f"lead{i}@example.ae").randint(1, 100)
        lo, hi = ob.parse_roll_range(ob.weighted_pick(rows, roll)["roll_1_100"])
        assert lo <= roll <= hi


def test_weight_ranges_tile_1_to_100_without_gaps_or_overlap():
    copy = ob.load_copy()
    for name in ("offer", "cta"):
        covered = []
        for row in copy[name]:
            lo, hi = ob.parse_roll_range(row["roll_1_100"])
            covered.extend(range(lo, hi + 1))
        assert sorted(covered) == list(range(1, 101)), \
            f"{name}.csv roll_1_100 ranges do not tile 1-100 exactly"


# --- 4. an empty hook renders without a double blank line ------------------

def test_empty_hook_collapses_its_paragraph():
    row = lead(hook="", cold_read="A measured observation.", identity="Who I am.",
               offer="Ten names.", cta="Fifteen minutes.")
    rendered = ob.render_email(row)

    assert "\n\n\n" not in rendered, "empty hook left a double blank line"
    assert rendered.startswith("Subject:\n\nHey Sarah,\n\nA measured observation.")
    assert not rendered.startswith("Subject: \n"), "empty subject left a trailing space"
    assert rendered.endswith(f"{ob.SIGN_OFF}\n\n{ob.PS_LINE}")


def test_populated_hook_renders_its_own_paragraph():
    row = lead(subject="the reset", hook="Your framework caught my eye.",
               cold_read="A measured observation.", identity="Who I am.",
               offer="Ten names.", cta="Fifteen minutes.")
    rendered = ob.render_email(row)

    assert "\n\n\n" not in rendered
    assert "Hey Sarah,\n\nYour framework caught my eye.\n\nA measured observation." in rendered
    assert rendered.startswith("Subject: the reset")


# --- 5. dropped rows do not reach the export -------------------------------

def test_dropped_rows_do_not_reach_the_export():
    with temp_leads():
        ob.write_csv(ob.RAW_CSV, [
            {"name": "Sarah Nolan", "email": "sarah@example.ae", "site_url": "https://a.ae"},
            {"name": "Omar Reyes", "email": "omar@example.ae", "site_url": "https://b.ae"},
            {"name": "Lena Ito", "email": "lena@example.ae", "site_url": "https://c.ae"},
        ], ob.RAW_COLUMNS)

        rows = ob.load_leads()
        ob.apply_enrich(rows, {
            "sarah@example.ae": {"uae_based": "yes", "active_30d": "yes",
                                 "solo": "yes", "coach_type": "Business"},
            # a clear "no" on one gate is enough to drop the row
            "omar@example.ae": {"uae_based": "yes", "active_30d": "yes",
                                "solo": "no", "coach_type": "Life"},
            # "unclear" passes
            "lena@example.ae": {"uae_based": "unclear", "active_30d": "yes",
                                "solo": "unclear", "coach_type": "Fitness"},
        })
        ob.save_leads(rows)

        assert ob.cmd_assemble(_args()) == 0
        assert ob.cmd_export(_args()) == 0

        exported = ob.read_csv(ob.SMARTLEAD_CSV)
        emails = {r["email"] for r in exported}
        assert emails == {"sarah@example.ae", "lena@example.ae"}
        assert "omar@example.ae" not in emails

        # and the drop is recorded, not silent
        by_email = {r["email"]: r for r in ob.read_csv(ob.ENRICHED_CSV)}
        assert by_email["omar@example.ae"]["drop_reason"] == "gate: solo=no"
        assert by_email["sarah@example.ae"]["drop_reason"] == ""


def test_export_has_the_exact_columns_and_no_none_literals():
    with temp_leads():
        ob.write_csv(ob.RAW_CSV, [
            {"name": "Sarah Nolan", "email": "sarah@example.ae", "site_url": "https://a.ae"},
        ], ob.RAW_COLUMNS)
        rows = ob.load_leads()
        ob.apply_enrich(rows, {"sarah@example.ae": {
            "uae_based": "yes", "active_30d": "yes", "solo": "yes",
            "coach_type": "Business",
        }})
        ob.save_leads(rows)
        ob.cmd_assemble(_args())
        ob.cmd_export(_args())

        header = ob.SMARTLEAD_CSV.read_text(encoding="utf-8").splitlines()[0]
        assert header == ",".join(ob.EXPORT_COLUMNS)

        record = ob.read_csv(ob.SMARTLEAD_CSV)[0]
        assert record["firstName"] == "Sarah"
        assert record["hook"] == ""           # no hook found: empty string...
        assert "None" not in ",".join(record.values())   # ...never the literal
        assert record["cold_read"] and record["identity"]
        assert record["offer"] and record["cta"]


class _args:
    """Stand-in for the argparse namespace the commands take."""
    n = 10
    write = None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
