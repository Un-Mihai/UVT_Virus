import re
from decimal import Decimal

from app.localized import LOCALES, format_amount
from app.verification.messages import MESSAGES, document_type_name, message


def placeholders(template: str) -> set[str]:
    return set(re.findall(r"\{(\w+)\}", template))


def test_every_message_has_every_language_with_the_same_placeholders() -> None:
    for key, by_locale in MESSAGES.items():
        assert set(by_locale) == set(LOCALES), key
        english = [placeholders(template) for template in by_locale["en"]]
        for locale in LOCALES:
            assert [placeholders(t) for t in by_locale[locale]] == english, (key, locale)


def test_amounts_follow_each_language() -> None:
    assert format_amount(Decimal("1234567.5"), "en") == "1,234,567.50"
    assert format_amount(Decimal("1234567.5"), "ro") == "1.234.567,50"


def test_message_fills_every_language() -> None:
    reason, recommendation = message(
        "document_missing", document_type=document_type_name("guarantee")
    )

    assert reason == {
        "en": "No guarantee was found among the uploaded documents.",
        "ro": "Printre documentele încărcate nu s-a găsit: garanția.",
    }
    assert set(recommendation) == set(LOCALES)
