"""
Gate 0 floor evaluation — the machine-checkable half.

The floor (from the opener-finder skill, Jul 2 2026):
- Audience floor:  ~1K followers or equivalent real audience signal
- Activity floor:  last visible activity within ~3 weeks
- Niche floor:     parenting or faith-based, genuinely
- Plus the sourcing gate: is there an actual offer/funnel behind the bio link?

A crawler can settle the funnel-existence questions and take follower count
as input. Activity and niche need a web search + judgment — those come back
as NEEDS_REVIEW for the Claude layer, never guessed here.
"""

from dataclasses import dataclass, field

AUDIENCE_FLOOR = 1000

PASS, FAIL, NEEDS_REVIEW = "pass", "fail", "needs_review"


@dataclass
class FloorVerdict:
    name: str
    verdict: str          # pass | fail | needs_review
    evidence: str


@dataclass
class FloorResult:
    verdicts: list[FloorVerdict] = field(default_factory=list)

    @property
    def hard_fail(self) -> bool:
        return any(v.verdict == FAIL for v in self.verdicts)

    def as_dict(self) -> dict:
        return {
            "hard_fail": self.hard_fail,
            "floors": [
                {"floor": v.name, "verdict": v.verdict, "evidence": v.evidence}
                for v in self.verdicts
            ],
        }


def evaluate_floors(
    *,
    bio_link_alive: bool,
    bio_link_error: str,
    offer_evidence: list[str],
    email_capture_anywhere: bool,
    followers: int | None = None,
) -> FloorResult:
    result = FloorResult()

    # --- Bio link alive (sourcing gate: dead first click) ---
    if bio_link_alive:
        result.verdicts.append(FloorVerdict("bio_link_alive", PASS, "Bio link loaded"))
    else:
        # A dead bio link is not a disqualifier — it's a Tier A finding candidate.
        result.verdicts.append(FloorVerdict(
            "bio_link_alive", NEEDS_REVIEW,
            f"Bio link failed to load ({bio_link_error[:120]}). Verify logged-out by hand: "
            "hard 404 = Tier A opener candidate, permission wall = not openable.",
        ))

    # --- Offer/funnel behind the link ---
    if offer_evidence:
        result.verdicts.append(FloorVerdict(
            "offer_present", PASS, "; ".join(offer_evidence[:3]),
        ))
    else:
        result.verdicts.append(FloorVerdict(
            "offer_present", NEEDS_REVIEW,
            "No paid offer or checkout visible from the crawl. Could be DM-gated or "
            "login-walled — confirm by hand before dropping. If genuinely nothing: hobbyist floor, Lane 3.",
        ))

    # --- Audience floor ---
    if followers is None:
        result.verdicts.append(FloorVerdict(
            "audience_floor", NEEDS_REVIEW,
            f"Follower count not supplied. Floor is ~{AUDIENCE_FLOOR:,} or an equivalent "
            "real audience signal (podcast, list, community).",
        ))
    elif followers >= AUDIENCE_FLOOR:
        result.verdicts.append(FloorVerdict(
            "audience_floor", PASS, f"{followers:,} followers",
        ))
    else:
        result.verdicts.append(FloorVerdict(
            "audience_floor", FAIL,
            f"{followers:,} followers — under the ~{AUDIENCE_FLOOR:,} floor. Lane 3 unless "
            "there's an equivalent audience signal (podcast, list, active community).",
        ))

    # --- Activity + niche: not machine-checkable ---
    result.verdicts.append(FloorVerdict(
        "activity_floor", NEEDS_REVIEW,
        "Verify via web search: last post/visible activity within ~3 weeks.",
    ))
    result.verdicts.append(FloorVerdict(
        "niche_floor", NEEDS_REVIEW,
        "Verify: genuinely parenting or faith-based. Adjacent wellness without case-study fit = park.",
    ))

    # --- Context signal, not a gate ---
    result.verdicts.append(FloorVerdict(
        "email_capture_anywhere",
        PASS if email_capture_anywhere else NEEDS_REVIEW,
        "Email capture found on at least one crawled page." if email_capture_anywhere
        else "No email capture visible anywhere in the crawl (Stop 5 signal, needs felt-cost framing).",
    ))

    return result
