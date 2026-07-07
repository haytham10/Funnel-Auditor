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
    "google.com", "goo.gl", "maps.app.goo.gl",
    "apple.com", "play.google.com",
    "amazon.com", "amazon.co.uk", "amazon.com.au", "amzn.to",
]

BIO_LINK_PLATFORMS = {
    "linktree": ["linktr.ee", "linktree.com"],
    "stan": ["stan.store"],
    "beacons": ["beacons.ai"],
}

# External domains that are part of a lead's own funnel when linked from her
# site: booking tools, course/checkout platforms, payment pages. Any OTHER
# external domain linked from the lead's site (press mentions, a web
# designer's credit, a podcast host) is NOT her funnel and must not be
# crawled — it gets listed as an external reference instead. This is the
# rule that keeps radio-station homepages and site-builder portfolios out
# of the walk.
EXTERNAL_FUNNEL_PLATFORMS = [
    "calendly.com", "acuityscheduling.com", "youcanbook.me", "tidycal.com",
    "savvycal.com", "cal.com", "practicebetter.io", "healthie.net",
    "kajabi.com", "mykajabi.com", "teachable.com", "thinkific.com",
    "podia.com", "kartra.com", "systeme.io", "clickfunnels.com",
    "samcart.com", "thrivecart.com", "gumroad.com", "payhip.com",
    "lemonsqueezy.com", "stan.store", "whop.com", "skool.com",
    "buy.stripe.com", "checkout.stripe.com", "paypal.com",
    "eventbrite.com", "eventbrite.co.uk", "lu.ma",
    "mailchi.mp", "ck.page", "convertkit.com", "flodesk.com",
    "subscribepage.com", "landing.mailerlite.com",
    "gohighlevel.com", "app.gohighlevel.com",
]

# Same-domain paths that never advance a funnel walk: auth, account,
# search, wp plumbing, legal. Crawling a login page burns a page-budget
# slot to learn nothing (the login page's existence is already visible
# from the link label on the bio page).
SKIP_PATH_RE = (
    r"/(log-?in|sign-?in|auth|account|my-account|members?-?only|search|"
    r"wp-admin|wp-login|privacy|terms|cookie|refund|disclaimer|sitemap)(/|$|\?)"
)

# Same-domain path hints that mark a page as offer-bearing — these get the
# page budget first (the whole point of the walk is offers, pricing, and
# booking flows, not the About page).
OFFER_PATH_HINTS = [
    "work-with", "workwith", "services", "pricing", "prices", "invest",
    "offers", "course", "program", "shop", "store", "book", "booking",
    "schedule", "consult", "coaching", "membership", "join", "enroll",
    "checkout", "cart", "buy", "class", "intensive", "package",
]
