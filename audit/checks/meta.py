"""OG tags and mobile viewport detection."""

from bs4 import BeautifulSoup


def check_meta(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    def _og(prop: str) -> str | None:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if tag:
            return (tag.get("content") or "").strip() or None
        return None

    twitter_card = bool(
        soup.find("meta", attrs={"name": "twitter:card"})
        or soup.find("meta", property="twitter:card")
    )

    viewport_tag = soup.find("meta", attrs={"name": "viewport"})
    mobile_viewport = bool(viewport_tag and "width=device-width" in (viewport_tag.get("content") or ""))

    return {
        "og_title":       _og("og:title"),
        "og_description": _og("og:description"),
        "og_image":       _og("og:image"),
        "twitter_card":   twitter_card,
        "mobile_viewport": mobile_viewport,
    }
