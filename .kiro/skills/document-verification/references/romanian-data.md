# Romanian identifiers, amounts, dates and diacritics

Tested helpers (Python 3.12+, standard library only). Copy them into `api/app/` with their tests
when the product needs them.

- **CUI/CIF:** optional `RO` prefix, 2–10 digits, the last is a check digit (key `753217532`,
  sum × 10 mod 11, 10 becomes 0).
- **IBAN:** ISO 13616 mod-97; Romanian IBANs are 24 characters: `RO`, 2 check digits, a 4-letter
  bank code, 16 account characters.
- **CNP:** personal data. Validate locally, mask before sending text to a model.
- **Amounts:** Romanian documents write `1.234.567,89`; English ones `1,234,567.89`. A lone
  `1.234` is ambiguous, so the parser refuses to guess.
- **Diacritics:** older documents use cedilla `ş ţ` (U+015F, U+0163) instead of comma-below `ș ț`
  (U+0219, U+021B). Normalise both sides before comparing or searching.
- **CPV codes** (procurement vocabulary) look like `45000000-7`; check them against the official
  CPV list rather than computing the check digit.

```python
import re
import unicodedata
from datetime import date
from decimal import Decimal

CUI_KEY = "753217532"
CNP_KEY = "279146358279"


def is_valid_cui(value: str) -> bool:
    """Romanian CUI/CIF: optional RO prefix, 2-10 digits, last digit is the check digit."""
    digits = re.sub(r"^RO", "", value.strip().upper().replace(" ", ""))
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
    "ianuarie": 1, "februarie": 2, "martie": 3, "aprilie": 4, "mai": 5, "iunie": 6,
    "iulie": 7, "august": 8, "septembrie": 9, "octombrie": 10, "noiembrie": 11, "decembrie": 12,
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
```

## Tests

```python
# --- tests -----------------------------------------------------------------
assert is_valid_cui("361820")          # Raiffeisen Bank S.A.
assert is_valid_cui("RO 361579")       # BRD - Groupe Société Générale
assert not is_valid_cui("361821")
assert not is_valid_cui("RO12A")
assert is_valid_iban("RO49 AAAA 1B31 0075 9384 0000")  # IBAN registry example
assert not is_valid_iban("RO49AAAA1B31007593840001")
assert not is_valid_iban("RO49AAAA1B3100759384000")    # 23 chars

def make_cnp(prefix12: str) -> str:
    total = sum(int(d) * int(k) for d, k in zip(prefix12, CNP_KEY, strict=True)) % 11
    return prefix12 + str(1 if total == 10 else total)

synthetic = make_cnp("190010112345")
assert is_valid_cnp(synthetic), synthetic
assert not is_valid_cnp(synthetic[:-1] + str((int(synthetic[-1]) + 1) % 10))

assert parse_ro_amount("1.234.567,89 lei") == Decimal("1234567.89")
assert parse_ro_amount("1 234 567,89") == Decimal("1234567.89")
assert parse_ro_amount("1,234,567.89") == Decimal("1234567.89")
assert parse_ro_amount("19,5") == Decimal("19.5")
assert parse_ro_amount("1500") == Decimal("1500")
assert parse_ro_amount("1.234") is None
assert parse_ro_amount("1.234 lei") is None
assert parse_ro_amount("1,234") is None
assert parse_ro_amount("1.234.567") == Decimal("1234567")
assert parse_ro_amount("n/a") is None
assert parse_ro_amount("12.50") == Decimal("12.50")

assert parse_ro_date("28.10.2026") == date(2026, 10, 28)
assert parse_ro_date("28 octombrie 2026") == date(2026, 10, 28)
assert parse_ro_date("31.02.2026") is None

assert normalize_ro("Garanţie de bună execuţie") == "Garanție de bună execuție"
assert quote_in_page("garanția de bună execuție", "Valoarea garan-\nția de bună  execuție este 10%")
assert not quote_in_page("garanția de participare", "Valoarea garanției de bună execuție")
print("all validator tests passed; synthetic CNP:", synthetic)
```
