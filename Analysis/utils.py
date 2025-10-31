# app/analytics/utils.py
from decimal import Decimal, InvalidOperation
from dateutil import parser as dateparser

def parse_money(value: str) -> Decimal:
    """
    Turns '1,234.56', '$1,234.56', '  1234 ', '' into Decimal safely.
    Returns Decimal('0') for junk.
    """
    if value is None:
        return Decimal("0")
    s = str(value).strip()
    if not s:
        return Decimal("0")
    # remove currency symbols and commas
    for ch in ["$", "₹", "€", "£", ","]:
        s = s.replace(ch, "")
    s = s.replace("CR", "").replace("Dr", "").strip()
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal("0")

def parse_date(value: str):
    """
    Parses many string date shapes to a date (not datetime). Returns None if unknown.
    """
    if not value:
        return None
    try:
        dt = dateparser.parse(str(value), dayfirst=False, yearfirst=False, fuzzy=True)
        return dt.date() if dt else None
    except Exception:
        return None
