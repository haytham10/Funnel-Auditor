"""Weights and the batch deal.

Run: python -m pytest tests/test_weights.py -q
 or: python tests/test_weights.py

Two changes these cover, both aimed at the same complaint: Copy Assets sat
there as an inert table with arithmetic homework attached.

**Weights replaced roll ranges.** Under ranges, adding a fifth offer line meant
renumbering the other four by hand so the spans stayed contiguous, and a slip
failed the whole sync. A weight is one number that cannot be wrong on its own,
and the gap-and-overlap failure class disappeared with the ranges.

**The batch is dealt, not rolled.** Independent per-lead hashing is unbiased in
the limit and wrong at real sizes: measured over the live offer lines, a 50-lead
batch gave one line 8% against a declared 20% and pushed another to 38%, over
the 35% repetition cap. It only converged near n=200.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import anchors, lint


def lines(*weights):
    return [anchors.Line(id=f"l-{i}", line=f"line {i}", meta={"weight": str(w)})
            for i, w in enumerate(weights)]


# --------------------------------------------------------------------- shares


def test_weights_normalise_to_one():
    assert sum(anchors.shares(lines(30, 25, 25, 20)).values()) == 1.0


def test_any_scale_means_the_same_thing():
    """30/25/25/20 and 6/5/5/4 are the same declaration."""
    a = anchors.shares(lines(30, 25, 25, 20))
    b = anchors.shares(lines(6, 5, 5, 4))
    assert [round(v, 6) for v in a.values()] == [round(v, 6) for v in b.values()]


def test_blank_weights_share_equally():
    blank = [anchors.Line(id=f"l-{i}", line="x", meta={}) for i in range(4)]
    assert set(anchors.shares(blank).values()) == {0.25}


def test_a_junk_weight_scores_zero_rather_than_crashing():
    assert anchors.weight_of(anchors.Line(id="x", line="y", meta={"weight": "lots"})) == 0.0


def test_shares_of_nothing_is_empty():
    assert anchors.shares([]) == {}


# ------------------------------------------------------------------ allocate


def test_allocation_sums_to_the_batch():
    for count in (1, 7, 10, 50, 137):
        quota = anchors.allocate(lines(30, 25, 25, 20), count)
        assert sum(quota.values()) == count, count


def test_allocation_matches_the_declared_weights():
    quota = anchors.allocate(lines(30, 25, 25, 20), 100)
    assert quota == {"l-0": 30, "l-1": 25, "l-2": 25, "l-3": 20}


def test_allocation_is_reproducible_on_ties():
    """Two lines with the same weight and one seat left: the tie breaks on id,
    so re-running a batch reproduces it."""
    first = anchors.allocate(lines(50, 50), 3)
    for _ in range(5):
        assert anchors.allocate(lines(50, 50), 3) == first


def test_a_tiny_batch_still_allocates_everyone():
    quota = anchors.allocate(lines(30, 25, 25, 20), 2)
    assert sum(quota.values()) == 2


def test_an_empty_batch_allocates_nothing():
    assert sum(anchors.allocate(lines(30, 70), 0).values()) == 0


# ---------------------------------------------------------------------- deal


def test_the_deal_gives_every_lead_exactly_one_line():
    emails = [f"c{i}@x.ae" for i in range(37)]
    dealt = anchors.deal(lines(30, 25, 25, 20), emails, "offer")
    assert len(dealt) == 37
    assert set(dealt) == set(emails)


def test_the_deal_is_reproducible():
    emails = [f"c{i}@x.ae" for i in range(20)]
    first = {k: v.id for k, v in anchors.deal(lines(30, 70), emails, "offer").items()}
    again = {k: v.id for k, v in anchors.deal(lines(30, 70), emails, "offer").items()}
    assert first == again


def test_lead_order_does_not_change_the_deal():
    """The batch is a set, not a list. Shuffling the input must not move anyone."""
    emails = [f"c{i}@x.ae" for i in range(20)]
    forward = {k: v.id for k, v in anchors.deal(lines(30, 70), emails, "offer").items()}
    backward = {k: v.id for k, v in
                anchors.deal(lines(30, 70), list(reversed(emails)), "offer").items()}
    assert forward == backward


def test_the_deal_holds_the_repetition_cap_by_construction():
    """The blind hash needed a warning after the fact. This satisfies the cap
    before anything is written."""
    bank = anchors.CopyBank.from_csv()
    for n in (10, 25, 50, 200):
        emails = [f"coach{i}@site{i}.ae" for i in range(n)]
        dealt = anchors.deal(bank.offer, emails, "offer")
        counts = {}
        for line in dealt.values():
            counts[line.id] = counts.get(line.id, 0) + 1
        worst = max(counts.values()) / n
        assert worst <= lint.FIXED_LINE_SHARE_CAP + 0.01, (n, counts)


def test_the_deal_beats_the_blind_hash_at_realistic_sizes():
    """The measurement that justified this: at n=50 the hash missed a declared
    weight by 13 points. The deal must do materially better."""
    bank = anchors.CopyBank.from_csv()
    declared = anchors.shares(bank.offer)
    emails = [f"coach{i}@site{i}.ae" for i in range(50)]

    def miss(counts):
        return max(abs(counts.get(k, 0) / 50 - v) for k, v in declared.items())

    hashed = {}
    for email in emails:
        line = anchors.draw_weighted(bank.offer, email, "offer")
        hashed[line.id] = hashed.get(line.id, 0) + 1

    dealt_counts = {}
    for line in anchors.deal(bank.offer, emails, "offer").values():
        dealt_counts[line.id] = dealt_counts.get(line.id, 0) + 1

    assert miss(dealt_counts) < miss(hashed)
    assert miss(dealt_counts) <= 0.05


def test_dealing_a_single_lead_still_works():
    dealt = anchors.deal(lines(30, 25, 25, 20), ["solo@x.ae"], "offer")
    assert len(dealt) == 1


def test_dealing_from_no_lines_is_an_error_not_a_silent_empty():
    try:
        anchors.deal([], ["a@x.ae"], "offer")
    except ValueError:
        return
    raise AssertionError("dealing from an empty pool should raise")


# ------------------------------------------------------------- the batch path


def test_deal_batch_returns_a_full_anchor_per_lead():
    leads = [{"email": f"c{i}@x.ae", "coach_type": "Health", "sells_to": "any"}
             for i in range(12)]
    dealt = anchors.deal_batch(leads)
    assert len(dealt) == 12
    for anchor in dealt.values():
        assert anchor.identity.id and anchor.offer.id and anchor.cta.id and anchor.ps.id
        assert anchor.allowed_numbers


def test_deal_batch_spreads_identity_within_a_segment():
    """A whole batch of Health coaches must not all get the same identity line."""
    leads = [{"email": f"c{i}@x.ae", "coach_type": "Health", "sells_to": "any"}
             for i in range(20)]
    drawn = {a.identity.id for a in anchors.deal_batch(leads).values()}
    assert len(drawn) > 1, drawn


def test_deal_batch_handles_mixed_segments():
    leads = [
        {"email": "a@x.ae", "coach_type": "Health", "sells_to": "any"},
        {"email": "b@x.ae", "coach_type": "Executive", "sells_to": "corporates"},
        {"email": "c@x.ae", "coach_type": "", "sells_to": ""},
    ]
    dealt = anchors.deal_batch(leads)
    assert len(dealt) == 3
    # The unknown-segment lead falls to the generic pool and carries no segment.
    assert dealt["c@x.ae"].segment == ""


def test_deal_batch_is_reproducible():
    leads = [{"email": f"c{i}@x.ae", "coach_type": "Life", "sells_to": "any"}
             for i in range(15)]
    a = {k: v.identity.id for k, v in anchors.deal_batch(leads).items()}
    b = {k: v.identity.id for k, v in anchors.deal_batch(leads).items()}
    assert a == b


# ------------------------------------------------------ the single-lead path


def test_the_single_lead_draw_still_works_off_weights():
    """`outbound-draft` has no batch to balance against, so per-lead hashing
    stays the right answer there."""
    bank = anchors.CopyBank.from_csv()
    first = anchors.draw_weighted(bank.offer, "sarah@x.ae", "offer")
    again = anchors.draw_weighted(bank.offer, "sarah@x.ae", "offer")
    assert first.id == again.id


def test_a_zero_weight_line_is_never_drawn_but_stays_in_the_table():
    """Setting a weight to 0 retires a line from the draw without deleting it —
    the same intent as unchecking Active, reachable with one number."""
    pool = lines(100, 0)
    quota = anchors.allocate(pool, 50)
    assert quota["l-1"] == 0


# ------------------------------------------------- identity: ratio vs the cap


def test_the_seventy_thirty_split_is_exact_where_content_allows():
    """One stage with per-line weights undershot to 60%: Health has 3 matched
    lines against 6 generic ones, so the generic side carried the larger
    rounding remainders and took every leftover seat. Deciding the split before
    spreading inside it makes the documented ratio true."""
    for n in (10, 20, 50):
        leads = [{"email": f"h{i}@x.ae", "coach_type": "Health",
                  "sells_to": "individuals"} for i in range(n)]
        dealt = anchors.deal_batch(leads)
        exact = sum(1 for a in dealt.values()
                    if a.identity.meta.get("coach_type") == "Health")
        assert abs(exact / n - anchors.EXACT_MATCH_RATIO) < 0.05, (n, exact)


def test_the_cap_outranks_the_ratio_when_a_segment_is_thin():
    """Executive has exactly one identity line usable for an individuals-facing
    lead. A straight 70% put that one sentence in front of 70% of the batch,
    double the cap. A weaker match beats the same sentence twice in one inbox
    pair, so the excess spills to generic."""
    for n in (10, 50):
        leads = [{"email": f"e{i}@x.ae", "coach_type": "Executive",
                  "sells_to": "individuals"} for i in range(n)]
        dealt = anchors.deal_batch(leads)
        counts = {}
        for a in dealt.values():
            counts[a.identity.id] = counts.get(a.identity.id, 0) + 1
        assert max(counts.values()) / n <= lint.FIXED_LINE_SHARE_CAP + 0.01, (n, counts)


def test_no_segment_batch_ever_breaks_the_repetition_cap():
    bank = anchors.CopyBank.from_csv()
    segments = {l.meta.get("coach_type") for l in bank.identity} - {"Any", ""}
    for segment in sorted(segments):
        for sells_to in ("individuals", "corporates"):
            leads = [{"email": f"{segment}{sells_to}{i}@x.ae",
                      "coach_type": segment, "sells_to": sells_to}
                     for i in range(25)]
            dealt = anchors.deal_batch(leads)
            counts = {}
            for a in dealt.values():
                counts[a.identity.id] = counts.get(a.identity.id, 0) + 1
            worst = max(counts.values()) / 25
            assert worst <= lint.FIXED_LINE_SHARE_CAP + 0.01, (segment, sells_to, counts)


def test_a_mixed_batch_holds_the_cap_across_segments():
    """The failure this restructure fixed: six small segment groups each dealt
    their own generic spill, independently picked the same first generic line,
    and put it in front of 42% of a 12-lead batch. The generic pool is shared,
    so it has to be dealt once across the whole batch."""
    segments = [("Health", "individuals"), ("Life", "individuals"),
                ("Executive", "corporates"), ("Business", "corporates"),
                ("Career", "individuals"), ("", "")]
    leads = []
    for index, (segment, sells_to) in enumerate(segments):
        for j in range(2):
            leads.append({"email": f"m{index}{j}@x.ae", "coach_type": segment,
                          "sells_to": sells_to})
    dealt = anchors.deal_batch(leads)
    counts = {}
    for a in dealt.values():
        counts[a.identity.id] = counts.get(a.identity.id, 0) + 1
    worst = max(counts.values()) / len(leads)
    assert worst <= lint.FIXED_LINE_SHARE_CAP + 0.01, counts


def test_thin_segments_names_what_to_write():
    """The spill keeps a batch legal; it does not fix the gap. Nobody writes
    another line unless something says the pool is too thin.

    Executive/individuals was the live instance and has since been filled, so
    this exercises the reporter on a bank built with one line in a segment."""
    bank = anchors.CopyBank.from_csv()
    one_line = [l for l in bank.identity
                if not (l.meta.get("coach_type") == "Health"
                        and l.id != "id-health-1")]
    thin = anchors.thin_segments(anchors.CopyBank(
        identity=one_line, offer=bank.offer, cta=bank.cta, ps=bank.ps))
    assert any(k.startswith("Health/") for k in thin), thin


def test_the_live_bank_has_no_thin_segment_left():
    """Every segment/audience pool can now hold its share without repeating a
    sentence. Executive/individuals was the last one open."""
    assert anchors.thin_segments(anchors.CopyBank.from_csv()) == {}


def test_a_well_stocked_segment_is_not_flagged_thin():
    thin = anchors.thin_segments(anchors.CopyBank.from_csv())
    assert not any(k.startswith("Life/") for k in thin), thin


# ------------------------------------------------------------- the tie-break


def test_ties_do_not_all_break_the_same_way():
    """Alphabetical tie-breaking is deterministic AND systematically biased: it
    handed every leftover seat to whichever id sorted first, so small groups
    never drew their matched line."""
    pool = [anchors.Line(id=f"id-{c}", line="x", meta={}) for c in "abcdefghi"]
    quota = anchors.allocate(pool, 3)
    winners = [k for k, v in quota.items() if v]
    assert winners != sorted(pool, key=lambda l: l.id)[:3][0:1] * 3
    assert sum(quota.values()) == 3
    # Deterministic, just not alphabetical.
    assert anchors.allocate(pool, 3) == quota


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


# ------------------------------------------------------- the echo reallocation


def test_the_deal_never_issues_a_colliding_offer_ps_pair():
    """`b4-01` ("Not a scraped list") and `ps-01` ("not a list") are each fine
    and collide when dealt together. On the live bank that is 1 of 16 offer/ps
    pairs, so roughly one email in sixteen was rejected at export for something
    no drafter caused and none could fix without abandoning an anchor."""
    from outbound import lint
    bank = anchors.CopyBank.from_csv()
    for n in (8, 11, 25, 50, 200):
        leads = [{"email": f"lead{i}@x.ae", "coach_type": "", "sells_to": ""}
                 for i in range(n)]
        dealt = anchors.deal_batch(leads, bank=bank)
        echoes = [e for e, a in dealt.items()
                  if lint.check_echo({"offer": a.offer.line, "cta": a.cta.line,
                                      "ps": a.ps.line})]
        assert not echoes, f"n={n}: {echoes}"


def test_the_reallocation_does_not_push_a_ps_line_over_the_cap():
    """Taking the first clean candidate put one ps at 35% at n=200, exactly the
    repetition cap; hashing put it at 36% on an 11-lead batch, because a hash
    cannot see what it has already handed out. Counting can."""
    from outbound import lint
    bank = anchors.CopyBank.from_csv()
    for n in (8, 11, 25, 50, 100, 200):
        leads = [{"email": f"lead{i}@x.ae", "coach_type": "", "sells_to": ""}
                 for i in range(n)]
        dealt = anchors.deal_batch(leads, bank=bank)
        counts: dict = {}
        for a in dealt.values():
            counts[a.ps.id] = counts.get(a.ps.id, 0) + 1
        top = max(counts.values()) / n
        assert top <= lint.FIXED_LINE_SHARE_CAP, f"n={n}: top ps share {top:.0%}"


def test_the_reallocation_is_reproducible():
    bank = anchors.CopyBank.from_csv()
    leads = [{"email": f"lead{i}@x.ae", "coach_type": "", "sells_to": ""}
             for i in range(50)]
    first = {e: a.ps.id for e, a in anchors.deal_batch(leads, bank=bank).items()}
    second = {e: a.ps.id for e, a in anchors.deal_batch(leads, bank=bank).items()}
    assert first == second


def test_echo_pairs_detects_a_collision_when_one_exists():
    """The reporter itself, on a bank built to collide. `b4-01` + the old
    `ps-01` was the live instance; the copy was rewritten so the pair no longer
    exists, but the mechanism has to keep working for the next one."""
    bank = anchors.CopyBank.from_csv()
    colliding = anchors.CopyBank(
        identity=bank.identity,
        offer=[anchors.Line(id="b4-t", line="I pulled 10 names. Not a scraped list.")],
        cta=bank.cta,
        ps=[anchors.Line(id="ps-t", line="ps: not a list. A fine answer either way.")],
    )
    assert ("b4-t", "ps-t") in anchors.echo_pairs(colliding)


# Collisions the live copy is known to carry. An entry here is a COPY problem
# parked, not a rule relaxed: `deal` reports each one, `_resolve_echoes` refuses
# to deal it, and the ps in it loses roughly a quarter of its allocation as a
# result. The fix for anything listed here is three cells in Airtable's Copy
# Assets, not a change in this repo.
KNOWN_ECHO_PAIRS = {
    # b4-01 ends "...before writing this"; ps-05 is "I read your work before I
    # wrote this one". Two sentences apart in a five-sentence email, so the ps
    # reads as a weaker restatement of the offer. Found by a cold read on
    # `2026-08-02-q2`.
    ("b4-01", "ps-05"),
}


def test_the_live_bank_carries_only_the_echo_pairs_we_know_about():
    """The guard, kept sharp while one real collision is outstanding.

    It used to assert the live bank had NO colliding pair, which was true when
    written: `ps-01` said "not a list", collided with `b4-01`, and the copy was
    rewritten rather than the rule bent. That is still the right response and
    the right response is not available from inside this repo — Copy Assets in
    Airtable owns the lines.

    So a known pair is listed above and anything else fails. The value of the
    original assertion was that a new collision cannot arrive unnoticed, and
    that survives.
    """
    pairs = set(anchors.echo_pairs(anchors.CopyBank.from_csv()))
    assert pairs <= KNOWN_ECHO_PAIRS, f"new echo pair: {sorted(pairs - KNOWN_ECHO_PAIRS)}"


def test_a_known_echo_pair_is_never_dealt_together():
    """The point of listing it: the emails stay clean while the copy is wrong."""
    bank = anchors.CopyBank.from_csv()
    leads = [{"email": f"c{i}@x.ae", "coach_type": "", "sells_to": ""}
             for i in range(120)]
    dealt = anchors.deal_batch(leads, bank=bank)
    for email, deal in dealt.items():
        assert (deal.offer.id, deal.ps.id) not in KNOWN_ECHO_PAIRS, email


# ------------------------------------------------------- room for the hook


def test_the_deal_never_issues_a_combination_with_no_room_for_a_hook():
    """The rule that replaced trimming the copy.

    Six of the live bank's 2,112 combinations leave under 12 words for a hook.
    The old defence rejected the whole bank until somebody shortened a
    hand-written sentence; this one just declines to deal those six.
    """
    from outbound import lint

    bank = anchors.CopyBank.from_csv()
    segs = ["Life", "Career", "Business", "Executive", "Health", "Fitness", ""]
    for n in (8, 25, 60, 200):
        leads = [{"email": f"c{i}@x.ae", "coach_type": segs[i % len(segs)],
                  "sells_to": "individuals" if i % 3 else "corporates"}
                 for i in range(n)]
        dealt = anchors.deal_batch(leads, bank=bank)
        short = {e: a.hook_room() for e, a in dealt.items()
                 if a.hook_room() < lint.MIN_HOOK_WORDS}
        assert not short, f"n={n}: {short}"


def test_the_length_repair_moves_the_ps_and_says_so():
    """The ps moves first: shortest beat, "verbatim or near", and it takes no
    part in the seam between the hook and the identity beat. The cta follows
    only when a ps alone cannot get there.

    Repair is measured against `MIN_HOOK_WORDS + IDENTITY_SLACK`, not against
    `MIN_HOOK_WORDS`, because the drafter authors the identity beat and may
    write to the top of its range. Repairing against the reference length would
    leave `Deal.hook_room()` promising room the linter can still refuse.
    """
    from outbound import lint

    floor = lint.MIN_HOOK_WORDS + anchors.IDENTITY_SLACK
    bank = anchors.CopyBank.from_csv()
    longest = {beat: max(getattr(bank, beat), key=lambda l: lint.word_count(l.line))
               for beat in ("identity", "offer", "cta", "ps")}
    shortest_cta = min(bank.cta, key=lambda l: lint.word_count(l.line))

    # The tight case: the longest line in every beat. Under the floor this needs
    # both beats, which is the documented escalation rather than a defect.
    fixed = {beat: {"a@x.ae": longest[beat]} for beat in ("offer", "cta", "ps")}
    identity = {"a@x.ae": longest["identity"]}
    before = lint.hook_room({b: l.line for b, l in longest.items()})
    assert before < floor, "the fixture stopped being the tight case"

    repaired = anchors._resolve_length(fixed, identity, ["a@x.ae"], bank)
    assert repaired == {"a@x.ae"}
    assert fixed["ps"]["a@x.ae"].id != longest["ps"].id, "the ps must always move"

    after = lint.hook_room({"identity": identity["a@x.ae"].line,
                            "offer": fixed["offer"]["a@x.ae"].line,
                            "cta": fixed["cta"]["a@x.ae"].line,
                            "ps": fixed["ps"]["a@x.ae"].line})
    assert after >= floor

    # Cheapest first: where a ps swap alone clears the floor, the cta stays put.
    fixed2 = {"offer": {"b@x.ae": longest["offer"]},
              "cta": {"b@x.ae": shortest_cta},
              "ps": {"b@x.ae": longest["ps"]}}
    identity2 = {"b@x.ae": longest["identity"]}
    anchors._resolve_length(fixed2, identity2, ["b@x.ae"], bank)
    assert fixed2["cta"]["b@x.ae"].id == shortest_cta.id, "the cta should not move"


def test_a_length_repair_never_introduces_an_echo():
    """It runs after the echo pass, so it must not undo it."""
    from outbound.lint import check_echo

    bank = anchors.CopyBank.from_csv()
    segs = ["Life", "Career", "Business", "Executive", "Health", ""]
    leads = [{"email": f"c{i}@x.ae", "coach_type": segs[i % len(segs)],
              "sells_to": "individuals"} for i in range(60)]
    for anchor in anchors.deal_batch(leads, bank=bank).values():
        assert not check_echo({"offer": anchor.offer.line, "cta": anchor.cta.line,
                               "ps": anchor.ps.line})


def test_no_legal_swap_leaves_the_lead_alone_and_fails_closed():
    """With nothing short enough in the bank the combination is left as dealt,
    and the linter refuses the email. The repair never invents a way out."""
    from outbound import lint

    long_ps = "ps: " + " ".join(["word"] * 40)
    bank = anchors.CopyBank(
        identity=[anchors.Line(id="id-t", line=" ".join(["word"] * 40))],
        offer=[anchors.Line(id="b4-t", line=" ".join(["word"] * 30))],
        cta=[anchors.Line(id="cta-t", line=" ".join(["word"] * 30))],
        ps=[anchors.Line(id="ps-t", line=long_ps)],
    )
    fixed = {beat: {"a@x.ae": getattr(bank, beat)[0]} for beat in ("offer", "cta", "ps")}
    identity = {"a@x.ae": bank.identity[0]}
    assert anchors._resolve_length(fixed, identity, ["a@x.ae"], bank) == set()
    assert fixed["ps"]["a@x.ae"].id == "ps-t"
    assert lint.hook_room({"identity": bank.identity[0].line,
                           "offer": bank.offer[0].line,
                           "cta": bank.cta[0].line,
                           "ps": long_ps}) < lint.MIN_HOOK_WORDS


def test_one_counter_everywhere():
    """A separated figure is two words to the linter and one to `str.split()`.
    The guards used `split()` and the check that rejects an email used the
    other, so a guard could pass a combination the linter then refused."""
    from outbound import lint

    assert lint.word_count("We closed AED 91,500 in 60 days.") == 8
    assert len("We closed AED 91,500 in 60 days.".split()) == 7


# ------------------------------------------------- rebalancing after a hold


def _drafted(n, ps_line="ps: a no here costs you nothing and costs me nothing."):
    return [{"email": f"lead{i}@x.ae",
             "beats": {"hook": "You wrote about pricing packages this week.",
                       "identity": "Your next client is the job. 12 meetings in 60 days.",
                       "offer": "I pulled 10 names for you. Not a scraped list.",
                       "cta": "15 minutes and they're yours the same day, plus why these 10.",
                       "ps": ps_line}}
            for i in range(n)]


def test_a_rebalance_holds_the_share_cap_when_the_cap_is_reachable():
    """Holds are guaranteed by design, and every hold unbalances a deal made
    for the larger batch. Dropping 3 of 11 put two ps lines at 38% against a
    35% cap, and the batch check blocked the whole file.

    The offers here vary, so all four ps lines are usable and the cap is
    reachable. See the next test for what happens when it is not."""
    from outbound import lint
    bank = anchors.CopyBank.from_csv()
    offers = ["I pulled 10 names for you. Not a scraped list.",
              "I've already got 10 names for you, picked one at a time.",
              "10 names are sitting in a doc with your name on it.",
              "I went and found 10 names already. People worth the meeting."]
    for n in (8, 9, 12, 20):
        drafted = _drafted(n)
        for i, d in enumerate(drafted):
            d["beats"]["offer"] = offers[i % len(offers)]
        moves = anchors.rebalance_ps(drafted, bank=bank)
        assert len(moves) == n, f"n={n}: only {len(moves)} allocated"
        counts = {}
        for line_id in moves.values():
            counts[line_id] = counts.get(line_id, 0) + 1
        assert max(counts.values()) / n <= lint.FIXED_LINE_SHARE_CAP, f"n={n}: {counts}"


def test_when_the_cap_cannot_hold_the_echo_rule_still_does():
    """If every offer says "scraped list", ps-01 is excluded and three lines
    must cover the batch — so the cap is arithmetically unreachable. The
    fallback drops the CAP, never the echo rule: a repeated sentence is a
    batch-quality problem, an email that contradicts itself is one nobody can
    fix."""
    from outbound import lint
    bank = anchors.CopyBank.from_csv()
    by_id = {l.id: l.line for l in bank.ps}
    drafted = _drafted(8)          # every offer carries "scraped list"
    moves = anchors.rebalance_ps(drafted, bank=bank)
    assert len(moves) == 8, "every lead must still get a line"
    for d in drafted:
        assert not lint.check_echo(
            {"offer": d["beats"]["offer"], "cta": d["beats"]["cta"],
             "ps": by_id[moves[d["email"]]]})


def test_a_rebalance_never_introduces_an_echo():
    from outbound import lint
    bank = anchors.CopyBank.from_csv()
    by_id = {l.id: l.line for l in bank.ps}
    drafted = _drafted(12)
    moves = anchors.rebalance_ps(drafted, bank=bank)
    for d in drafted:
        chosen = by_id[moves[d["email"]]]
        assert not lint.check_echo({"offer": d["beats"]["offer"],
                                    "cta": d["beats"]["cta"], "ps": chosen})


def test_a_rebalance_never_pushes_an_email_over_the_word_cap():
    """A ps runs 11 to 26 words, so exchanging one for another moves the total
    by up to 15 — enough to tip an email sitting at the ceiling. Two were
    rejected for a length change nobody wrote."""
    from outbound import export, lint
    bank = anchors.CopyBank.from_csv()
    by_id = {l.id: l.line for l in bank.ps}
    # Bodies deliberately near the ceiling.
    drafted = _drafted(10)
    for d in drafted:
        d["beats"]["identity"] = (
            "Your next client is the whole job, and finding them is the part "
            "that takes the time. 12 meetings in 60 days on the last one, "
            "every meeting with somebody who could actually sign it off.")
    moves = anchors.rebalance_ps(drafted, bank=bank)
    for d in drafted:
        body = export.assemble_body({**d["beats"], "ps": by_id[moves[d["email"]]]},
                                    greeting_name="Name")
        assert len(body.split()) <= lint.WORD_MAX, len(body.split())


def test_the_rebalance_finds_an_assignment_a_naive_order_would_miss():
    """Processing in address order let unconstrained leads take the scarce
    lines, so the constrained ones arrived to find nothing legal — and the
    allocator gave up where a perfect 2/2/2/2 assignment existed."""
    bank = anchors.CopyBank.from_csv()
    drafted = _drafted(8)
    # Half can only take the shortest ps lines.
    for d in drafted[:4]:
        d["beats"]["identity"] = (
            "Your next client is the whole job, and finding them is the part "
            "that takes the time. 12 meetings in 60 days on the last one, "
            "every meeting with somebody who could actually sign it off.")
    moves = anchors.rebalance_ps(drafted, bank=bank)
    assert len(moves) == 8
    counts = {}
    for line_id in moves.values():
        counts[line_id] = counts.get(line_id, 0) + 1
    assert max(counts.values()) <= 3, counts


def test_the_rebalance_is_reproducible():
    bank = anchors.CopyBank.from_csv()
    drafted = _drafted(12)
    assert (anchors.rebalance_ps(drafted, bank=bank)
            == anchors.rebalance_ps(drafted, bank=bank))


def test_hook_room_is_a_floor_the_drafter_can_rely_on():
    """`hook_room()` must hold however long the identity beat comes out.

    It used to be measured against the REFERENCE identity line, which is the
    room a hook has only if the drafter writes that sentence at exactly
    reference length. Drafters write to the top of a range, so the figure was
    optimistic on every lead of `2026-08-02-q2`: Sabine was told 18 and had 16,
    John was told 32 and had 22. Three drafters independently recomputed it and
    reported the instruction wrong, and the orchestrator relaying it got the
    correction wrong twice more.

    So the promise is now the floor, and this pins it: whatever the drafter
    writes inside `identity_budget()`, the hook still has `hook_room()` words.
    """
    from outbound import lint

    bank = anchors.CopyBank.from_csv()
    leads = [{"email": f"c{i}@x.ae", "coach_type": "", "sells_to": ""}
             for i in range(60)]
    dealt = anchors.deal_batch(leads, bank=bank)

    for email, deal in dealt.items():
        low, high = deal.identity_budget()
        promised = deal.hook_room()
        # The worst case the drafter is allowed: identity at the top of range.
        worst = deal.authored_budget() - high
        assert promised <= worst, f"{email}: promised {promised}, worst {worst}"
        # And the promise never dips under the floor the linter enforces.
        assert promised >= lint.MIN_HOOK_WORDS, f"{email}: {promised}"


def test_the_authored_budget_is_exact_and_the_room_is_derived_from_it():
    """`authored_budget()` is the one length figure that is true at deal time.

    It depends on nothing the drafter has written — the ceiling less the three
    hand-written lines, the greeting and the sign-off — so a drafter can get the
    exact hook room by subtracting its own identity sentence from it. That is
    what the prompt now hands over, alongside the guaranteed floor.
    """
    from outbound import lint
    from outbound.export import assemble_body

    bank = anchors.CopyBank.from_csv()
    deal = anchors.deal_batch(
        [{"email": "a@x.ae", "coach_type": "", "sells_to": ""}], bank=bank)["a@x.ae"]

    body = assemble_body({"identity": "", "offer": deal.offer.line,
                          "cta": deal.cta.line, "ps": deal.ps.line},
                         greeting_name="Name")
    assert deal.authored_budget() == lint.WORD_MAX - lint.word_count(body)
    assert deal.hook_room() == deal.authored_budget() - deal.identity_budget()[1]

    block = deal.as_prompt_block()
    assert str(deal.authored_budget()) in block
    assert str(deal.hook_room()) in block
