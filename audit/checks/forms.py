"""Email capture form detection."""

import re
from bs4 import BeautifulSoup


_EMAIL_PLATFORMS = {
    "kajabi":      ["kajabi.com", "kajabi-content.com"],
    "convertkit":  ["convertkit.com", "ck.page", "api.convertkit.com"],
    "mailchimp":   ["mailchimp.com", "list-manage.com", "chimpstatic.com"],
    "activecampaign": ["activecampaign.com", "activehosted.com"],
    "klaviyo":     ["klaviyo.com", "klaviyo-forms"],
    "aweber":      ["aweber.com", "awlist"],
    "drip":        ["getdrip.com", "drip.com"],
    "flodesk":     ["flodesk.com"],
    "beehiiv":     ["beehiiv.com"],
}

_EMAIL_INPUT_ATTRS = re.compile(r"email", re.I)


def _has_email_input(form) -> bool:
    for inp in form.find_all("input"):
        t = (inp.get("type") or "").lower()
        name = inp.get("name") or ""
        placeholder = inp.get("placeholder") or ""
        if t == "email":
            return True
        if _EMAIL_INPUT_ATTRS.search(name) or _EMAIL_INPUT_ATTRS.search(placeholder):
            return True
    return False


def _detect_embed_platform(html: str) -> str | None:
    lower = html.lower()
    for platform, markers in _EMAIL_PLATFORMS.items():
        if any(m in lower for m in markers):
            return platform
    return None


def check_forms(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    form_present = any(_has_email_input(f) for f in soup.find_all("form"))
    platform = _detect_embed_platform(html)

    # If no native form found but an embed platform is detected, still flag it
    if platform and not form_present:
        form_present = True

    return {
        "form_present": form_present,
        "platform_detected": platform,
    }
