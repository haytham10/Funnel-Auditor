"""Two-pass dedupe against everyone already contacted.

This is the step with the worst failure mode in the whole machine, and the
cheapest. On the last real batch it caught 7 people who would otherwise have
received a cold template on an existing thread, two of them live warm
conversations. A cold opener landing on someone mid-negotiation is not a
wasted send, it is the only kind of send that actively destroys something.

**Pass 1 runs on name and domain, BEFORE any paid call.** This ordering is the
bug the old pipeline shipped: dedupe ran last, so an already-excluded lead paid
for all 8 Apify calls and was then thrown away. A text match costs nothing and
belongs first.

**Pass 2 runs on email, AFTER research has found one.** Pass 1 cannot catch a
married name, a business name that doesn't resemble a person name, or an
address that only matches once you know it. Both passes are needed; neither is
sufficient.

Matching is deliberately loose on names and exact on domains and addresses.
A false positive costs one lead we skip. A false negative costs a relationship.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from audit.urls import registrable_domain

_PARTICLES = {"van", "von", "de", "del", "della", "da", "di", "du", "la",
              "le", "el", "al", "bin", "ibn", "abu", "mac", "mc", "st"}
_TITLES = {"dr", "mr", "mrs", "ms", "miss", "prof", "professor", "coach",
           "sir", "eng", "phd", "mba", "pcc", "acc", "mcc", "icf"}


def name_key(name: str) -> str:
    """A comparable form of a person's name.

    Strips accents, titles, suffixes and punctuation, lowercases, and sorts the
    remaining tokens so "Sarah Al-Mansouri" and "Al Mansouri, Sarah" collapse
    to the same key. Particles are kept because dropping them merges genuinely
    different people (de Vries and Vries are not the same surname).
    """
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s]", " ", text.lower())
    # Digits are kept. They are rare in a real name, and dropping them merges
    # any two names that differ only by a number into one key.
    tokens = [t for t in text.split() if t and t not in _TITLES]
    return " ".join(sorted(tokens))


def email_key(address: str) -> str:
    """Normalized address. Gmail dots and +tags are the same mailbox."""
    address = (address or "").strip().lower()
    if "@" not in address:
        return ""
    local, _, domain = address.partition("@")
    local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def domain_key(url_or_domain: str) -> str:
    if not url_or_domain:
        return ""
    return registrable_domain(url_or_domain)


@dataclass
class KnownContact:
    """One row of the Contacted-Before wall.

    `warm` marks a live or previously-replying thread. Those are not merely
    duplicates to skip quietly, they are the ones worth shouting about, so the
    report separates them.
    """
    name: str = ""
    email: str = ""
    domain: str = ""
    status: str = ""
    warm: bool = False
    track: str = ""


class ContactWall:
    """Everyone already contacted, on any track, ever.

    Built from the CRMs rather than a text file, so it stays true without
    anyone remembering to update it.
    """

    def __init__(self, contacts: list[KnownContact] | None = None):
        self.by_name: dict[str, KnownContact] = {}
        self.by_email: dict[str, KnownContact] = {}
        self.by_domain: dict[str, KnownContact] = {}
        for contact in contacts or []:
            self.add(contact)

    def add(self, contact: KnownContact) -> None:
        if contact.name:
            self.by_name.setdefault(name_key(contact.name), contact)
        if contact.email:
            self.by_email.setdefault(email_key(contact.email), contact)
        if contact.domain:
            self.by_domain.setdefault(domain_key(contact.domain), contact)

    def __len__(self) -> int:
        return len(set(id(c) for c in
                       list(self.by_name.values())
                       + list(self.by_email.values())
                       + list(self.by_domain.values())))

    @classmethod
    def from_records(cls, records: list[dict]) -> "ContactWall":
        """Build from Airtable/Notion rows the skill layer fetched.

        Accepts the field spellings both CRMs use, so the caller can hand over
        rows from either without reshaping them first.
        """
        wall = cls()
        for row in records:
            status = str(row.get("Status") or row.get("status") or "")
            wall.add(KnownContact(
                name=row.get("Contact Name") or row.get("Name") or row.get("name") or "",
                email=row.get("Email") or row.get("email") or "",
                domain=row.get("Site URL") or row.get("Domain") or row.get("domain") or "",
                status=status,
                warm=_is_warm(status),
                track=row.get("Track") or row.get("track") or "",
            ))
        return wall


# Any status that means a human was on the other end of this thread.
_WARM_STATUSES = {
    "reply received", "call booked", "offer sent", "won", "lost",
    "price discovery sent", "leak fix sold", "leak fix delivered",
    "replied", "warm", "in conversation",
}


def _is_warm(status: str) -> bool:
    return (status or "").strip().lower() in _WARM_STATUSES


@dataclass
class DupeHit:
    lead_name: str
    matched_on: str          # name | domain | email
    contact: KnownContact

    @property
    def warm(self) -> bool:
        return self.contact.warm

    def line(self) -> str:
        flag = "WARM THREAD" if self.warm else "already contacted"
        where = f"{self.contact.status or 'unknown status'}"
        return (f"{self.lead_name}: {flag}, matched on {self.matched_on} "
                f"({where})")


def check_early(lead, wall: ContactWall) -> DupeHit | None:
    """Pass 1. Name and domain only. Runs BEFORE any paid call."""
    key = name_key(getattr(lead, "name", "") or "")
    if key and key in wall.by_name:
        return DupeHit(lead.name, "name", wall.by_name[key])
    domain = domain_key(getattr(lead, "site_url", "") or "")
    if domain and domain in wall.by_domain:
        return DupeHit(lead.name, "domain", wall.by_domain[domain])
    return None


def check_late(lead, wall: ContactWall) -> DupeHit | None:
    """Pass 2. Email only, once research has actually found one."""
    key = email_key(getattr(lead, "email", "") or "")
    if key and key in wall.by_email:
        return DupeHit(lead.name, "email", wall.by_email[key])
    return None


def partition(leads: list, wall: ContactWall, *, stage: str = "early") -> dict:
    """Split a batch into what proceeds and what stops here.

    Also catches duplicates WITHIN the batch itself: 7 of 50 survivors on the
    last list were the same people arriving from two overlapping directories,
    and two coaches receiving the same email is the tell that the whole thing
    was generated.
    """
    check = check_early if stage == "early" else check_late
    seen_name: dict[str, str] = {}
    seen_email: dict[str, str] = {}

    clear, dupes, internal = [], [], []
    for lead in leads:
        hit = check(lead, wall)
        if hit:
            dupes.append(hit)
            continue

        nkey = name_key(getattr(lead, "name", "") or "")
        ekey = email_key(getattr(lead, "email", "") or "")
        if nkey and nkey in seen_name:
            internal.append(f"{lead.name}: duplicate of {seen_name[nkey]} in this same batch")
            continue
        if ekey and ekey in seen_email:
            internal.append(f"{lead.name}: same address as {seen_email[ekey]} in this same batch")
            continue

        if nkey:
            seen_name[nkey] = lead.name
        if ekey:
            seen_email[ekey] = lead.name
        clear.append(lead)

    return {
        "clear": clear,
        "dupes": dupes,
        "internal": internal,
        "warm_hits": [d for d in dupes if d.warm],
    }


def report(result: dict, *, stage: str = "early") -> list[str]:
    """The quotable output. Warm hits are listed individually and first."""
    lines = [
        f"DEDUPE {stage}: {len(result['clear'])} clear, "
        f"{len(result['dupes'])} already contacted, "
        f"{len(result['internal'])} duplicated inside the batch"
    ]
    for hit in result["warm_hits"]:
        lines.append(f"  STOP  {hit.line()}")
    for hit in result["dupes"]:
        if not hit.warm:
            lines.append(f"  skip  {hit.line()}")
    for note in result["internal"]:
        lines.append(f"  skip  {note}")
    return lines
