MAX_PAGES = 8            # bio page + funnel pages, before the checkout hop
MAX_CHECKOUT_HOPS = 3    # extra pages crawled from buy/enroll links on sales pages
SCREENSHOT_DIR = "./screenshots"
EVIDENCE_DIR = "./evidence"

# Kept for backward compat with older scripts
MAX_CRAWL_DEPTH = MAX_PAGES

FUNNEL_KEYWORDS = [
    "course", "coaching", "program", "masterclass", "workshop", "training",
    "freebie", "free", "guide", "checklist", "template", "download",
    "optin", "opt-in", "opt_in", "subscribe", "signup", "sign-up",
    "sales", "buy", "enroll", "join", "offer", "product", "shop",
    "booking", "book", "schedule", "call", "consult",
    "webinar", "challenge", "bootcamp", "membership",
    "kajabi", "teachable", "thinkific", "podia", "stan.store",
    "samcart", "clickfunnels", "kartra", "systeme",
    "gumroad", "payhip", "lemon",
]

CHECKOUT_LINK_KEYWORDS = [
    "checkout", "buy", "enroll", "cart", "order", "register",
    "purchase", "pay", "get-access", "get access", "sign-up-now",
]

NOISE_DOMAINS = [
    "youtube.com", "youtu.be",
    "instagram.com", "facebook.com", "twitter.com", "x.com",
    "tiktok.com", "pinterest.com", "snapchat.com",
    "spotify.com", "podcasts.apple.com", "anchor.fm",
    "linkedin.com",
    "open.spotify.com",
]

BIO_LINK_PLATFORMS = {
    "linktree": ["linktr.ee", "linktree.com"],
    "stan": ["stan.store"],
    "beacons": ["beacons.ai"],
}
