"""Checkout platform and revenue-maximizing element detection.

Platform detection requires a signal that can only mean that platform —
a platform-owned domain in a link/form/script, or a markup fingerprint
unique to it. Generic fragments are banned: the old `cf-` signal matched
Cloudflare artifacts on random news sites ("clickfunnels"), bare
`/checkout` matched any page that merely links to a checkout ("kajabi"),
and bare `/cart` made everything "shopify".
"""

import re
from bs4 import BeautifulSoup


# (platform, url_signals, markup_signals)
# url_signals match against href/action/src attributes; markup_signals
# against the raw HTML. Every signal must be platform-unique.
_PLATFORM_SIGNALS: list[tuple[str, list[str], list[str]]] = [
    ("kajabi",       ["kajabi.com", "mykajabi.com"], ["kajabi-content", "kajabi-app"]),
    ("thrivecart",   ["thrivecart.com", "thrv.co"], []),
    ("stripe",       ["buy.stripe.com", "checkout.stripe.com"], []),
    ("gumroad",      ["gumroad.com", "gum.co"], []),
    ("samcart",      ["samcart.com"], []),
    ("clickfunnels", ["clickfunnels.com", "myclickfunnels.com"], ["cfcdn.com"]),
    ("kartra",       ["kartra.com"], []),
    ("payhip",       ["payhip.com"], []),
    ("lemonsqueezy", ["lemonsqueezy.com"], []),
    ("stan",         ["stan.store"], []),
    ("gohighlevel",  ["gohighlevel.com", "leadconnectorhq.com", "msgsndr.com"], []),
    ("woocommerce",  [], ["woocommerce", "wc-ajax", "wp-content/plugins/woocommerce"]),
    ("shopify",      ["cdn.shopify.com", "myshopify.com"], ["shopify-section", "cdn.shopify.com"]),
    ("squarespace",  [], ["squarespace-commerce", "sqs-add-to-cart"]),
]

_ORDER_BUMP_PATTERNS = re.compile(
    r"order[\s_-]?bump|add[\s_-]?on|include.{0,30}for only|one[\s_-]?time[\s_-]?offer",
    re.I,
)

_UPSELL_PATTERNS = re.compile(
    r"upsell|upgrade|wait.{0,20}special|one[\s_-]?time[\s_-]?upgrade"
    r"|before you go|exclusive offer|special deal",
    re.I,
)

_DOWNSELL_PATTERNS = re.compile(
    r"downsell|no thanks|not ready|maybe later|smaller.{0,20}option",
    re.I,
)

# Signals that the page itself transacts (vs merely linking somewhere that does)
_TRANSACTS_RE = re.compile(
    r"add[\s_-]?to[\s_-]?cart|payment|card number|billing|order summary"
    r"|pay\s?&\s?book|pay now|complete (?:your )?(?:order|purchase)|place order",
    re.I,
)


def _detect_platform(html: str, soup: BeautifulSoup) -> str | None:
    lower = html.lower()
    all_urls = " ".join(
        (t.get("href", "") or t.get("action", "") or t.get("src", "") or "")
        for t in soup.find_all(["a", "form", "script", "iframe"])
    ).lower()

    for platform, url_signals, markup_signals in _PLATFORM_SIGNALS:
        for sig in url_signals:
            if sig in all_urls:
                return platform
        for sig in markup_signals:
            if sig in lower:
                return platform
    return None


def check_checkout(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")

    platform = _detect_platform(html, soup)
    transacts = bool(_TRANSACTS_RE.search(text))
    order_bump = bool(_ORDER_BUMP_PATTERNS.search(text) or _ORDER_BUMP_PATTERNS.search(html))
    upsell = bool(
        _UPSELL_PATTERNS.search(text)
        or _DOWNSELL_PATTERNS.search(text)
    )

    return {
        "platform":            platform,
        "transacts":           transacts,
        "order_bump_detected": order_bump,
        "upsell_detected":     upsell,
    }
