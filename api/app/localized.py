"""Text in every interface language; the web shows the reader's (web/src/i18n)."""

from decimal import Decimal

LOCALES = ("en", "ro")

type LocalizedText = dict[str, str]


def same_in_all(text: str) -> LocalizedText:
    """Text that reads the same in every language, such as a quote or a name."""
    return dict.fromkeys(LOCALES, text)


def format_amount(value: Decimal, locale: str) -> str:
    """1234.5 as "1,234.50" in English and "1.234,50" in Romanian."""
    english = f"{value:,.2f}"
    if locale == "en":
        return english
    return english.replace(",", " ").replace(".", ",").replace(" ", ".")
