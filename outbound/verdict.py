"""What the cold read decided, written down instead of remembered.

Until now the draft verdict had no artifact. `draft-verifier` returned SEND,
REWRITE or REJECT as prose, its tool list was `Read, Bash, Grep` with no `Write`,
and `.claude/skills/outbound-batch/SKILL.md` said so outright: *"The verdict
lives in an agent, nothing in Python can reach it."* `REWRITE` appeared in zero
Python in this repo.

That is the shape that made drafting expensive. A verdict nothing can read is a
verdict only the orchestrator can route, so every one arrived on its own turn,
was held in a 600k-token context, and was handed back as a hand-written note. On
`2026-08-02-q3` seventeen drafts failed their first cold read on the same beat
and were repaired seventeen separate times, the redraft prompts running 1.6x the
size of all seventeen original briefs put together. The journal names the mistake
plainly: *"I answered the first finding per-lead, and the second, and the third,
before treating the repetition as the signal it was."*

A repetition is only a signal if something can count it. That is what this file
is for.

**The shape is the agent's own contract, not a new one.** `draft-verifier.md`
already specifies `verdict / seam / voice / problems[{beat, sentence, ...}]`.
The only change is that its last key was written in English (`what is wrong`)
and is now an identifier, because a field that has to be counted has to have a
name.

**`beat` is an enum, and that is the whole point.** Clustering findings across a
wave needs the beat to be the same string every time; free text would put "the
identity line" and "identity beat" in two buckets and report seventeen
one-of-a-kind problems, which is exactly the state this is fixing.

**A REWRITE with no problems is rejected.** The verdict's entire downstream use
is deciding what to say to the drafter, and a REWRITE that names nothing is a
lead that will be redrafted against no instruction — the most expensive possible
pass, since it is a full opus draft that cannot improve on anything.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

VERDICTS = ("SEND", "REWRITE", "REJECT")

# The five beats, as `outbound/lint.py` and every draft file spell them. Named
# here rather than re-derived so a sixth cannot appear in a verdict without
# appearing in the email.
BEATS = ("hook", "identity", "offer", "cta", "ps")


@dataclass
class Problem:
    """One thing wrong, in the one place it is wrong."""

    beat: str = ""
    sentence: str = ""
    problem: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verdict:
    """One draft, read cold. `round` is what makes the cap enforceable."""

    slug: str = ""
    verdict: str = ""
    seam: str = ""
    voice: str = ""
    problems: list = field(default_factory=list)
    round: int = 1

    @classmethod
    def from_dict(cls, data: dict) -> "Verdict":
        raw = data.get("problems") or []
        problems = []
        for item in raw if isinstance(raw, list) else []:
            if isinstance(item, dict):
                problems.append(Problem(
                    beat=str(item.get("beat") or "").strip().lower(),
                    sentence=str(item.get("sentence") or "").strip(),
                    problem=str(item.get("problem") or "").strip()))
        return cls(
            slug=str(data.get("slug") or "").strip(),
            verdict=str(data.get("verdict") or "").strip().upper(),
            seam=str(data.get("seam") or "").strip(),
            voice=str(data.get("voice") or "").strip(),
            problems=problems,
            round=int(data.get("round") or 1),
        )

    def to_dict(self) -> dict:
        out = asdict(self)
        out["problems"] = [p.to_dict() if isinstance(p, Problem) else p
                           for p in self.problems]
        return out


def validate(item: Verdict) -> list[str]:
    """Schema violations. An empty list means the cold read is routable."""
    problems = []
    if not item.slug:
        problems.append("no slug — a verdict that names no lead cannot be routed")
    if item.verdict not in VERDICTS:
        problems.append(
            f"verdict={item.verdict!r} is not one of {' | '.join(VERDICTS)}")
    if item.verdict == "REWRITE" and not item.problems:
        problems.append(
            "REWRITE with no problems — the drafter would be re-run against no "
            "instruction, which is a full opus pass that cannot improve on "
            "anything. Name the beat and the sentence, or return SEND")
    for n, problem in enumerate(item.problems, 1):
        if problem.beat not in BEATS:
            problems.append(
                f"problem {n}: beat={problem.beat!r} is not one of "
                f"{' | '.join(BEATS)}. The beat is an enum because a wave's "
                f"findings get counted by it, and free text does not cluster")
        if not problem.problem:
            problems.append(f"problem {n}: says nothing is wrong")
    if item.round < 1:
        problems.append(f"round={item.round} — rounds start at 1")
    return problems


def load(raw) -> list[Verdict]:
    """One verdict, a list of them, or a `{slug: verdict}` map."""
    if isinstance(raw, dict) and "verdict" not in raw:
        out = []
        for slug, body in raw.items():
            if isinstance(body, dict):
                body = dict(body)
                body.setdefault("slug", slug)
                out.append(Verdict.from_dict(body))
        return out
    if isinstance(raw, dict):
        return [Verdict.from_dict(raw)]
    return [Verdict.from_dict(r) for r in raw if isinstance(r, dict)]


def read_dir(where: str | Path, pattern: str = "verdict-*.json") -> list[Verdict]:
    """Every verdict a wave wrote. The orchestrator no longer carries them."""
    out = []
    for path in sorted(Path(where).glob(pattern)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for item in load(data):
            if not item.slug:
                item.slug = path.stem[len("verdict-"):]
            out.append(item)
    return out


def report(items: list) -> str:
    """The quotable line, and every schema violation under it."""
    counts: dict = {}
    for item in items:
        counts[item.verdict or "?"] = counts.get(item.verdict or "?", 0) + 1
    tally = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    bad = [(i, validate(i)) for i in items]
    broken = sum(1 for _, p in bad if p)
    head = "VALID" if not broken else f"INVALID ({broken})"
    lines = [f"VERDICT: {head}, {len(items)} cold read(s) — {tally or 'none'}"]
    for item, problems in bad:
        for problem in problems:
            lines.append(f"  SCHEMA  {item.slug or '?'}: {problem}")
    return "\n".join(lines)


def validate_all(items: list) -> bool:
    """True when anything failed, matching `select` and `hook`."""
    return any(validate(i) for i in items)
