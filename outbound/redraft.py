"""Who gets redrafted, decided in code instead of one lead at a time.

`.claude/skills/outbound-batch/SKILL.md` has said since it was written that a
REWRITE goes *"back to the drafter once, with the verifier's note. Then it either
passes or it holds."* As an instruction it lost twice. On `2026-08-02-q2` eight
of nine leads exceeded it, one of them running five rounds; on `2026-08-02-q3`
eight leads exceeded it and three ran three rounds. Measured, the repeats were
68% and 46% of their draft stages.

A cap that is a sentence is a cap a long session talks itself out of, one
reasonable exception at a time. A cap that is a loop bound is not.

**The clustering is the other half, and it is the bigger one.** Seventeen of
seventeen drafts on q3 failed their first cold read on the identity beat. Each
was answered individually: nineteen redraft prompts carrying 1.6x the text of all
seventeen original briefs, and roughly $12 of orchestrator turns at 300-500k
context each. The journal's own diagnosis is *"I answered the first finding
per-lead, and the second, and the third, before treating the repetition as the
signal it was."*

Nobody was being careless. A human reading verdicts one at a time cannot see the
seventeenth until they have paid for sixteen. Counting is what makes the pattern
visible on the first pass rather than the last, and counting needs the beat to be
an enum, which is what `outbound/verdict.py` is for.

So: when a beat accounts for at least `CLUSTER_MIN` of a wave's REWRITEs, this
says so and emits **one shared correction** naming the beat and the leads. The
fix for a stage-level defect is one instruction to the whole wave, not N
instructions that happen to say the same thing.

**This decides, it does not draft.** It emits who is redrafted, who holds, and
why — the same boundary `crm-rows` keeps. And like every observer here it never
exits 1 on a finding: a batch where everything holds is a real answer, and a gate
that can halt a send file over a routing decision gets routed around.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

# How many leads must share a beat before it stops being N problems and starts
# being one. Two is deliberately low: the cost of one shared note that was not
# needed is a sentence, and the cost of missing the pattern was measured at
# about $12 of orchestrator turns in a single batch.
CLUSTER_MIN = 2

# The cap SKILL.md always specified. One repair round, then the lead holds.
MAX_ROUNDS = 2


@dataclass
class Plan:
    """What happens next, per lead, and why."""

    redraft: list = field(default_factory=list)     # slugs to send back
    hold: list = field(default_factory=list)        # slugs that stop here
    ship: list = field(default_factory=list)        # slugs at SEND
    reasons: dict = field(default_factory=dict)     # slug -> why
    shared: list = field(default_factory=list)      # one note per clustered beat
    by_beat: dict = field(default_factory=dict)     # beat -> how many leads
    round: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def plan(verdicts: list, *, max_rounds: int = MAX_ROUNDS,
         cluster_min: int = CLUSTER_MIN) -> Plan:
    """Route a wave of cold reads. Pure: no files, no agents, no fetching."""
    out = Plan()
    out.round = max((v.round for v in verdicts), default=0)

    for item in verdicts:
        if item.verdict == "SEND":
            out.ship.append(item.slug)
            out.reasons[item.slug] = "SEND"
        elif item.verdict == "REJECT":
            out.hold.append(item.slug)
            out.reasons[item.slug] = "REJECT — holds, no row"
        elif item.verdict == "REWRITE":
            if item.round >= max_rounds:
                out.hold.append(item.slug)
                out.reasons[item.slug] = (
                    f"REWRITE on round {item.round}, cap is {max_rounds} — "
                    f"holds. A third attempt has never been the thing that "
                    f"fixed it")
            else:
                out.redraft.append(item.slug)
                beats = ", ".join(sorted({p.beat for p in item.problems}))
                out.reasons[item.slug] = f"REWRITE round {item.round} — {beats}"
        else:
            out.hold.append(item.slug)
            out.reasons[item.slug] = f"verdict {item.verdict!r} is not routable"

    # Count the beats across everything that was sent back, including the ones
    # that hit the cap: a pattern is a pattern whether or not this wave acts on
    # each instance of it.
    rewrites = [v for v in verdicts if v.verdict == "REWRITE"]
    for item in rewrites:
        for beat in {p.beat for p in item.problems}:
            out.by_beat.setdefault(beat, []).append(item.slug)
    out.by_beat = {k: sorted(v) for k, v in
                   sorted(out.by_beat.items(), key=lambda kv: (-len(kv[1]), kv[0]))}

    for beat, slugs in out.by_beat.items():
        if len(slugs) < cluster_min:
            continue
        shared = sorted({p.problem for item in rewrites for p in item.problems
                         if p.beat == beat})
        out.shared.append({
            "beat": beat,
            "leads": slugs,
            "n": len(slugs),
            "share": round(len(slugs) / len(rewrites), 2) if rewrites else None,
            "findings": shared[:5],
        })
    return out


def report(out: Plan, *, cluster_min: int = CLUSTER_MIN) -> str:
    """The block a skill quotes instead of narrating a wave lead by lead."""
    lines = [
        f"REDRAFT round {out.round}: {len(out.ship)} ship, "
        f"{len(out.redraft)} back to the drafter, {len(out.hold)} hold",
    ]
    for entry in out.shared:
        share = "" if entry["share"] is None else f" ({entry['share'] * 100:.0f}% of them)"
        lines.append(
            f"  SHARED  {entry['n']} of this wave's rewrites fail on the "
            f"{entry['beat']} beat{share} — fix the stage, not the leads. "
            f"Send ONE correction to all of them.")
        for finding in entry["findings"]:
            lines.append(f"          {finding}")
        lines.append(f"          leads: {', '.join(entry['leads'])}")
    if out.by_beat and not out.shared:
        lines.append(f"  no beat reaches {cluster_min} leads — these are "
                     f"genuinely separate problems, so separate notes are right")
    capped = [s for s in out.hold if "cap is" in out.reasons.get(s, "")]
    if capped:
        lines.append(f"  CAP     {len(capped)} lead(s) held at the round cap: "
                     + ", ".join(capped))
    # A lead the shared notes already name is a lead this would be printing
    # twice. Seventeen redundant lines is how the old loop reported a single
    # stage defect, and the orchestrator keeps every one of them.
    covered = {slug for entry in out.shared for slug in entry["leads"]}
    for slug in out.redraft:
        if slug in covered:
            continue
        lines.append(f"  redraft {slug}: {out.reasons[slug]}")
    quiet = sum(1 for s in out.redraft if s in covered)
    if quiet:
        lines.append(f"  {quiet} more redrafted lead(s) are named in the SHARED "
                     f"block(s) above and not repeated here")
    for slug in out.hold:
        lines.append(f"  hold    {slug}: {out.reasons[slug]}")
    lines.append("  OBSERVER. This routes; it never fails a batch. A wave where "
                 "everything holds is a real answer.")
    return "\n".join(lines)
