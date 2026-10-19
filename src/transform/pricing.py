"""Price string parser (currency, amount, period, billing)."""
import re

PRICE = re.compile(
    r"(?P<cur>US\$|\$|₹|Rs\.?|INR)\s*(?P<amt>\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)
PERIOD = re.compile(r"(?:per|/|a)\s*(?P<p>month|mo|year|yr|annum)\b", re.IGNORECASE)
CUR = {"us$": "USD", "$": "USD", "₹": "INR", "rs": "INR", "rs.": "INR", "inr": "INR"}


def parse_price(text):
    m = PRICE.search(text or "")
    if not m:
        return None
    amount = float(m.group("amt").replace(",", ""))
    amount = int(amount) if amount.is_integer() else amount
    p = PERIOD.search(text[m.end():])
    period = None
    if p:
        period = "month" if p.group("p").lower() in ("month", "mo") else "year"
    billed_annually = bool(re.search(r"annual|yearly|per year|/\s*(?:year|yr)", text, re.IGNORECASE))
    return {"amount": amount, "currency": CUR[m.group("cur").lower()], "period": period,
            "billed_annually": billed_annually}
