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
# `ad` and `ae` were in this list and are not. Both are two letters that occur
# constantly in ordinary prose, and `_stated_residence` matches on equality with
# a captured 1-2 word group — so "based in Ae" is not the failure, but the
# tokens carry no signal a real bio would ever intend and every other entry here
# is unambiguous. Dropping them costs nothing and removes two ways to be right
# by accident.
UAE_SHORTHAND = (
    "dxb", "auh", "shj", "rak", "uaq", "fjr", "awz",
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
# Evidence they SELL it, rather than that the word appears. A hobby, a job
# title containing "coach", or a page about coaching all match the markers
# above; a booking page and a programme do not appear by accident.
COACH_OFFER_MARKERS = (
    "book a call", "book a session", "discovery call", "free consultation",
    "1:1", "one-to-one", "one on one", "my clients", "my programme",
    "my program", "work with me", "packages", "coaching package",
    "coaching programme", "coaching program", "sessions", "per session",
    "intake form", "apply to work", "client results", "testimonials",
)
# Occupations that are plainly something else. A stated one of these, with no
# coach marker and no offer anywhere, is the only thing that earns a `no` —
# see `check_coach`. Every entry was a real row on the first batch or is the
# same shape as one: a Bacardi retail supervisor, flydubai cabin crew, a
# Middlesex lecturer, and an airline CEO whose goalie coaching is a hobby.
NON_COACH_OCCUPATIONS = (
    "cabin crew", "flight attendant", "pilot", "first officer",
    "retail supervisor", "store manager", "sales assistant", "cashier",
    "lecturer", "professor", "phd student", "postdoc", "teaching assistant",
    "software engineer", "data scientist", "developer", "accountant",
    "nurse", "surgeon", "dentist", "pharmacist", "lawyer", "solicitor",
    "estate agent", "real estate agent", "receptionist", "chef", "barista",
    "driver", "security guard", "warehouse", "logistics coordinator",
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
    # `scale` used to be a bare alternative here — the `\b` binds only to the
    # first branch — so it matched "scaled", "at scale", and inside "rescale",
    # and it pulled two fitness coaches into Business on the first batch. A
    # segment decides which proof line a real email carries, so a false
    # positive here is a wrong reference group in a stranger's inbox.
    ("Business", re.compile(
        r"\bbusiness coach|\bfounder coach|\bentrepreneur coach|"
        r"\bscal(?:e|ing)\s+(?:your|their|a|my)\s+(?:business|company|agency|team)", re.I)),
    ("Career", re.compile(
        r"\bcareer coach|\bjob search|\binterview (?:prep|coach|skills)|"
        r"\bcv\b|\bresume\b", re.I)),
    # Same shape: `wellness` alone pulled a brand strategist into Health off a
    # sentence that had nothing to do with them.
    ("Health", re.compile(
        r"\bhealth coach|\bnutrition(?:ist|\s+coach)|\bwellness (?:coach|practice|program|programme)|"
        r"\bhormone|\bgut\b", re.I)),
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
              source: str = "", headline: str = "", location: str = "") -> Verdict:
    """Based in the UAE, not merely serving it.

    The distinction is load-bearing: a coach in London selling to Dubai has a
    different market, a different price ceiling, and no reason to recognise the
    reference group in the identity beat.

    **Two haystacks, not one.** `city`, `headline` and `location` are fields
    about the SUBJECT — their own stated location — and they settle this either
    way. `text` is a page of prose that happens to be on their site, and it may
    only ever produce a `yes`.

    That split is the fix for a real pair of failures on the first batch. The
    old version joined everything into one blob, so a lead was killed by "based
    in Singapore" describing a PAST EMPLOYER, and another passed on a "dubai"
    that came from an unrelated part of the page. A page can say anything about
    anyone; a location field is about this person. Both errors were invisible,
    and the kill was permanent.
    """
    subject = " ".join([city, headline, location]).lower()
    haystack = " ".join([city, headline, location, text, domain]).lower()
    if not haystack.strip():
        return Verdict(UNCLEAR, source or "no data")

    for phrase in UAE_NEGATIVE:
        if phrase in haystack:
            return Verdict(UNCLEAR, source or "text",
                           f"claims reach, not residence: {phrase}")

    # A subject-owned field naming a UAE place settles it outright, ahead of
    # anything in the prose.
    for marker in UAE_CITIES:
        if subject and re.search(rf"\b{re.escape(marker)}\b", subject):
            return Verdict(YES, source or "location field", marker)

    # An explicit statement of residence is checked before the loose scan, and
    # settles it either way. It used to run last — so "I am a coach based in
    # Toronto. Read my essay at nowhere.aeon.co" returned YES on ".ae", and "Our
    # client Marina came to us from Manchester" returned YES on "marina". A
    # coach who has written down where they live outranks a word that happened
    # to appear in a URL.
    stated = _stated_residence(text, source, subject_fields=subject)
    # An `unclear` from a sentence about somebody else is not an answer, it is
    # the absence of one — so it falls through to the marker scan below rather
    # than short-circuiting. "Leadership coach in Dubai. Previously at Acme,
    # based in Singapore." should read the Dubai.
    if stated is not None and stated.value != UNCLEAR:
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
    # The second `_stated_residence` call that used to be here was dead: the
    # branch above returns for every case it can produce a value in.
    return Verdict(UNCLEAR, source or "text")


# Evidence a "based in X" sentence is about SOMEBODY ELSE. On the first batch
# "based in Singapore" describing a past employer killed a real lead, and a kill
# is permanent and invisible.
#
# Note the direction. The default stays "this is about them", because "Based in
# Manchester." with no pronoun is the ordinary bio form and requiring a first
# person would spare every one of those — weakening the only floor that can
# actually drop a row. So the burden is on the exception: something in the
# clause just before it has to name a different subject.
_THIRD_PARTY = re.compile(
    r"\b(client|clients|customer|employer|company|companies|team|teams|partner|"
    r"partners|colleague|colleagues|agency|firm|school|studio|brand|"
    r"headquarters|office|offices|he|she|they|his|her|their|"
    r"previously|formerly|worked at|worked with|joined|graduated from)\b"
    r"[^.]{0,60}?\b(?:based|located|living|headquartered)\s+in\b", re.I)


def _stated_residence(text: str, source: str = "",
                      subject_fields: str = "") -> "Verdict | None":
    """A "based in X" line, resolved. None when the text has no such line.

    A `NO` needs the sentence to be about the SUBJECT, which is the default — a
    bare "Based in Manchester." is the ordinary bio form. It is spared only when
    something just before it names a different subject (a past employer, a
    client, a third-person pronoun), or when the lead's own location field says
    somewhere else and the two disagree.
    """
    other = re.search(
        r"\b(?:based|located|living|headquartered)\s+in\s+(?:the\s+)?"
        r"([A-Za-z]+(?:[ -][A-Za-z]+)?)",
        text or "", re.I,
    )
    if other:
        # Their own location field naming a different place outranks a sentence
        # in the prose. Two claims about where one person is, and the field is
        # the one that is definitely about them.
        contradicted = bool(
            subject_fields.strip()
            and other.group(1).strip().lower() not in subject_fields)
        about_subject = not _THIRD_PARTY.search(text or "") and not contradicted
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
        # "Based in Manchester, UK" — the regex takes two words, so the leading
        # word counts too before giving up on a place we do know.
        first_word = lowered.split()[0] if lowered.split() else ""
        foreign = lowered in FOREIGN_PLACES or first_word in FOREIGN_PLACES
        if foreign and about_subject:
            return Verdict(NO, source or "text", other.group(0))
        if foreign:
            return Verdict(
                UNCLEAR, source or "text",
                f"{other.group(0)} — but that sentence is about somebody else, "
                f"or their own location field says otherwise")
        return Verdict(UNCLEAR, source or "text",
                       f"{other.group(0)} — place not recognised either way")
    return None


def check_coach(*, headline: str = "", text: str = "", source: str = "") -> Verdict:
    """Actually sells coaching, rather than merely using the word.

    The docstring said that and the code did the opposite: it substring-matched
    "coach" and had three returns, none of which could be `NO`. It was
    documented as a hard floor and was structurally incapable of rejecting
    anyone, so workers in five slices of the first batch hand-overrode it with
    sourced evidence — a Bacardi retail supervisor, flydubai cabin crew, a
    Middlesex lecturer, an airline CEO whose goalie coaching is a stated hobby.

    Now it can say no, and the bar for that is deliberately high: a stated
    non-coach occupation AND no coach marker anywhere AND nothing that looks
    like a coaching offer. All three, because a false kill is permanent and
    invisible while a false pass costs one research call — and plenty of real
    coaches also have a day job.

    Matching is word-bounded. `"coach" in haystack` fires on "coachella",
    "stagecoach" and any URL containing the letters, which is how a floor comes
    to pass everything.
    """
    haystack = " ".join([headline, text]).lower()
    if not haystack.strip():
        return Verdict(UNCLEAR, source or "no data")

    # A coach word anywhere is still a `yes`, including the airline CEO whose
    # goalie coaching is a weekend hobby. Telling that apart from "I coach
    # founders" needs context this function does not have, and getting it wrong
    # costs a real lead permanently against one wasted research call. It stays
    # a false pass on purpose; the research worker overrides it with a source.
    for marker in COACH_MARKERS:
        if re.search(rf"\b{re.escape(marker)}\b", haystack):
            return Verdict(YES, source or "text", marker)

    offer = next((m for m in COACH_OFFER_MARKERS
                  if re.search(rf"\b{re.escape(m)}\b", haystack)), None)
    if offer:
        # No coach word, but something is plainly being sold one-to-one. Not a
        # `yes` — this is a shape, not a claim — but nowhere near a `no`.
        return Verdict(UNCLEAR, source or "text", f"no coach word, but: {offer}")

    other = next((o for o in NON_COACH_OCCUPATIONS
                  if re.search(rf"\b{re.escape(o)}\b", haystack)), None)
    if other:
        return Verdict(NO, source or "text", f"states another occupation: {other}")
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


def activity_from_observations(observations, *,
                               today: date | None = None) -> tuple[date | None, str]:
    """The newest observation date, but ONLY when it clears the floor.

    F3 of docs/proposals/2026-08-01-hook-retrieval.md. `latest_activity_date`
    below found zero usable dates across nine sites and ~220,000 characters, so
    `active_recent` came back `unclear` for effectively every lead and the floor
    did nothing. The evidence it wanted has existed since P1: `research-worker`
    returns schema-checked `Observation`s carrying `published_at`, and it
    returns them before it calls this floor. The date was already in its hand.

    **An observation can only ever turn `unclear` into `yes`.** It is never
    allowed to argue the other way, and that restriction is the whole design of
    this function rather than a caller's discipline. `check_active` returns `NO`
    for a stale date — so handing it the newest of a stale set would open a
    brand-new kill surface at the one floor built not to have one, and it would
    open it on the weakest possible evidence: that the pages we happened to
    retrieve were old. D4 is the rule, and giving a floor better evidence is not
    a reason to weaken it. A lead whose observations are all stale comes back
    from here exactly as a lead with no observations at all does, and falls
    through to the page-text path unchanged.

    So a date outside the window returns `(None, why)` — and `why` says the
    dates were there and were old, because that is worth reading in a report
    even though it changes no verdict.
    """
    today = today or date.today()
    dated: list[tuple[date, str]] = []
    for obs in observations or []:
        raw = (obs.get("published_at") if isinstance(obs, dict)
               else getattr(obs, "published_at", "")) or ""
        try:
            when = date.fromisoformat(str(raw).strip())
        except ValueError:
            continue                      # the schema gate's job, not this one
        if when > today:
            continue                      # a date nobody could have read
        url = (obs.get("url") if isinstance(obs, dict)
               else getattr(obs, "url", "")) or "an observation"
        dated.append((when, url))

    if not dated:
        return None, "no dated observation"
    when, url = max(dated, key=lambda pair: pair[0])
    age = (today - when).days
    if age <= ACTIVITY_WINDOW_DAYS:
        return when, f"{url} ({when}, {age}d ago)"
    return None, (f"newest of {len(dated)} observation(s) is {when} ({age}d ago) "
                  f"— too old to settle the floor, and never a kill")


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
    for four of twelve leads on that same batch, several inside a week. That
    used to arrive one stage after the floor ran, and the repair was a manual
    write-back an orchestrator had to remember. It is not any more —
    `activity_from_observations` above reads the dates the research worker
    already retrieved, at the stage where the floor actually runs. This stays as
    the rung below it, for a lead whose only evidence is a page.

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
