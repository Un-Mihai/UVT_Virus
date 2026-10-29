"""Romanian identifiers, amounts, dates and diacritics.

Copied from the document-verification skill (references/romanian-data.md), with its tests in
tests/test_romanian.py. Standard library only.
"""

import re
import unicodedata
from datetime import date
from decimal import Decimal

CUI_KEY = "753217532"
CNP_KEY = "279146358279"


def is_valid_cui(value: str) -> bool:
    """Romanian CUI/CIF by the ANAF formula: 2-10 digits, the last one is the check digit.

    The value is taken as written on the page, so a label ("CUI", "C.I.F.", "cod fiscal") and the
    "RO" prefix are dropped first. The other digits, padded to nine on the left, are multiplied by
    753217532 and summed; the sum times 10 modulo 11 is the check digit, 10 counting as 0.
    """
    text = re.sub(r"[\s.:/-]", "", value.upper())
    digits = re.sub(r"^(?:CUI|CIF|CODFISCAL|CF)?(?:RO)?", "", text)
    if not re.fullmatch(r"\d{2,10}", digits):
        return False
    body, check = digits[:-1].zfill(9), int(digits[-1])
    total = sum(int(d) * int(k) for d, k in zip(body, CUI_KEY, strict=True))
    return (total * 10 % 11) % 10 == check


def is_valid_iban(value: str) -> bool:
    """ISO 13616 mod-97 check; Romanian IBANs are 24 characters (RO + 2 check digits + 20)."""
    iban = value.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", iban):
        return False
    if iban.startswith("RO") and len(iban) != 24:
        return False
    rearranged = iban[4:] + iban[:4]
    return int("".join(str(int(c, 36)) for c in rearranged)) % 97 == 1


def is_valid_cnp(value: str) -> bool:
    """Romanian personal numeric code (personal data: mask it before sending text to a model)."""
    if not re.fullmatch(r"[1-9]\d{12}", value):
        return False
    total = sum(int(d) * int(k) for d, k in zip(value[:12], CNP_KEY, strict=True))
    check = total % 11
    return (1 if check == 10 else check) == int(value[12])


def parse_ro_amount(text: str) -> Decimal | None:
    """'1.234.567,89 lei' -> Decimal('1234567.89'); None when the format is ambiguous."""
    s = re.sub(r"[^\d.,-]", "", text)
    if re.fullmatch(r"-?\d{1,3}[.,]\d{3}", s):
        return None  # "1.234" or "1,234": thousands or decimals? Ask, don't guess.
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?|-?\d+(,\d+)?", s):  # 1.234.567,89
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):  # 1,234,567.89
        s = s.replace(",", "")
    elif not re.fullmatch(r"-?\d+\.\d+", s):
        return None
    return Decimal(s)


RO_MONTHS = {
    "ianuarie": 1,
    "februarie": 2,
    "martie": 3,
    "aprilie": 4,
    "mai": 5,
    "iunie": 6,
    "iulie": 7,
    "august": 8,
    "septembrie": 9,
    "octombrie": 10,
    "noiembrie": 11,
    "decembrie": 12,
}


def parse_ro_date(text: str) -> date | None:
    """'28.10.2026', '28/10/2026' or '28 octombrie 2026' -> date(2026, 10, 28)."""
    text = normalize_ro(text).lower().strip()
    if m := re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", text):
        day, month, year = map(int, m.groups())
    elif m := re.fullmatch(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", text):
        if m.group(2) not in RO_MONTHS:
            return None
        day, month, year = int(m.group(1)), RO_MONTHS[m.group(2)], int(m.group(3))
    else:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


CEDILLA_TO_COMMA = str.maketrans("şţŞŢ", "șțȘȚ")


def normalize_ro(text: str) -> str:
    """Legacy cedilla ş/ţ -> correct comma-below ș/ț, NFC, soft hyphens removed."""
    return unicodedata.normalize("NFC", text).translate(CEDILLA_TO_COMMA).replace("­", "")


def quote_key(text: str) -> str:
    """Comparison key for checking that a model's quote appears in the page text."""
    text = normalize_ro(text).casefold()
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # words hyphenated across lines
    return re.sub(r"\s+", " ", text).strip()


def quote_in_page(quote: str, page_text: str) -> bool:
    return bool(quote.strip()) and quote_key(quote) in quote_key(page_text)
