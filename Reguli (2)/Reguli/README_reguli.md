# Reguli pentru verificarea dosarului de credit – persoană fizică

Acest folder conține reglementările **în vigoare** folosite la verificarea dosarului de credit și a documentelor din el.
Surse: **Raiffeisen Bank** (documente publice) și **surse oficiale externe** (BNR, Guvern, Parlament, ANAF, UE). Nu conține documente ale altor bănci.

**Domeniul acoperit:** credit nou de nevoi personale, **în lei**, fără ipotecă, pentru o **persoană fizică salariată** (produsul Flexicredit).
**În afara domeniului**, cu reguli diferite care nu se aplică automat: refinanțările, creditele revolving și cardurile de credit, creditele în valută, creditele imobiliare și ipotecare (OUG 52/2016) și creditele pentru firme.

**Data de referință:** 28.10.2026. Pentru fiecare dosar se aplică forma actului în vigoare **la data dosarului**. Data la care a fost descărcat un text nu dovedește că acel text e actual.

> Acest README este o sinteză și o interpretare. **Nu se indexează în RAG ca act normativ.** Pentru RAG se indexează numai PDF-urile din rădăcina folderului, câte **o singură reprezentare** pentru fiecare sursă. HTML-urile din `_sursa_html` sunt originalele din care s-au făcut PDF-urile și nu sunt a doua confirmare a aceleiași reguli. Folderul `_arhiva_abrogate` nu se indexează pentru dosare actuale.

---

## 1. Ce conține folderul

Coloana „Tip sursă” arată cât de aproape de original este fișierul:
- **Original**: fișierul exact, așa cum a fost descărcat de la emitent.
- **Text oficial → PDF**: textul paginii oficiale salvate, convertit în PDF fără modificări de conținut. Pagina HTML salvată se află în `_sursa_html`.

| Fișier | Regulament | Emitent | Tip sursă | Pe scurt |
|---|---|---|---|---|
| `BNR_Regulament_17_2012_conditii_creditare.pdf` | **Regulamentul BNR nr. 17/2012** privind unele condiții de creditare | Banca Națională a României | Text oficial → PDF (legislatie.just.ro, forma consolidată) | Gradul de îndatorare, venitul eligibil, durata maximă, LTV |
| `OUG_50_2010_contracte_credit_consumatori.pdf` | **OUG nr. 50/2010** privind contractele de credit pentru consumatori | Guvernul României | Text oficial → PDF (legislatie.just.ro) | Informarea precontractuală, evaluarea bonității, conținutul contractului |
| `BNR_Regulament_4_2025_Centrala_Riscului_de_Credit.pdf` | **Regulamentul BNR nr. 4/2025** privind organizarea și funcționarea la BNR a Centralei Riscului de Credit (M.Of. nr. 913/03.10.2025), **în vigoare de la 01.12.2025** | Banca Națională a României | Text oficial → PDF ([legislatie.just.ro/…/302766](https://legislatie.just.ro/Public/DetaliiDocument/302766)); include numai anexa nr. 5 | Consultarea CRC de către bancă și acordul persoanei (art. 23) |
| `BNR_Regulament_4_2025_Anexa5_F5_Acord_CRC_original_bnr.ro.pdf` | Anexa nr. 5 la Reg. BNR 4/2025: formularul **F5 „Acord de consultare a bazei de date a CRC”** și modul de completare | Banca Națională a României | **Original** (bnr.ro) | Modelul acordului CRC, cu rubricile lui |
| `Legea_129_2019_spalarea_banilor_KYC.pdf` | **Legea nr. 129/2019** pentru prevenirea și combaterea spălării banilor și finanțării terorismului | Parlamentul României | Text oficial → PDF (legislatie.just.ro) | Cunoașterea clientului (KYC), identificarea, persoanele expuse public (PEP) |
| `BNR_Regulament_2_2019_spalarea_banilor_banci.pdf` | **Regulamentul BNR nr. 2/2019** privind prevenirea și combaterea spălării banilor și finanțării terorismului | Banca Națională a României | Text oficial → PDF (legislatie.just.ro) | Cum aplică băncile Legea 129/2019 |
| `OUG_97_2005_acte_de_identitate.pdf` | **OUG nr. 97/2005** privind evidența, domiciliul, reședința și actele de identitate (republicată) | Guvernul României | Text oficial → PDF (legislatie.just.ro) | Tipurile de act de identitate, valabilitatea lor, CNP |
| `Ordin_ANAF_3396_2016_adeverinta_de_venit.pdf` | **Ordinul ANAF nr. 3396/2016** pentru aprobarea modelului „Adeverință de venit” | ANAF | Text oficial → PDF (originalul e la [static.anaf.ro](https://static.anaf.ro/static/10/Anaf/legislatie/OPANAF_3396_2016.pdf)) | Modelul adeverinței de venit emise de ANAF și valabilitatea ei |
| `GDPR_Regulamentul_UE_2016_679.pdf` | **Regulamentul (UE) 2016/679** (GDPR) | Parlamentul European și Consiliul | **Original** ([EUR-Lex](https://eur-lex.europa.eu/legal-content/RO/TXT/PDF/?uri=CELEX:32016R0679)) | Prelucrarea datelor personale, temeiurile legale, drepturile clientului |
| `CGB_Raiffeisen_PF_2026.pdf` | **Condițiile Generale de Derulare a Operațiunilor Bancare – Persoane Fizice**, ediția 26.02.2026 | Raiffeisen Bank | **Original** ([raiffeisen.ro](https://www.raiffeisen.ro/persoane-fizice/in-sprijinul-tau/informatii-utile/documente/)) | Relația contractuală bancă–client; se aplică și contractelor de credit |
| `Nota_informare_credite_Raiffeisen.pdf` | **Notă de informare privind prelucrarea datelor cu caracter personal în contextul furnizării serviciilor bancare aferente produselor de credit** | Raiffeisen Bank | Text oficial → PDF ([raiffeisen.ro/ro/aplica/nota-de-informare-credit.html](https://www.raiffeisen.ro/ro/aplica/nota-de-informare-credit.html), salvată pe 28.10.2026) | Ce date prelucrează banca pentru credite și în ce temei; Biroul de Credit (interes legitim) |
| `Flexicredit_Raiffeisen_conditii.pdf` | **Pagina produsului Flexicredit**, întreagă: campanie, eligibilitate, documente, informații generale, costuri | Raiffeisen Bank | Text oficial → PDF ([bank.raiffeisen.ro/ro/flexicredit/home.html](https://bank.raiffeisen.ro/ro/flexicredit/home.html), salvată pe 28.10.2026) | **Politică publică de produs**, nu lege. Pagina se contrazice în câteva puncte, detaliate în secțiunea 3.2 |

---

## 2. Ce regulament se folosește pentru fiecare document

### Categoria 1 – Formulare ale băncii

| Document | Regulamente | Ce se verifică pe baza lor |
|---|---|---|
| **Cerere de credit** | Reg. BNR 17/2012 · OUG 50/2010 · CGB Raiffeisen · pagina Flexicredit | Datele solicitantului și ale creditului; durata cerută față de art. 17 și condițiile produsului; încadrarea în gradul de îndatorare (vezi 3.1); evaluarea bonității pe bază de informații suficiente |
| **Formular Biroul de Credit** | CGB Raiffeisen pct. 2.1.4.3 · Nota de informare credite (pct. 2.2, 4.2, 4.3) · GDPR art. 6 alin. (1) lit. f) și art. 13–14 · OUG 50/2010 | La Raiffeisen, Biroul de Credit se consultă în **interesul legitim** al băncii (banca și Biroul de Credit sunt operatori asociați), **nu pe bază de consimțământ**. Documentul din dosar dovedește **informarea** clientului. Se verifică: nume și CNP identice cu CI, semnătura, data ≤ data interogării. **Biroul de Credit nu e CRC.** |
| **Acord interogare CRC (BNR)** | **Reg. BNR 4/2025 art. 23** și anexa nr. 5 (formularul F5) · GDPR | Consultarea CRC se face **numai cu acordul persoanei**. Acordul poate fi dat prin semnătură olografă, semnătură electronică simplă sau calificată, ori prin identificare la distanță. Formularul F5 are: nr. și data emiterii, persoana (cod de identificare), persoana declarantă (denumire, cod), informațiile pentru care se dă acordul, perioada de valabilitate, semnătura emitentului, semnătura autorizată a reprezentantului băncii. Acordurile semnate **înainte de 01.12.2025** se verifică după Reg. 2/2012, din `_arhiva_abrogate` |
| **Acord consultare date ANAF** | GDPR · Nota de informare credite (pct. 4.4, 5.1) · pagina Flexicredit | Acordul pentru verificarea veniturilor la ANAF. E singurul document cerut pentru Flexicredit în afară de actul de identitate |
| **GDPR + FATCA/CRS + declarație PEP** | GDPR · Nota de informare credite · Legea 129/2019 · Reg. BNR 2/2019 · FATCA/CRS (vezi secțiunea 5) | Informarea GDPR și opțiunea de marketing; statutul PEP și măsurile suplimentare de cunoaștere a clientului; completitudinea declarației de rezidență fiscală |

### Categoria 2 – Identitate

| Document | Regulamente | Ce se verifică pe baza lor |
|---|---|---|
| **Carte de identitate** | OUG 97/2005 art. 16 · Legea 129/2019 (art. 11, art. 15) · Reg. BNR 2/2019 | Tipul actului (CI clasică / CEI / CIS); valabilitatea **la data dosarului**, după regula tipului respectiv; datele de stare civilă; CNP corect. **Data emiterii și tipul actului nu dovedesc singure că actul e fals** |

### Categoria 3 – Venit

| Document | Regulamente | Ce se verifică pe baza lor |
|---|---|---|
| **Adeverință de venit (ANAF)**, modelul folosit în datele de test | Ordinul ANAF 3396/2016 · Reg. BNR 17/2012 (art. 15) | Mai întâi se confirmă că documentul este modelul din Ordinul 3396/2016. Numai pentru acest model, adeverința e valabilă **90 de zile** de la emitere. Se verifică perioada de venit, data emiterii și venitul folosit la analiză (vezi 3.3 despre D112) |
| **Adeverință de venit (angajator)** | Reg. BNR 17/2012 (art. 14, art. 15) · normele interne ale băncii | Venitul eligibil. **Termenul de 90 de zile nu se aplică.** Nu există model legal unic, iar valabilitatea o stabilește banca (normă internă: *necesită confirmare*) |
| **Extras de cont** | CGB Raiffeisen · Reg. BNR 17/2012 (art. 14) | Încasările salariale confirmă venitul. Plățile de rate indică unele datorii, dar **nu pe toate**: datoriile complete vin din CRC și Biroul de Credit. Transferurile între conturi proprii, creditele primite și tranzacțiile anulate nu sunt venit recurent (pagina Flexicredit le exclude explicit din venitul minim recurent) |

### Decizia de credit (pe tot dosarul)

| Verificare | Regulament |
|---|---|
| Durata maximă a creditului de consum | Reg. BNR 17/2012 – art. 17 |
| Eligibilitate produs (vârstă, venit minim, vechime, sumă, durată) | Pagina Flexicredit (politică de produs) |
| Gradul total de îndatorare | Reg. BNR 17/2012 – art. 13, 14, 19 |
| Venitul eligibil și creșterea venitului | Reg. BNR 17/2012 – art. 15 alin. (1) și (4) |
| Excepții de la plafonul de îndatorare | Reg. BNR 17/2012 – art. 20 (excepție la nivelul portofoliului băncii, nu al dosarului) |
| Evaluarea bonității înainte de contract | OUG 50/2010 |
| Cunoașterea clientului (KYC, PEP) | Legea 129/2019 · Reg. BNR 2/2019 |
| Protecția datelor din dosar | GDPR · Nota de informare credite |

Aplicația **verifică documentele**, dar **nu aprobă creditul**. Dacă toate verificările ies conforme, asta nu înseamnă că creditul se acordă.

---

## 3. Regulile concrete utile pentru aplicație

Sunt extrase din textele din acest folder, în forma consolidată la 28.10.2026. Calculele de date, vârstă, durată și procente se fac **determinist în cod**. RAG doar găsește sursa și explică regula. Rezultatele posibile ale unei verificări: **conform**, **problemă**, **date insuficiente**, **nu se aplică** sau **necesită analiză umană**.

### 3.1 Reguli legale

| Regulă | Valoare | Sursa |
|---|---|---|
| Durata maximă a creditului de consum | **5 ani (60 de luni)**. Excepții: (2) creditele de consum cu destinație imobiliară, în lei, cu avans de minimum 40%; (3) prelungirea facilităților **revolving prin carduri** peste 5 ani, cu reevaluarea capacității de rambursare la fiecare 5 ani. Pentru un credit nou de nevoi personale nu se aplică niciuna dintre excepții | Reg. BNR 17/2012, art. 17 alin. (1)–(3) |
| Gradul total de îndatorare | Obligațiile lunare totale din credite și alte finanțări rambursabile, raportate la venitul net lunar. Pentru ratele inegale se ia cea mai mare rată | Reg. BNR 17/2012, art. 13 alin. (1) și (1^1) |
| Plafonul gradului de îndatorare | **40%** la acordarea creditului (45% doar la primul credit imobiliar pentru locuință). Pentru creditele în valută acordate unei persoane neacoperite la riscul valutar se adaugă un plafon separat de 20% pentru obligațiile în valută. Plafonul se calculează doar cu toate obligațiile cunoscute. **Dacă lipsesc date (CRC, Biroul de Credit), rezultatul este „date insuficiente” sau un calcul provizoriu, nu un verdict** | Reg. BNR 17/2012, art. 19 alin. (1)–(3) |
| Gradul de îndatorare pe durata creditului | Trebuie să rămână probabil în limita maximă pe toată durata creditului | Reg. BNR 17/2012, art. 14 alin. (1) |
| Excepția de la plafon (art. 20) | **Nu e o toleranță de 15 puncte procentuale pentru fiecare client.** Banca poate acorda peste plafon credite de consum în valoare de cel mult **15% din media volumelor trimestriale** ale creditelor de consum acordate în ultimele 4 trimestre. Condiții suplimentare: credit ≤ 250.000 EUR; venit de cel puțin salariul mediu net pe economie; categoria de debitori justificată din date istorice; nivelurile maxime stabilite în normele proprii. **Disponibilitatea excepției nu se poate stabili din dosar.** Dacă se depășesc 40%, aplicația semnalează „peste plafonul standard, necesită analiza unei eventuale excepții” și nu acordă excepția automat | Reg. BNR 17/2012, art. 20 alin. (1)–(7) |
| Venitul eligibil | Ca regulă, nu poate depăși cu mai mult de **20%** venitul anului anterior. **Excepție:** banca poate lua în calcul un venit mai mare dacă are documente justificative care dovedesc **modificarea** (de exemplu promovare sau schimbarea locului de muncă) și **continuitatea** venitului. Dacă venitul a crescut peste 20%, rezultatul este „se cer documente justificative / analiză umană”, nu respingere automată. Se compară venituri pentru **perioade echivalente** (lunar cu lunar, anual cu anual) și pe aceeași bază (net cu net) | Reg. BNR 17/2012, art. 15 alin. (1), (3) și (4) |
| Adeverința de venit ANAF (modelul OPANAF 3396/2016) | valabilă **90 de zile** de la data emiterii, **numai pentru acest model** | Ordinul ANAF 3396/2016, anexa 1 (textul formularului) |
| Valabilitatea **cărții de identitate clasice** (CI) | 4 ani între 14 și 18 ani · 7 ani între 18 și 25 de ani · 10 ani după 25 de ani · nelimitată după 55 de ani | OUG 97/2005, art. 16 alin. (1) |
| CI clasică emisă după eliberarea primei cărți electronice (2021) | valabilă cel mult până la **03.08.2031** | OUG 97/2005, art. 16 alin. (1^1) |
| Valabilitatea **cărții electronice de identitate (CEI)** și a **cărții de identitate simple (CIS)** | 5 ani între 14 și 18 ani · **10 ani după 18 ani** · nelimitată după 70 de ani; CEI cu valabilitate de 1 an când amprentele nu pot fi prelevate | OUG 97/2005, art. 16 alin. (2) și (2^2) |
| CI clasică emisă după 01.08.2025 | **Nu se marchează automat ca suspectă.** Legea permite în continuare emiterea CI clasice cu valabilitate până la 03.08.2031 (art. 16 alin. (1^1)), iar, potrivit precizărilor DGEP/MAI, există situații speciale în care se emite (comunicatul nu a putut fi consultat la revizie). Se verifică doar tipul actului, data expirării și datele din el | OUG 97/2005, art. 16 alin. (1^1); precizările DGEP/MAI (nu sunt în folder) |
| Identificarea clientului persoană fizică | toate datele de stare civilă din actul de identitate, verificate din surse sigure și independente | Legea 129/2019, art. 11 și art. 15 |
| Persoane expuse public | măsuri suplimentare de cunoaștere a clientului | Legea 129/2019, art. 17 |
| Acordul pentru consultarea CRC | Este obligatoriu. Se poate da prin semnătură olografă, semnătură electronică sau identificare la distanță. Formularul este F5 | Reg. BNR 4/2025, art. 23 și anexa nr. 5 |

### 3.2 Condiții de produs Flexicredit (politică publică a băncii, nu lege)

Pagina oficială, salvată pe 28.10.2026, conține **informații contradictorii**. Regulile marcate „necesită confirmarea băncii” nu se folosesc ca motiv sigur de respingere.

| Condiție | Ce scrie pe pagină | Statut |
|---|---|---|
| Vârsta | Secțiunea „Criterii minime de eligibilitate”: **21 – 63 de ani femei / 65 de ani bărbați** la terminarea creditului. Secțiunea „Informații utile”, pe aceeași pagină: **21 – 65 de ani** la terminarea creditului, fără diferență între femei și bărbați | **necesită confirmarea băncii** (femeile între 63 și 65 de ani la final = analiză umană) |
| Venitul minim | „cel puțin egal cu venitul minim net pe economie”. Pagina nu dă o sumă | provizoriu. Pragul în lei îl confirmă mentorul. **Nu se calculează un net aproximativ din salariul minim brut** |
| Vechimea la angajatorul actual | minimum **3 luni** | confirmat (pagina e consecventă) |
| Contractul de muncă | nedeterminat; determinat care acoperă durata creditului; sau determinat care nu o acoperă, dar cu cel puțin 2 reînnoiri succesive | confirmat |
| Suma | „Informații generale”: **500 – 30.000 EUR** (echivalent în lei). Banner-ul campaniei „Yellow Friday” **15.10 – 26.11.2026**: „sume de până la **50.000 euro**” | **necesită confirmarea băncii**. Peste 30.000 EUR, în perioada campaniei = analiză umană, nu neeligibil automat |
| Durata | 18 luni – 5 ani | confirmat (și Reg. BNR 17/2012, art. 17) |
| Moneda | lei | confirmat |
| Documente cerute | actul de identitate + acordul de consultare a veniturilor ANAF; banca poate cere documente de venit | confirmat |
| Fără credite executate sau rambursate cu întârzieri mari și repetate | criteriu de eligibilitate | confirmat. Se verifică din CRC sau Biroul de Credit, nu din dosar |

---

## 4. Reguli corectate sau eliminate la revizia din 28.10.2026

| Ce scria înainte | Ce s-a schimbat | Motiv |
|---|---|---|
| Acordul CRC după Reg. BNR 2/2012, formularul F5 din anexa nr. 5 | Înlocuit cu **Reg. BNR 4/2025 art. 23 + anexa nr. 5**. Reg. 2/2012 a fost mutat în `_arhiva_abrogate` | Reg. 4/2025 art. 44 alin. (2) abrogă Reg. 2/2012 de la 01.12.2025 |
| „Venitul eligibil nu poate depăși cu mai mult de 20% venitul anului anterior”, prezentat ca limită absolută | S-a adăugat excepția din art. 15 alin. (4) | Venitul mai mare se acceptă dacă există documente justificative |
| „Excepție de la plafonul de îndatorare: maximum 15%” | Explicat ca plafon de portofoliu al băncii, cu condițiile lui | Art. 20 nu se aplică individual pe dosar |
| Durata de 5 ani: „excepție doar pentru creditele imobiliare” | S-a adăugat excepția pentru revolving prin carduri (alin. (3)) | Textul art. 17 |
| „CI clasică emisă după 01.08.2025 e suspectă” | **Eliminat** | Legea permite emiterea până la 03.08.2031, iar precizările DGEP/MAI menționează situații speciale |
| „Lunile declarate în D112 nu pot depăși ultima lună pentru care D112 era scadentă” | **Eliminat** | Scadența (25 a lunii următoare) e un termen-limită, iar D112 se poate depune mai devreme. Nicio regulă D112 nu se folosește până nu se identifică articolul din Codul de procedură fiscală, în forma actuală |
| „Venit minim: aprox. 2.699 lei net (salariul minim brut 4.325 lei)” | **Eliminat** | Sursa era presa, nu un text oficial. Calculul brut → net depinde de situația fiscală a persoanei |
| „Vârsta: 21 – 63 F / 65 B”, „Suma: 500 – 30.000 EUR” ca reguli sigure | Marcate „necesită confirmarea băncii” | Pagina oficială se contrazice (vezi 3.2) |
| Termenul de 90 de zile aplicat oricărei adeverințe de venit | Limitat la modelul din OPANAF 3396/2016 | Termenul apare doar în textul acelui formular |
| `Flexicredit_Raiffeisen_conditii.pdf`: extras redactat, cu o notă proprie | Refăcut din textul întreg al paginii oficiale salvate | Un extras redactat nu e sursă oficială |

---

## 5. Ce nu se află în folder și de ce

| Lipsește | Motiv |
|---|---|
| **Normele interne de creditare Raiffeisen** (metodologia gradului de îndatorare, tratarea bonusurilor, valabilitatea adeverinței de la angajator, scoring) | Nu sunt publice. Reg. BNR 17/2012 art. 12 cere fiecărei bănci propriile reglementări. Se cer mentorului (secțiunea 7). Orice valoare simulată se marchează explicit ca **simulată** |
| Proiectul BNR din 2026 de modificare a Reg. 17/2012 | Este doar proiect, nu e în vigoare |
| Cererea de credit Raiffeisen | Nu e publicată online. Acordul CRC (F5) este în folder. **Acordul de consultare ANAF** publicat de Raiffeisen: [PDF](https://www.raiffeisen.ro/content/dam/rbi/retail/eu/ro/documents/pf/20150514-Acord-Consultare-Agentia-Nationala-Administrare-Fiscala.pdf.coredownload.inline.pdf). Nu e inclus în folder și se descarcă manual |
| Regulile Biroului de Credit | Sunt contractuale între bănci și Biroul de Credit. Temeiul și datele transmise sunt în `Nota_informare_credite_Raiffeisen.pdf` |
| Codul de procedură fiscală (D112) | Nu e descărcat. De aceea **nu există nicio regulă activă despre D112** |
| Precizările DGEP/MAI despre cărțile de identitate | [mai.gov.ro](https://www.mai.gov.ro/precizari-ale-directiei-generale-pentru-evidenta-persoanelor-dgep-cu-privire-la-informatiile-eronate-aparute-in-spatiul-public-referitoare-la-documentele-de-identitate-aflate-in-prezent-in-circulati/). Nu e descărcat |
| FATCA / CRS | FATCA: Legea nr. 233/2015 (Acordul România–SUA); CRS: Codul de procedură fiscală. Textele nu sunt în folder. Aplicația verifică doar că declarația e **completă și semnată**. Regulile despre TIN/NIF nu se presupun pentru toți solicitanții |
| Semnătura electronică (Legea 214/2024, eIDAS) | Nu e în folder. Un document semnat electronic valid **nu se respinge** pentru că nu are semnătură olografă. O imagine a semnăturii nu înseamnă verificare criptografică |
| Credite imobiliare (OUG 52/2016), credite pentru firme | În afara domeniului. Au nevoie de cataloage separate |

## 6. De verificat înainte de prezentare

- **OUG 50/2010** rămâne aplicabilă cererilor din datele de test (23–28.10.2026). Regulile noi care transpun Directiva (UE) 2023/2225 se aplică de la **20.11.2026**. Pentru dosarele de după această dată trebuie verificate actul român de transpunere și dispozițiile tranzitorii. Directiva singură nu înlocuiește legea națională.
- Formele consolidate de pe legislatie.just.ro **nu au valoare oficială**; textul oficial e cel publicat în Monitorul Oficial. Pentru o aplicație de test sunt suficiente.
- Pagina Flexicredit se schimbă cu campaniile. Valorile din 3.2 sunt cele afișate pe 28.10.2026.

## 7. Întrebări pentru mentorul Raiffeisen

1. Ce produs, canal (agenție / Smart Mobile) și ofertă (standard sau campania Yellow Friday) se reprezintă în demo?
2. Care e limita de vârstă corectă la final: 63 F / 65 B sau 65 pentru toți? Plafonul de sumă e 30.000 EUR sau 50.000 EUR în campanie?
3. Care e lista documentelor obligatorii pentru dosarul din demo și ce termen de valabilitate are fiecare (în special adeverința de la angajator și extrasul de cont)?
4. Ce venituri sunt eligibile și cum se tratează bonusurile, contractele pe perioadă determinată și alte venituri?
5. Cu ce metodologie se calculează obligațiile existente (carduri de credit, overdraft, garanții)?
6. Ce formulare și mecanisme de semnare se acceptă pentru informări și acorduri (olograf, electronic, identificare la distanță)?
7. Care e pragul în lei pentru „venitul minim net pe economie”?
8. Cum circulă excepțiile (de exemplu peste plafonul de 40%) și ce date se pot simula în hackathon?
