"""Tracking pixel detection."""

from bs4 import BeautifulSoup


def check_pixels(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    scripts = [
        (s.get("src") or "") + s.get_text()
        for s in soup.find_all("script")
    ]
    combined = " ".join(scripts)

    meta   = "connect.facebook.net" in combined
    ga4    = "gtag/js" in combined or "google-analytics.com/g/collect" in combined
    gtm    = "googletagmanager.com/gtm.js" in combined
    tiktok = "analytics.tiktok.com" in combined

    return {
        "meta": meta,
        "ga4": ga4,
        "gtm": gtm,
        "tiktok": tiktok,
        "any_present": any([meta, ga4, gtm, tiktok]),
    }
