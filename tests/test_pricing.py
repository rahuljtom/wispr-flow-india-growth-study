import pytest

from src.transform.pricing import parse_price


@pytest.mark.parametrize("text,amount,cur,period,annual", [
    ("Rs 320 per month, billed annually", 320, "INR", "month", True),
    ("₹320/mo billed annually", 320, "INR", "month", True),
    ("INR 3,840 per year", 3840, "INR", "year", True),
    ("$12 / month billed annually", 12, "USD", "month", True),
    ("$15 per month", 15, "USD", "month", False),
    ("US$144/yr", 144, "USD", "year", True),
    ("Rs. 10 per month", 10, "INR", "month", False),
    ("$8.49 / mo", 8.49, "USD", "month", False),
])
def test_parse_price(text, amount, cur, period, annual):
    r = parse_price(text)
    assert (r["amount"], r["currency"], r["period"], r["billed_annually"]) == (amount, cur, period, annual)


@pytest.mark.parametrize("text", ["Free", "Contact sales", "", "no price here 2026"])
def test_parse_price_none(text):
    assert parse_price(text) is None
