"""The three floors. UAE-based, actually a coach, active in the last 30 days.

Deliberately smaller than the gate it replaces. The old Gate 0 had five floors
including a 1,500 audience minimum and an AED 5,000 program price, and both of
them are now wrong for a different reason each:

- **The audience floor is decoupled from the offer.** We are selling a coach
  their next client. That has nothing to do with how many followers they have, so
  audience size stopped predicting anything the day the offer changed.
- **The price floor cannot be measured.** Six coach sites in about a hundred
  publish a number. A floor that reads `unclear` on 94% of the market is not a
  gate, it is a coin flip with extra fetches attached.

Both are still *captured* — they are useful for choosing an identity line and
for cohort analysis later — but neither kills a lead.

**`unclear` passes.** Only a clear `no` drops a row. This asymmetry is the
whole design: a false kill is permanent and invisible, a false pass costs one
research call. The verdicts are therefore three-valued everywhere, and every
one of them carries the source that settled it, so a `no` can be argued with
instead of taken on trust.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from audit.urls import registrable_domain

YES, NO, UNCLEAR = "yes", "no", "unclear"

ACTIVITY_WINDOW_DAYS = 30

# A footer's copyright year is the site's opinion of today, not evidence that
# anyone did anything. `latest_activity_date` drops any date sitting next to it.
_COPYRIGHT_NEAR = re.compile(r"(?:©|&copy;|copyright|all rights reserved)", re.I)

UAE_CITIES = (
    "dubai", "abu dhabi", "abudhabi", "sharjah", "ajman", "fujairah",
    "ras al khaimah", "ras al-khaimah", "umm al quwain", "al ain",
)
UAE_MARKERS = (
    "united arab emirates", "u.a.e", "uae", ".ae", "jumeirah",
    "dubai marina",
    "downtown dubai", "difc", "jlt", "business bay", "silicon oasis",
    "media city", "internet city", "khalifa city", "yas island",
    # Neighbourhoods a real bio writes instead of the emirate. Every one of
    # these returned a hard NO from the "based in X" rule below, because the
    # rule killed on any place it did not recognise. "Based in Al Barsha" is a
    # Dubai coach telling us exactly where they are.
    "al barsha", "al quoz", "al nahda", "al wasl", "al safa", "al furjan",
    "deira", "bur dubai", "mirdif", "motor city", "sports city",
    "arabian ranches", "emirates hills", "dubai hills", "the greens",
    "the springs", "the meadows", "palm jumeirah", "jvc", "jbr", "jlt",
    "reem island", "saadiyat", "al reem", "masdar", "corniche",
    "tecom", "barsha heights", "discovery gardens", "city walk",
)

# Shorthand a real bio uses instead of a city name. Airport codes and emirate
# abbreviations were returning a hard NO on genuinely UAE-based coaches,
# because the "based in X" rule below fired whenever X was not literally in
# UAE_CITIES. That is the one failure this whole design exists to avoid.
UAE_SHORTHAND = (
    "dxb", "auh", "shj", "rak", "uaq", "fjr", "awz", "ad", "ae",
)
# Places that mention the UAE without being in it. "Serving clients across the
# GCC" from a London address is the exact failure this catches.
UAE_NEGATIVE = (
    "serving the uae", "clients across the gcc", "remote across the middle east",
    "we work with clients in dubai",
)

# The ONLY thing that earns a hard NO from a "based in X" line. The rule used to
# be "X is not a UAE city", which killed "Based in Al Barsha", "Based in Deira"
# and nine other real UAE localities outright — a permanent, invisible loss on
# leads who had just told us where they were. Recognising a foreign place is a
# positive claim; failing to recognise a place is not. Anything absent from both
# lists is `unclear`, which costs one research call.
FOREIGN_PLACES = (
    # countries and regions
    "united kingdom", "uk", "england", "scotland", "wales", "ireland",
    "united states", "usa", "us", "america", "canada", "australia",
    "new zealand", "india", "pakistan", "bangladesh", "sri lanka",
    "south africa", "nigeria", "kenya", "egypt", "morocco", "lebanon",
    "jordan", "syria", "iraq", "iran", "turkey", "turkiye", "germany",
    "france", "spain", "portugal", "italy", "greece", "netherlands",
    "holland", "belgium", "switzerland", "austria", "sweden", "norway",
    "denmark", "finland", "poland", "romania", "russia", "ukraine",
    "china", "japan", "korea", "singapore", "malaysia", "indonesia",
    "thailand", "vietnam", "philippines", "brazil", "argentina", "mexico",
    "chile", "colombia", "saudi arabia", "ksa", "qatar", "kuwait",
    "bahrain", "oman", "israel", "cyprus", "malta",
    # cities coaches actually list
    "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh",
    "bristol", "liverpool", "dublin", "new york", "brooklyn", "los angeles",
    "san francisco", "chicago", "boston", "seattle", "austin", "denver",
    "miami", "atlanta", "houston", "dallas", "toronto", "vancouver",
    "montreal", "sydney", "melbourne", "brisbane", "perth", "auckland",
    "mumbai", "delhi", "new delhi", "bangalore", "bengaluru", "hyderabad",
    "chennai", "pune", "kolkata", "karachi", "lahore", "islamabad",
    "colombo", "dhaka", "cairo", "alexandria", "casablanca", "beirut",
    "amman", "istanbul", "ankara", "tehran", "riyadh", "jeddah", "dammam",
    "doha", "kuwait city", "manama", "muscat", "paris", "lyon", "marseille",
    "berlin", "munich", "hamburg", "frankfurt", "madrid", "barcelona",
    "lisbon", "porto", "rome", "milan", "athens", "amsterdam", "rotterdam",
    "brussels", "zurich", "geneva", "vienna", "stockholm", "oslo",
    "copenhagen", "helsinki", "warsaw", "prague", "budapest", "bucharest",
    "moscow", "kyiv", "kiev", "beijing", "shanghai", "hong kong", "tokyo",
    "osaka", "seoul", "bangkok", "jakarta", "kuala lumpur", "manila",
    "sao paulo", "rio de janeiro", "buenos aires", "mexico city", "bogota",
    "santiago", "lagos", "abuja", "nairobi", "accra", "johannesburg",
    "cape town", "durban", "tel aviv", "jerusalem", "nicosia", "valletta",
)

COACH_MARKERS = (
    "coach", "coaching", "mentor", "mentoring", "consultant to founders",
    "therapist", "practitioner", "facilitator",
)
# A coaching *company* with staff is not the solo operator this is written for,
# but per the ICP decision that is captured, not gated.
COACH_TYPES = (
    "Business", "Leadership", "Life", "Mindset", "Career",
    "Health", "Fitness", "Executive", "Other",
)

_TYPE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Executive", re.compile(r"\bexecutive coach|c-suite|senior leader", re.I)),
    ("Leadership", re.compile(r"\bleadership|team lead|manager development", re.I)),
    ("Business", re.compile(r"\bbusiness coach|founder coach|entrepreneur coach|scale", re.I)),
    ("Career", re.compile(r"\bcareer coach|job search|interview|cv\b|resume", re.I)),
    ("Health", re.compile(r"\bhealth coach|nutrition|wellness|hormone|gut\b", re.I)),
    ("Fitness", re.compile(r"\bfitness|personal train|strength|physique", re.I)),
    ("Mindset", re.compile(r"\bmindset|confidence|limiting belief|self.?worth", re.I)),
    ("Life", re.compile(r"\blife coach|transformation|purpose|fulfil", re.I)),
]

# Second pass, applied ONLY to a headline, and only after the strict patterns
# have found nothing anywhere. A real headline puts words between the segment
# and the noun — "Career and Work-Life Balance Coach", "Chief Executive Officer
# Coach", "Training and Development Coaching Leaders" — and the strict patterns
# above want them adjacent. Three of twelve on the first real list came back
# with no segment for exactly that reason, and a lead with no segment draws a
# generic identity line.
#
# Restricted to the headline on purpose. A headline is a deliberate
# self-description; body copy is noise, and a loose pattern let loose on 80,000
# characters of site text would find every segment on every site. A wrong
# segment is worse than none: it ships an identity line about the wrong kind of
# coach, while no segment ships a generic line that is merely weaker.
_GAP = r"[\w\s&|/,.-]{0,32}"
_TYPE_PATTERNS_LOOSE: list[tuple[str, re.Pattern]] = [
    ("Executive", re.compile(rf"\bexecutive\b{_GAP}\bcoach|\bcoach\w*{_GAP}\bexecutives?\b", re.I)),
    ("Career", re.compile(rf"\bcareer\b{_GAP}\bcoach|\bcoach\w*{_GAP}\bcareers?\b", re.I)),
    ("Leadership", re.compile(rf"\bleaders?(?:hip)?\b{_GAP}\bcoach|\bcoach\w*{_GAP}\bleaders?\b", re.I)),
    ("Business", re.compile(rf"\bbusiness\b{_GAP}\bcoach|\bcoach\w*{_GAP}\bbusiness\b", re.I)),
    ("Health", re.compile(rf"\bhealth\b{_GAP}\bcoach|\bcoach\w*{_GAP}\bhealth\b", re.I)),
    ("Mindset", re.compile(rf"\bmindset\b{_GAP}\bcoach|\bcoach\w*{_GAP}\bmindset\b", re.I)),
    ("Fitness", re.compile(rf"\bfitness\b{_GAP}\bcoach|\bcoach\w*{_GAP}\bfitness\b", re.I)),
    ("Life", re.compile(rf"\blife\b{_GAP}\bcoach|\bcoach\w*{_GAP}\blife\b", re.I)),
]

_CORPORATE_MARKERS = re.compile(
    r"\b(corporate|organisation|organization|team|l&d|leadership team|"
    r"employees|workshop for|in.?house|b2b|enterprise)\b", re.I
)
_INDIVIDUAL_MARKERS = re.compile(
    r"\b(1:1|one.to.one|individual|personal|private client|women who|"
    r"professionals who|my clients)\b", re.I
)


@dataclass
class Verdict:
    """One floor's answer, and what settled it.

    `source` is not decoration. A `no` with no source is a guess wearing a
    verdict's clothes, and the verifier's job is to reject exactly that.
    """
    value: str = UNCLEAR
    source: str = ""
    evidence: str = ""

    def __bool__(self) -> bool:
        return self.value != NO

    def line(self, label: str) -> str:
        detail = f" [{self.source}]" if self.source else ""
        quote = f' "{self.evidence[:80]}"' if self.evidence else ""
        return f"{label}: {self.value.upper()}{detail}{quote}"


@dataclass
class Qualification:
    uae_based: Verdict = field(default_factory=Verdict)
    is_coach: Verdict = field(default_factory=Verdict)
    active_recent: Verdict = field(default_factory=Verdict)
    # Captured, never gated.
    coach_type: str = ""
    coach_type_source: str = ""
    sells_to: str = ""
    sells_to_source: str = ""
    audience_size: int | None = None
    top_program_price_aed: int | None = None
    solo: str = UNCLEAR

    @property
    def passed(self) -> bool:
        return all(v.value != NO for v in
                   (self.uae_based, self.is_coach, self.active_recent))

    @property
    def failed_floors(self) -> list[str]:
        return [name for name, v in (
            ("UAE-based", self.uae_based),
            ("is a coach", self.is_coach),
            ("active in 30 days", self.active_recent),
        ) if v.value == NO]

    def report(self, name: str) -> str:
        head = "PASS" if self.passed else f"FAIL ({', '.join(self.failed_floors)})"
        lines = [
            f"QUALIFY {name}: {head}",
            "  " + self.uae_based.line("UAE-based"),
            "  " + self.is_coach.line("is a coach"),
            "  " + self.active_recent.line("active in 30 days"),
            f"  captured: type={self.coach_type or '?'} "
            f"sells_to={self.sells_to or '?'} "
            f"audience={self.audience_size if self.audience_size is not None else '?'} "
            f"price_aed={self.top_program_price_aed if self.top_program_price_aed is not None else '?'} "
            f"solo={self.solo}",
        ]
        return "\n".join(lines)


# ------------------------------------------------------------------- the floors


def check_uae(*, city: str = "", text: str = "", domain: str = "",
              source: str = "") -> Verdict:
    """Based in the UAE, not merely serving it.

    The distinction is load-bearing: a coach in London selling to Dubai has a
    different market, a different price ceiling, and no reason to recognise the
    reference group in the identity beat.
    """
    haystack = " ".join([city, text, domain]).lower()
    if not haystack.strip():
        return Verdict(UNCLEAR, source or "no data")

    for phrase in UAE_NEGATIVE:
        if phrase in haystack:
            return Verdict(UNCLEAR, source or "text",
                           f"claims reach, not residence: {phrase}")

    # An explicit statement of residence is checked FIRST, and settles it either
    # way. It used to run last, after a loose scan for UAE words — so "I am a
    # coach based in Toronto. Read my essay at nowhere.aeon.co" returned YES on
    # ".ae", and "Our client Marina came to us from Manchester" returned YES on
    # "marina". A coach who has written down where they live outranks a word
    # that happened to appear in a URL.
    stated = _stated_residence(text, source)
    if stated is not None:
        return stated

    for marker in UAE_CITIES:
        if re.search(rf"\b{re.escape(marker)}\b", haystack):
            return Verdict(YES, source or "text", marker)
    # The TLD, on the DOMAIN only. `".ae" in haystack` matched aeon.co,
    # michae.com and every other incidental "ae" in a page of prose.
    if registrable_domain(domain).endswith(".ae") if domain else False:
        return Verdict(YES, source or "domain", domain)
    # Word-bounded, for the same reason. "marina" inside "Marina Bay, Singapore"
    # is not a Dubai address.
    for marker in UAE_MARKERS:
        if marker == ".ae":
            continue                      # handled above, on the domain only
        if re.search(rf"\b{re.escape(marker)}\b", haystack):
            return Verdict(YES, source or "text", marker)

    # A RECOGNISED other place is the only thing that earns a NO. Matched
    # case-insensitively: "Based in Manchester" at the start of a sentence is
    # the common form, and a lowercase-only pattern silently misses all of them.
    #
    # The burden sits on the kill, not on the pass. The old rule was "X is not
    # in UAE_CITIES", which is a statement about our list rather than about the
    # lead, and it hard-killed eleven real UAE localities including Al Barsha,
    # Deira and Mirdif. Now an unrecognised place is `unclear` — one research
    # call — because a false kill is permanent and nobody ever sees it.
    return _stated_residence(text, source) or Verdict(UNCLEAR, source or "text")


def _stated_residence(text: str, source: str = "") -> "Verdict | None":
    """A "based in X" line, resolved. None when the text has no such line."""
    other = re.search(
        r"\b(?:based|located|living|headquartered)\s+in\s+(?:the\s+)?"
        r"([A-Za-z]+(?:[ -][A-Za-z]+)?)",
        text or "", re.I,
    )
    if other:
        where = other.group(1).strip()
        lowered = where.lower()
        if any(m in lowered for m in UAE_CITIES):
            return Verdict(YES, source or "text", other.group(0))
        if lowered in UAE_SHORTHAND:
            return Verdict(YES, source or "text", f"{other.group(0)} (UAE shorthand)")
        # The neighbourhood list too. This branch now runs BEFORE the general
        # marker scan, so without this "Based in Al Barsha" reached the foreign
        # check and came back unclear — undoing the eleven-locality fix.
        # Check the whole matched phrase too, not only the captured group: the
        # optional "the" prefix in the pattern above consumes it, so "Based in
        # The Greens" captured just "Greens" and missed the marker.
        whole = other.group(0).lower()
        if any(m in lowered or m in whole
               for m in UAE_MARKERS if m != ".ae"):
            return Verdict(YES, source or "text", other.group(0))
        if lowered in FOREIGN_PLACES:
            return Verdict(NO, source or "text", other.group(0))
        # "Based in Manchester, UK" — the regex takes two words, so check the
        # leading word too before giving up on a place we do know.
        first_word = lowered.split()[0] if lowered.split() else ""
        if first_word in FOREIGN_PLACES:
            return Verdict(NO, source or "text", other.group(0))
        return Verdict(UNCLEAR, source or "text",
                       f"{other.group(0)} — place not recognised either way")
    return None


def check_coach(*, headline: str = "", text: str = "", source: str = "") -> Verdict:
    """Actually sells coaching, rather than merely using the word."""
    haystack = " ".join([headline, text]).lower()
    if not haystack.strip():
        return Verdict(UNCLEAR, source or "no data")
    for marker in COACH_MARKERS:
        if marker in haystack:
            return Verdict(YES, source or "text", marker)
    return Verdict(UNCLEAR, source or "text")


def check_active(*, last_seen: date | None = None, today: date | None = None,
                 source: str = "") -> Verdict:
    """Posted, published or shipped something inside the window.

    No date found is `unclear`, never `no`. Absence of a visible post is
    absence of evidence — plenty of working coaches do not post.
    """
    if last_seen is None:
        return Verdict(UNCLEAR, source or "no dated activity found")
    today = today or date.today()
    age = (today - last_seen).days
    if age < 0:
        return Verdict(UNCLEAR, source or "date", f"future date {last_seen}")
    if age <= ACTIVITY_WINDOW_DAYS:
        return Verdict(YES, source or "date", f"{last_seen} ({age}d ago)")
    return Verdict(NO, source or "date", f"{last_seen} ({age}d ago)")


def latest_activity_date(text: str, *, page_url: str = "",
                         today: date | None = None) -> tuple[date | None, str]:
    """The most recent real date on a fetched page, and where it came from.

    **Measured on the first real batch: a coach's own website almost never
    carries one.** Across nine sites and about 220,000 characters of body text
    this found zero usable dates — six raw matches on one site, all of them
    year-less or in the future. So this settles the floor when a page happens to
    be dated, and honestly returns `None` the rest of the time, which
    `check_active` turns into `unclear` and passes.

    The signal that does exist is LinkedIn: the hook stage pulled dated posts
    for four of twelve leads on that same batch, several inside a week. That is
    the real evidence for this floor, and it arrives one stage later than the
    floor runs. Feed the verified hook's date back as `last_activity` rather
    than expecting a site read to produce it — see the outbound-batch skill.

    `check_active` wants a date; a worker reading a page has text. This is the
    bridge, and it is mechanical on purpose — "when did they last post" is a
    question a regex can settle, and a settled question is one fewer thing a
    worker can be talked into by a page that merely feels busy.

    Copyright lines and future dates are excluded: "© 2026" is the footer's
    opinion of the current year, not evidence anyone did anything. A date with
    no year written on it is excluded too — `extract_dates` assumes the current
    year for those, which would read a "March 14" from three years ago as this
    March and pass a dead site through the floor.

    Returns `(None, reason)` when nothing usable was found, which `check_active`
    turns into `unclear` rather than a kill.
    """
    from audit.extract import extract_dates

    today = today or date.today()
    try:
        hits = extract_dates(text or "", today=today, page_url=page_url)
    except Exception as exc:                      # a malformed page is not a kill
        return None, f"date scan failed ({type(exc).__name__})"

    usable = [h for h in hits
              if not h.get("year_assumed")
              and h.get("days_past", -1) >= 0
              and not _COPYRIGHT_NEAR.search(h.get("near", ""))]
    if not usable:
        return None, "no dated activity found"

    best = min(usable, key=lambda h: h["days_past"])
    parsed = date.fromisoformat(best["parsed"])
    return parsed, f"{page_url or 'page text'}: {best['raw']!r}"


# ------------------------------------------------------------------- capture


def classify_coach_type(*, linkedin_text: str = "", site_text: str = "") -> tuple[str, str]:
    """Which segment's identity line this lead should draw.

    **LinkedIn wins when the two disagree.** A real case: a coach whose site
    read as Life/Mindset ("Life Design Method") had a LinkedIn headline that
    said "Leadership & Performance Coach" aimed at corporate teams. Two offers
    to two audiences under one name. LinkedIn is the paid-facing profile and is
    usually the more explicit about what they actually sell.

    Pass `linkedin_text` the headline, not a page dump. The loose fallback below
    only runs against it, and it is only safe because a headline is short and
    deliberate.
    """
    def first_match(text: str, patterns=_TYPE_PATTERNS) -> str:
        for label, pattern in patterns:
            if pattern.search(text or ""):
                return label
        return ""

    from_linkedin = first_match(linkedin_text)
    if from_linkedin:
        site_says = first_match(site_text)
        if site_says and site_says != from_linkedin:
            return from_linkedin, f"linkedin (site said {site_says})"
        return from_linkedin, "linkedin"

    from_site = first_match(site_text)
    if from_site:
        return from_site, "site"

    # Last resort: the headline again, allowing words between the segment and
    # "coach". "Career and Work-Life Balance Coach" is unambiguous to a reader
    # and invisible to a pattern that wants the two words adjacent — three of
    # twelve on the first real list. Tried only after everything strict has
    # failed, so it can never override a confident match.
    loose = first_match(linkedin_text, _TYPE_PATTERNS_LOOSE)
    if loose:
        return loose, "linkedin (loose headline match)"
    return "", ""


def classify_sells_to(*, linkedin_text: str = "", site_text: str = "") -> tuple[str, str]:
    """corporates | individuals | "" — collected, never inferred from a hook.

    The old pipeline guessed this from hook keywords and coach type, and its own
    doc called it the sharpest divide on the list and expected the guess to be
    wrong on edge cases. So this reads the lead's own words and returns empty
    rather than guessing: an unknown `sells_to` draws a generic identity line,
    which is weaker than an exact match and much stronger than a wrong one.
    """
    for label, text in (("linkedin", linkedin_text), ("site", site_text)):
        corporate = bool(_CORPORATE_MARKERS.search(text or ""))
        individual = bool(_INDIVIDUAL_MARKERS.search(text or ""))
        if corporate and individual:
            # This source says both, so it says nothing. Fall through to the
            # next source rather than letting one half of a contradiction win.
            continue
        if corporate:
            return "corporates", label
        if individual:
            return "individuals", label

    return "", ""


def qualify(*, city: str = "", domain: str = "", headline: str = "",
            site_text: str = "", linkedin_text: str = "",
            last_activity: date | None = None, today: date | None = None,
            audience_size: int | None = None,
            top_program_price_aed: int | None = None,
            solo: str = UNCLEAR) -> Qualification:
    """Run all three floors and capture the rest. Never fetches anything."""
    combined = "\n".join([site_text, linkedin_text, headline])
    coach_type, type_source = classify_coach_type(
        linkedin_text=linkedin_text, site_text=site_text)
    sells_to, sells_source = classify_sells_to(
        linkedin_text=linkedin_text, site_text=site_text)

    return Qualification(
        uae_based=check_uae(city=city, text=combined, domain=domain),
        is_coach=check_coach(headline=headline, text=combined),
        active_recent=check_active(last_seen=last_activity, today=today),
        coach_type=coach_type,
        coach_type_source=type_source,
        sells_to=sells_to,
        sells_to_source=sells_source,
        audience_size=audience_size,
        top_program_price_aed=top_program_price_aed,
        solo=solo,
    )


def window(today: date | None = None) -> tuple[date, date]:
    """The activity window, for a worker that needs to state it out loud."""
    today = today or date.today()
    return today - timedelta(days=ACTIVITY_WINDOW_DAYS), today
