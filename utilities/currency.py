import re


def parse_currency(text: str) -> float:
    """Extract a dollar amount from label text like "$19.80" or "Total $19.80"
    into a float. Mirrors the same approach used in khub-web-tests for
    reading payment totals — never hardcode expected amounts, always parse
    the live value."""
    match = re.search(r"[\d,]+\.?\d*", text)
    if not match:
        raise ValueError(f"No numeric amount found in {text!r}")
    return float(match.group().replace(",", ""))
