"""Every finding sentence the code writes, as (reason, recommendation) in each language.

Placeholders are str.format names. A Decimal value is formatted per language; a LocalizedText
value (a dict) gives each language its own word. tests/test_messages.py checks that every key
has every language with the same placeholders.
"""

from decimal import Decimal

from app.localized import LOCALES, LocalizedText, format_amount

MESSAGES: dict[str, dict[str, tuple[str, str]]] = {
    "cui_invalid": {
        "en": (
            "The CUI {cui} of {party} fails its check digit, so it cannot be right.",
            "Check the CUI against the trade register (ONRC) and correct the document.",
        ),
        "ro": (
            "CUI-ul {cui} pentru {party} nu trece verificarea cifrei de control, deci nu poate"
            " fi corect.",
            "Verificați CUI-ul în registrul comerțului (ONRC) și corectați documentul.",
        ),
    },
    "iban_invalid": {
        "en": (
            "The IBAN {iban} fails its check digits, so payments to it would fail.",
            "Copy the IBAN again from the bank's account statement.",
        ),
        "ro": (
            "IBAN-ul {iban} nu trece verificarea cifrelor de control, deci plățile către el"
            " ar eșua.",
            "Copiați din nou IBAN-ul din extrasul de cont al băncii.",
        ),
    },
    "applicant_cui_mismatch": {
        "en": (
            "{document} gives {party} the CUI {cui}, but the application form says {form_cui}.",
            "Correct the CUI in the document or in the application form so both match.",
        ),
        "ro": (
            "{document} indică pentru {party} CUI-ul {cui}, dar cererea de finanțare indică"
            " {form_cui}.",
            "Corectați CUI-ul în document sau în cerere, astfel încât să coincidă.",
        ),
    },
    "requested_amount_above_total": {
        "en": (
            "The form requests {requested}, more than the total of {total} in {document}.",
            "Lower the requested amount, or correct the total in the budget.",
        ),
        "ro": (
            "Cererea solicită {requested}, mai mult decât totalul de {total} din {document}.",
            "Micșorați suma solicitată sau corectați totalul din buget.",
        ),
    },
    "subtotal_mismatch": {
        "en": (
            "{label} in {document} is {stated}, but the line totals add up to {expected}.",
            "Recompute the subtotal and correct the document, or the lines that are wrong.",
        ),
        "ro": (
            "{label} din {document} este {stated}, dar totalurile pe linii însumează {expected}.",
            "Recalculați subtotalul și corectați documentul sau liniile greșite.",
        ),
    },
    "grand_total_mismatch": {
        "en": (
            "{label} in {document} is {stated}, but the subtotal plus VAT is {expected}.",
            "Recompute the total with the VAT rate valid on the document's date.",
        ),
        "ro": (
            "{label} din {document} este {stated}, dar subtotalul plus TVA este {expected}.",
            "Recalculați totalul cu cota de TVA valabilă la data documentului.",
        ),
    },
    "date_outside_period": {
        "en": (
            "{label} {date} in {document} is outside the project period {start} to {end}.",
            "Check the date, or explain why this document falls outside the period.",
        ),
        "ro": (
            "{label} {date} din {document} este în afara perioadei proiectului, {start} - {end}.",
            "Verificați data sau explicați de ce documentul este în afara perioadei.",
        ),
    },
    "cnp_invalid": {
        "en": (
            "The CNP {masked} in {where} fails its check digit.",
            "Copy the CNP again from the person's identity card.",
        ),
        "ro": (
            "CNP-ul {masked} din {where} nu trece verificarea cifrei de control.",
            "Copiați din nou CNP-ul din actul de identitate al persoanei.",
        ),
    },
    "cnp_differs_from_form": {
        "en": (
            "The CNP {masked} in {where} differs from the legal representative's CNP in the"
            " application form.",
            "Check whether this is the same person; correct the CNP if it is.",
        ),
        "ro": (
            "CNP-ul {masked} din {where} diferă de CNP-ul reprezentantului legal din cerere.",
            "Verificați dacă este aceeași persoană; dacă da, corectați CNP-ul.",
        ),
    },
    "cnp_differs_between_documents": {
        "en": (
            "The CNP {masked} in {where} differs from the CNP the other documents give.",
            "Check whether this is the same person; correct the CNP if it is.",
        ),
        "ro": (
            "CNP-ul {masked} din {where} diferă de CNP-ul din celelalte documente.",
            "Verificați dacă este aceeași persoană; dacă da, corectați CNP-ul.",
        ),
    },
    "document_missing": {
        "en": (
            "No {document_type} was found among the uploaded documents.",
            "Upload the {document_type} the regulation requires.",
        ),
        "ro": (
            "Printre documentele încărcate nu s-a găsit: {document_type}.",
            "Încărcați documentul cerut de regulament: {document_type}.",
        ),
    },
    "page_unreadable": {
        "en": (
            "Page {page} of {document} could not be read, even with OCR, so it was not checked.",
            "Upload a clearer scan or a text PDF of this document, or check this page by hand.",
        ),
        "ro": (
            "Pagina {page} din {document} nu a putut fi citită, nici prin OCR, deci nu a"
            " fost verificată.",
            "Încărcați o scanare mai clară sau un PDF cu text al documentului, ori verificați"
            " pagina manual.",
        ),
    },
}

DOCUMENT_TYPE_NAMES: dict[str, LocalizedText] = {
    "financing_application": {"en": "financing application", "ro": "cererea de finanțare"},
    "contract": {"en": "contract", "ro": "contractul"},
    "offer": {"en": "offer", "ro": "oferta"},
    "invoice": {"en": "invoice", "ro": "factura"},
    "budget": {"en": "budget", "ro": "bugetul"},
    "guarantee": {"en": "guarantee", "ro": "garanția"},
    "certificate": {"en": "certificate", "ro": "certificatul"},
    "statement": {"en": "statement", "ro": "declarația"},
    "other": {"en": "other document", "ro": "alt document"},
}

type Param = str | int | Decimal | LocalizedText


def message(key: str, **params: Param) -> tuple[LocalizedText, LocalizedText]:
    """The reason and the recommendation for `key`, filled in, in every language."""
    entry = MESSAGES[key]

    def value(param: Param, locale: str) -> str:
        if isinstance(param, Decimal):
            return format_amount(param, locale)
        if isinstance(param, dict):
            return param[locale]
        return str(param)

    filled = {
        locale: tuple(
            template.format(**{name: value(param, locale) for name, param in params.items()})
            for template in entry[locale]
        )
        for locale in LOCALES
    }
    return (
        {locale: texts[0] for locale, texts in filled.items()},
        {locale: texts[1] for locale, texts in filled.items()},
    )


def document_type_name(document_type: str) -> LocalizedText:
    return DOCUMENT_TYPE_NAMES.get(document_type, dict.fromkeys(LOCALES, document_type))
