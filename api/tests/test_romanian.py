from datetime import date
from decimal import Decimal

from app.romanian import (
    CNP_KEY,
    is_valid_cnp,
    is_valid_cui,
    is_valid_iban,
    normalize_ro,
    parse_ro_amount,
    parse_ro_date,
    quote_in_page,
)


def make_cnp(prefix12: str) -> str:
    """A synthetic CNP with a valid check digit (never a real person's)."""
    total = sum(int(d) * int(k) for d, k in zip(prefix12, CNP_KEY, strict=True)) % 11
    return prefix12 + str(1 if total == 10 else total)


def test_validators_match_the_skill_reference() -> None:
    assert is_valid_cui("361820")  # Raiffeisen Bank S.A.
    assert is_valid_cui("RO 361579")  # BRD - Groupe Société Générale
    assert not is_valid_cui("361821")
    assert not is_valid_cui("RO12A")
    assert is_valid_iban("RO49 AAAA 1B31 0075 9384 0000")  # IBAN registry example
    assert not is_valid_iban("RO49AAAA1B31007593840001")
    assert not is_valid_iban("RO49AAAA1B3100759384000")  # 23 chars

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
    assert quote_in_page(
        "garanția de bună execuție", "Valoarea garan-\nția de bună  execuție este 10%"
    )
    assert not quote_in_page("garanția de participare", "Valoarea garanției de bună execuție")
