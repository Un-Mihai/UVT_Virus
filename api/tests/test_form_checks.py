"""The form checks read ticked boxes and dates in code, so they need no model."""

from app.verification.agents.form_checks import _days, form_findings
from app.verification.context import DocumentView, PageView

# Lines from a synthetic test dossier (BANCA TEST S.A., "date fictive").
HEADER = (
    "CERERE DE CREDIT - PERSOANE FIZICE\n"
    "Nr. CR-20261028-325771 din data de 28.10.2026 · Unitatea: Sucursala București Unirii\n"
)
APPLICATION = (
    HEADER + "Stare civilă Persoane în întreținere\n"
    "☒ necăsătorit(ă) ☒ căsătorit(ă) 0\n"
    "☐ divorțat(ă) ☐ văduv(ă)\n"
)
KYC = (
    "☒ în nume propriu ☐ în numele altei persoane ☒ subsemnatul(a) ☐ altă persoană\n"
    "Exercit o funcție publică importantă ☐ DA ☒ NU\n"
    "Accept să primesc comunicări de marketing de la bancă ☐ DA ☒ NU\n"
)
ANAF_REFUSED = "☐ DA ☒ NU sunt de acord ca BANCA TEST S.A. să consulte și să prelucreze datele"
CRC_PARTIAL = (
    "ACORD DE CONSULTARE A BAZEI DE DATE\n"
    "3. X a) SITUAȚIA RISCULUI GLOBAL și\n"
    "X b) SITUAȚIA CREDITELOR RESTANTE și\n"
    "X c) SITUAȚIA CREANȚELOR DE RECUPERAT și\n"
    "d) SITUAȚIA CREANȚELOR DE RECUPERAT RESTANTE\n"
)


def document(name: str, *pages: str) -> DocumentView:
    views = [
        PageView(0, number, text, [], False, None, None, None)
        for number, text in enumerate(pages, 1)
    ]
    return DocumentView(1, name, None, views)


def certificate(issued: str) -> DocumentView:
    return document(
        "adeverinta.pdf",
        f"Nr. înregistrare: 1268/{issued}\nData emiterii: {issued}\n"
        "Adeverința este valabilă 90 de zile de la data emiterii.",
    )


def codes(documents: list[DocumentView]) -> list[str]:
    return [draft.rule_code for draft in form_findings(documents)]


def test_two_neighbouring_options_ticked_contradict_each_other() -> None:
    (draft,) = form_findings([document("cerere.pdf", APPLICATION)])
    assert draft.rule_code == "forms.conflicting_marks"
    assert draft.evidence is not None
    assert (draft.evidence.page, draft.evidence.quote) == (1, "☒ necăsătorit(ă) ☒ căsătorit(ă)")
    assert "„necăsătorit(ă)” și „căsătorit(ă)”" in draft.reason["ro"]


def test_independent_questions_on_one_line_are_not_a_contradiction() -> None:
    assert codes([document("kyc.pdf", KYC)]) == []


def test_only_a_refused_consent_is_reported() -> None:
    (draft,) = form_findings([document("acord_anaf.pdf", ANAF_REFUSED)])
    assert draft.rule_code == "forms.consent_refused"
    assert draft.evidence is not None
    assert draft.evidence.quote == "☐ DA ☒ NU sunt de acord"
    assert codes([document("acord_anaf.pdf", ANAF_REFUSED.replace("☐ DA ☒ NU", "☒ DA ☐ NU"))]) == []


def test_a_consent_list_ticked_in_part_names_the_missing_item() -> None:
    (draft,) = form_findings([document("crc.pdf", CRC_PARTIAL)])
    assert draft.rule_code == "forms.consent_incomplete"
    assert draft.evidence is not None
    assert draft.evidence.quote == "d) SITUAȚIA CREANȚELOR DE RECUPERAT RESTANTE"
    assert codes([document("crc.pdf", CRC_PARTIAL.replace("\nd)", "\nX d)"))]) == []
    # A list nobody ticked (the data categories of a consent text) is not a partial consent.
    assert codes([document("anaf.pdf", "ACORD DE CONSULTARE\na) date de identificare")]) == []


def test_a_certificate_older_than_its_own_validity_is_expired() -> None:
    application = document("cerere.pdf", HEADER)
    (draft,) = form_findings([application, certificate("10.07.2026")])
    assert draft.rule_code == "forms.certificate_expired"
    assert "cu 110 zile înaintea cererii din 28.10.2026" in draft.reason["ro"]
    assert "valabilă 90 de zile" in draft.reason["ro"]
    assert codes([application, certificate("20.10.2026")]) == []
    assert codes([certificate("10.07.2026")]) == []  # no application date, nothing to compare


def test_day_counts_follow_romanian_grammar() -> None:
    assert [_days(n)["ro"] for n in (1, 5, 19, 20, 21, 90, 110, 111, 120)] == [
        "1 zi",
        "5 zile",
        "19 zile",
        "20 de zile",
        "21 de zile",
        "90 de zile",
        "110 zile",
        "111 zile",
        "120 de zile",
    ]


ID_ROW = "Eliberat de Data eliberării Valabil până la\nSPCLEP Pașcani 17.05.2016 28.07.2026\n"
KYC_ID_ROW = (
    "Act de identitate Eliberat de / la Valabil până la\n"
    "Carte de identitate MX 480833 SPCLEP Pașcani / 17.05.2016 28.07.2026\n"
)


def declared(total: str) -> DocumentView:
    return document(
        "cerere.pdf",
        f"Total rate lunare existente declarate Garanții acordate pentru alte persoane\n{total} nu\n",
    )


def statement(*days: str) -> DocumentView:
    return document(
        "extras.pdf",
        "".join(
            f"{day} {day} Plată rată credit nevoi personale 1 423.00\n"
            "Beneficiar: BCR | Contract nr. 8689044\n"
            for day in days
        ),
    )


def test_an_identity_card_that_expired_before_the_application_is_reported_once() -> None:
    application = document("cerere.pdf", HEADER + ID_ROW)
    (draft,) = form_findings([application, document("kyc.pdf", KYC_ID_ROW)])
    assert draft.rule_code == "forms.id_expired"
    assert draft.evidence is not None
    assert draft.evidence.quote == "SPCLEP Pașcani 17.05.2016 28.07.2026"
    assert draft.evidence.locate == "28.07.2026"
    assert "a expirat la 28.07.2026, înaintea cererii din 28.10.2026" in draft.reason["ro"]
    assert codes([document("cerere.pdf", HEADER + ID_ROW.replace("2026\n", "2030\n"))]) == []
    assert codes([document("cerere.pdf", ID_ROW)]) == []  # no application date to compare with


def test_instalments_paid_every_month_but_declared_as_none_are_reported() -> None:
    (draft,) = form_findings([declared("0,00 lei"), statement("21.05.2026", "22.06.2026")])
    assert draft.rule_code == "forms.installment_undeclared"
    assert draft.evidence is not None
    assert (
        draft.evidence.quote == "21.05.2026 21.05.2026 Plată rată credit nevoi personale 1 423.00"
    )
    assert "declară rate lunare existente de 0,00 lei" in draft.reason["ro"]
    assert "rate lunare de 1.423,00 lei plătite către BCR" in draft.reason["ro"]
    assert "declares 0.00 RON" in draft.reason["en"]


def test_declared_or_one_off_payments_are_not_reported() -> None:
    months = ("21.05.2026", "22.06.2026")
    assert codes([declared("1.423,00 lei"), statement(*months)]) == []
    assert codes([declared("0,00 lei"), statement("21.05.2026")]) == []  # one payment, no pattern
    assert codes([statement(*months)]) == []  # the application declares nothing to compare with


def income_application(average: str, hired: str = "24.05.2025") -> DocumentView:
    return document(
        "cerere.pdf",
        "Data angajării Vechime la angajatorul actual Vechime totală în muncă\n"
        f"{hired} 15 luni 10 ani\n"
        "Salariu net lunar Venit net mediu - ultimele 6 luni Alte venituri\n"
        f"5.996,00 lei {average} lei nu\n",
    )


def income_certificate(taxable: int, tax: int) -> DocumentView:
    return document(
        "adeverinta.pdf",
        f"1 Declarația 112 (ultima depusă) Venituri salariale venit realizat 53703 {taxable} {tax}\n"
        "nr. INTERNT-399010676-2026 sau asimilate\n"
        "din data de 25.09.2026 salariilor\n",
    )


def test_an_anaf_income_far_below_the_declared_one_is_reported() -> None:
    # (34907 - 3491) / 8 months (January to August) = 3.927 lei a month.
    (draft,) = form_findings([income_application("6.042,00"), income_certificate(34907, 3491)])
    assert draft.rule_code == "forms.income_below_declared"
    assert draft.evidence is not None
    assert draft.evidence.quote.endswith("venit realizat 53703 34907 3491")
    assert "aproximativ 3.927,00 lei pe lună (pe 8 luni)" in draft.reason["ro"]
    assert "mult sub cei 6.042,00 lei" in draft.reason["ro"]


def test_an_anaf_income_close_to_the_declared_one_is_not_reported() -> None:
    assert codes([income_application("5.344,00"), income_certificate(46800, 4680)]) == []  # 5.265
    assert codes([income_certificate(34907, 3491)]) == []  # no declared income to compare with


def test_months_before_the_hiring_month_do_not_count() -> None:
    # Hired on 27.03.2026: April to August is 5 months, 47.080 / 5 = 9.416 lei a month.
    hired = income_application("10.944,00", hired="27.03.2026")
    assert codes([hired, income_certificate(52_000, 4_920)]) == []
    # Counted over 8 months it would be 5.885 and wrongly reported.
    veteran = income_application("10.944,00", hired="27.03.2020")
    assert codes([veteran, income_certificate(52_000, 4_920)]) == ["forms.income_below_declared"]
