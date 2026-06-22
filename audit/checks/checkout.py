"""Checkout platform and revenue-maximizing element detection."""

import re
from bs4 import BeautifulSoup


_PLATFORM_SIGNALS: list[tuple[str, list[str]]] = [
    ("kajabi",      ["kajabi.com/checkout", "/checkout", "kajabi-content"]),
    ("thrivecart",  ["thrivecart.com", "thrv.co"]),
    ("stripe",      ["buy.stripe.com", "checkout.stripe.com"]),
    ("gumroad",     ["gumroad.com", "gum.co"]),
    ("samcart",     ["samcart.com"]),
    ("clickfunnels",["clickfunnels.com", "cf-",]),
    ("kartra",      ["kartra.com/checkout"]),
    ("payhip",      ["payhip.com"]),
    ("lemonsqueezy",["lemonsqueezy.com", "lemon.squeezy"]),
    ("stan",        ["stan.store/checkout"]),
    ("woocommerce", ["woocommerce", "add-to-cart"]),
    ("shopify",     ["shopify.com/cart", "/cart", "shopify"]),
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


def _detect_platform(html: str, soup: BeautifulSoup) -> str | None:
    lower = html.lower()
    # Check <a> hrefs and <form> actions first (more reliable)
    all_urls = [
        t.get("href", "") or t.get("action", "") or t.get("src", "")
        for t in soup.find_all(["a", "form", "script", "iframe"])
    ]
    combined_urls = " ".join(all_urls).lower()

    for platform, signals in _PLATFORM_SIGNALS:
        for sig in signals:
            if sig in combined_urls or sig in lower:
                return platform
    return None


def check_checkout(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")

    platform = _detect_platform(html, soup)
    order_bump = bool(_ORDER_BUMP_PATTERNS.search(text) or _ORDER_BUMP_PATTERNS.search(html))
    upsell = bool(
        _UPSELL_PATTERNS.search(text)
        or _DOWNSELL_PATTERNS.search(text)
    )

    return {
        "platform":            platform,
        "order_bump_detected": order_bump,
        "upsell_detected":     upsell,
    }
