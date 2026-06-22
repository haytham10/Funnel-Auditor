"""Page speed bucketing and asset bloat proxy."""

from bs4 import BeautifulSoup


def check_speed(html: str, base_url: str, load_time_ms: float = 0.0) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    img_count    = len(soup.find_all("img"))
    script_count = len(soup.find_all("script"))
    link_count   = len(soup.find_all("link"))
    asset_count  = img_count + script_count + link_count

    ms = int(load_time_ms)
    if ms < 2000:
        verdict = "fast"
    elif ms < 4000:
        verdict = "moderate"
    else:
        verdict = "slow"

    return {
        "load_ms":    ms,
        "verdict":    verdict,
        "asset_count": asset_count,
    }
