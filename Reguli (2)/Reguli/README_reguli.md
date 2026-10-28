# Reguli pentru verificarea dosarului de credit – persoană fizică

Acest folder conține surse legislative și documente publice folosite la verificarea dosarului de credit. **Nu reprezintă o certificare că toate textele sunt actualizate la data de referință.** Versiunea și aplicabilitatea se verifică pentru data fiecărui dosar; incertitudinile rămân marcate explicit.
Surse: **Raiffeisen Bank** (documente publice) și **surse oficiale externe** (BNR, Guvern, Parlament, ANAF, UE). Nu conține documente ale altor bănci.

**Domeniul acoperit:** credit nou de nevoi personale, **în lei**, fără ipotecă, pentru o **persoană fizică salariată** (produsul Flexicredit).
**În afara domeniului**, cu reguli diferite care nu se aplică automat: refinanțările, creditele revolving și cardurile de credit, creditele în valută, creditele imobiliare și ipotecare (OUG 52/2016) și creditele pentru firme.

**Data de referință:** 28.10.2026. Pentru fiecare dosar se aplică forma actului în vigoare **la data dosarului**. Data la care a fost descărcat un text nu dovedește că acel text e actual.

> Acest README este o sinteză și o interpretare. **Nu se indexează în RAG ca act normativ.** Pentru RAG se indexează numai PDF-urile din rădăcina folderului, câte **o singură reprezentare** pentru fiecare sursă. HTML-urile din `_sursa_html` sunt originalele din care s-au făcut PDF-urile și nu sunt a doua confirmare a aceleiași reguli. Folderul `_arhiva_abrogate` nu se indexează pentru dosare actuale. Folderul `_text_integral_neindexat` păstrează textele integrale din care s-au făcut extrase și nici el nu se indexează.

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
| `OPANAF_146_2022_protocol_inclusiv_Anexa1_acord_ANAF.pdf` | **Ordinul ANAF nr. 146/2022** (condițiile de furnizare a informațiilor și modelul-cadru al protocolului ANAF–PJDP, art. 70^1 alin. (1) lit. b) din Codul de procedură fiscală); **anexa 1 la protocol = „Acord pentru solicitarea veniturilor persoanelor fizice și/sau juridice”** | ANAF | **Original** (PDF publicat de ANAF, 23 de pagini) | Modelul oficial în vigoare al acordului ANAF: consultare pe maximum **5 zile lucrătoare** de la semnare sau acceptare expresă; dreptul de retragere a acordului în acest interval; trimiteri la GDPR |
| `Adeverinta_salariu_vechime_Raiffeisen.pdf` | Adeverință de salariu și vechime în muncă (fișier public 20220810) | Raiffeisen Bank | **Original**, descărcat la 28.10.2026 | Câmpuri de venit, contract, rețineri și semnatari; nu impune singur criterii de respingere |
| `Legea_214_2024_semnatura_electronica.pdf` | Legea nr. 214/2024 | Parlamentul României | Text oficial → PDF; HTML în `_sursa_html`; consultat la 28.10.2026 | Art. 3-4: efecte juridice, tipuri de semnături și verificarea la momentul semnării |
| `Codul_fiscal_Legea_227_2015_extras_art_147.pdf` | **Codul fiscal – Legea nr. 227/2015**, forma consolidată (modificări incluse până la 25.10.2026): **extras cu art. 147** | Parlamentul României | Text oficial → PDF. Extrasul conține paginile 1 și 101–102 din PDF-ul integral, neschimbate (pagina 101 începe cu finalul art. 146, pagina 102 se termină cu începutul art. 148). PDF-ul integral (258 de pagini, salvat din browser de pe legislatie.just.ro pe 28.10.2026) e în `_text_integral_neindexat` | Termenul declarației D112: **art. 147 alin. (1)** |

---

## 2. Ce regulament se folosește pentru fiecare document

### Categoria 1 – Formulare ale băncii

| Document | Regulamente | Ce se verifică pe baza lor |
|---|---|---|
| **Cerere de credit** | Reg. BNR 17/2012 · OUG 50/2010 · CGB Raiffeisen · pagina Flexicredit | Datele solicitantului și ale creditului; durata cerută față de art. 17 și condițiile produsului; încadrarea în gradul de îndatorare (vezi 3.1); evaluarea bonității pe bază de informații suficiente |
| **Formular Biroul de Credit** | CGB Raiffeisen pct. 2.1.4.3 · Nota de informare credite (pct. 2.2, 4.2, 4.3) · GDPR art. 6 alin. (1) lit. f) și art. 13–14 · OUG 50/2010 | La Raiffeisen, Biroul de Credit se consultă în **interesul legitim** al băncii (banca și Biroul de Credit sunt operatori asociați), **nu pe bază de consimțământ**. Documentul din dosar dovedește **informarea** clientului. Se verifică: nume și CNP identice cu CI, semnătura, data ≤ data interogării. **Biroul de Credit nu e CRC.** |
| **Acord interogare CRC (BNR)** | **Reg. BNR 4/2025 art. 23** și anexa nr. 5 (formularul F5) · GDPR | Consultarea CRC se face **cu acordul persoanei** (art. 23 alin. (1)). **Excepție (alin. (2)):** acordul nu e necesar dacă persoana e un debitor raportat de aceeași bancă în ultima perioadă de raportare încheiată, sau pentru informațiile despre fraude cu carduri. Acordul poate fi dat prin semnătură olografă, semnătură electronică simplă sau calificată, ori prin identificare la distanță. Formularul F5 are: nr. și data emiterii; persoana (cod de identificare); persoana declarantă (denumire, cod); informațiile pentru care se dă acordul: **a) situația riscului global, b) situația creditelor restante, c) situația creanțelor de recuperat, d) situația creanțelor de recuperat restante**; perioada de valabilitate; semnătura emitentului; **semnătura autorizată** a reprezentantului băncii, care trebuie să fie **olografă sau electronică calificată**. Dacă acordul s-a obținut prin identificare la distanță, banca trebuie să-l poată proba față de CRC (anexa 5, pct. (i)–(ii)). Acordurile semnate **înainte de 01.12.2025** se verifică după Reg. 2/2012, din `_arhiva_abrogate` |
| **Acord consultare date ANAF** | **OPANAF 146/2022, anexa 1 la protocol** · GDPR · Nota de informare credite (pct. 4.4, 5.1) · pagina Flexicredit | Mai întâi se confirmă că documentul urmează modelul din anexa 1 (titlul „Acord pentru solicitarea veniturilor persoanelor fizice și/sau juridice”, secțiunile A și B). Se verifică: numele, domiciliul și CNP-ul (identice cu CI), calitatea de client, denumirea băncii destinatare, numărul de înregistrare, data și semnătura. Consultarea ANAF e autorizată pe maximum **5 zile lucrătoare de la data semnării sau a acceptării exprese**; dacă se cunoaște data interogării, se verifică încadrarea în acest interval, iar fără ea rezultatul e „date insuficiente”. Clientul își poate retrage acordul în interiorul celor 5 zile. Formularul Raiffeisen din 2015 nu se folosește pentru dosarele actuale. Pagina Flexicredit indică actul de identitate și acordul ANAF, dar permite documente suplimentare |
| **GDPR + FATCA/CRS + declarație PEP** | GDPR · Nota de informare credite · Legea 129/2019 (art. 3 – definiția PEP, art. 11, 15, 17) · Reg. BNR 2/2019 (art. 8 – datele minime despre client) · FATCA/CRS (vezi secțiunea 5) | Datele de identificare cerute de Reg. BNR 2/2019 art. 8 (nume, data și locul nașterii, CNP, adresa și regimul ei juridic, cetățenia, ocupația și angajatorul, telefon/e-mail dacă există, scopul și natura relației, sursa fondurilor, încadrarea PEP, beneficiarul real dacă e altă persoană), identice cu CI și cererea; declarația PEP completată (calitatea de PEP se păstrează cel puțin 12 luni după încetarea funcției, art. 3); informarea GDPR și opțiunea de marketing; completitudinea declarației de rezidență fiscală |

### Categoria 2 – Identitate

| Document | Regulamente | Ce se verifică pe baza lor |
|---|---|---|
| **Carte de identitate** | OUG 97/2005 art. 16 · Legea 129/2019 (art. 11, art. 15) · Reg. BNR 2/2019 | Tipul actului (CI clasică / CEI / CIS); valabilitatea **la data dosarului**, după regula tipului respectiv; datele de stare civilă; CNP-ul identic în toate documentele. **Data emiterii și tipul actului nu dovedesc singure că actul e fals.** Validarea structurii CNP (data nașterii, sex, cifra de control) e un **control tehnic**: OUG 97/2005 art. 6 doar instituie CNP-ul, iar algoritmul nu e în niciun text din folder |

### Categoria 3 – Venit

| Document | Regulamente | Ce se verifică pe baza lor |
|---|---|---|
| **Adeverință de venit (ANAF)**, modelul oficial | Ordinul ANAF 3396/2016 · Reg. BNR 17/2012 (art. 15) · Codul fiscal art. 147 alin. (1) | Mai întâi se confirmă că documentul este modelul din Ordinul 3396/2016. Numai pentru acest model, adeverința e valabilă **90 de zile** de la emitere. Se verifică perioada de venit, data emiterii și venitul folosit la analiză (D112: vezi rândul din 3.1) |
| **Adeverință de venit (angajator)** | Reg. BNR 17/2012 (art. 14, art. 15) · normele interne ale băncii | Venitul eligibil. **Termenul de 90 de zile nu se aplică.** Nu există model legal unic. Este inclus modelul public Raiffeisen `Adeverinta_salariu_vechime_Raiffeisen.pdf`; verificările lui sunt în 3.4. Valabilitatea acceptată o confirmă banca; nu se inventează un termen |
| **Extras de cont** | CGB Raiffeisen · Reg. BNR 17/2012 (art. 14) | Încasările salariale confirmă venitul. Plățile de rate indică unele datorii, dar **nu pe toate**: CRC și Biroul de Credit sunt surse de informații despre datorii, dar **nu garantează inventarierea tuturor obligațiilor**. Se reconciliază rapoartele disponibile cu declarațiile clientului, contractele și celelalte dovezi; lipsa unei raportări nu dovedește lipsa datoriei. Transferurile între conturi proprii, creditele primite și tranzacțiile anulate nu se tratează automat ca salariu. **Aceasta e o regulă a echipei (control operațional), nu o regulă a băncii:** pagina Flexicredit le exclude doar din „venitul minim recurent de 2.000 lei” pentru discountul de dobândă, nu din venitul eligibil |

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

Sunt extrase din versiunile textelor incluse în acest folder. Data de referință a sintezei este 28.10.2026; aceasta nu echivalează cu verificarea integrală a istoricului fiecărui act până la acea dată. Calculele de date, vârstă, durată și procente se fac **determinist în cod**. RAG doar găsește sursa și explică regula. Rezultatele posibile ale unei verificări: **conform**, **problemă**, **date insuficiente**, **nu se aplică** sau **necesită analiză umană**.

### 3.1 Reguli legale

| Regulă | Valoare | Sursa |
|---|---|---|
| Durata maximă a creditului de consum | **5 ani (60 de luni)**. Excepții: (2) creditele de consum cu destinație imobiliară, în lei, cu avans de minimum 40%; (3) prelungirea facilităților **revolving prin carduri** peste 5 ani, cu reevaluarea capacității de rambursare la fiecare 5 ani. Pentru un credit nou de nevoi personale nu se aplică niciuna dintre excepții | Reg. BNR 17/2012, art. 17 alin. (1)–(3) |
| Gradul total de îndatorare | Obligațiile lunare totale din credite și alte finanțări rambursabile, raportate la venitul net lunar. Pentru ratele inegale se ia cea mai mare rată. **Cardurile de credit și overdraftul pe care clientul le are deja intră în calcul**: pentru o facilitate revolving, obligația lunară luată în calcul **nu poate fi mai mică de 3% din plafon** (procentul exact îl stabilește banca) | Reg. BNR 17/2012, art. 13 alin. (1), (1^1) și (2) |
| Plafonul gradului de îndatorare | **40%** la acordarea creditului (45% doar la primul credit imobiliar pentru locuință). Pentru creditele în valută acordate unei persoane neacoperite la riscul valutar se adaugă un plafon separat de 20% pentru obligațiile în valută. Plafonul se calculează doar cu toate obligațiile cunoscute. **Dacă lipsesc date (CRC, Biroul de Credit), rezultatul este „date insuficiente” sau un calcul provizoriu, nu un verdict** | Reg. BNR 17/2012, art. 19 alin. (1)–(3) |
| Gradul de îndatorare pe durata creditului | Trebuie să rămână probabil în limita maximă pe toată durata creditului | Reg. BNR 17/2012, art. 14 alin. (1) |
| Excepția de la plafon (art. 20) | **Nu e o toleranță de 15 puncte procentuale pentru fiecare client.** Banca poate acorda peste plafon credite de consum în valoare de cel mult **15% din media volumelor trimestriale** ale creditelor de consum acordate în ultimele 4 trimestre. Condiții suplimentare: credit ≤ 250.000 EUR; venit de cel puțin salariul mediu net pe economie; categoria de debitori justificată din date istorice; nivelurile maxime stabilite în normele proprii. **Disponibilitatea excepției nu se poate stabili din dosar.** Dacă se depășesc 40%, aplicația semnalează „peste plafonul standard, necesită analiza unei eventuale excepții” și nu acordă excepția automat | Reg. BNR 17/2012, art. 20 alin. (1)–(7) |
| Venitul eligibil | Ca regulă, nu poate depăși cu mai mult de **20%** venitul anului anterior. **Excepție:** banca poate lua în calcul un venit mai mare dacă are documente justificative care dovedesc **modificarea** (de exemplu promovare sau schimbarea locului de muncă) și **continuitatea** venitului. Dacă venitul a crescut peste 20%, rezultatul este „se cer documente justificative / analiză umană”, nu respingere automată. Se compară venituri pentru **perioade echivalente** (lunar cu lunar, anual cu anual) și pe aceeași bază (net cu net) | Reg. BNR 17/2012, art. 15 alin. (1), (3) și (4) |
| Adeverința de venit ANAF (modelul OPANAF 3396/2016) | valabilă **90 de zile** de la data emiterii, **numai pentru acest model** | Ordinul ANAF 3396/2016, anexa 1 (textul formularului) |
| Declarația D112 (rubrica „data ultimei declarații” din adeverința ANAF) | Angajatorul depune D112 lunar, **până la data de 25 inclusiv a lunii următoare** celei pentru care se plătesc veniturile. Termenul e o limită maximă: D112 se poate depune și mai devreme. Controale permise: data ultimei D112 ≤ data emiterii adeverinței (altfel: **problemă**); perioada de venit nu poate fi după data emiterii. Lipsa D112 pentru o lună deja scadentă nu dovedește un fals (poate fi depunere întârziată): **necesită analiză umană** | Codul fiscal (Legea 227/2015), art. 147 alin. (1) |
| Valabilitatea **cărții de identitate clasice** (CI) | 4 ani între 14 și 18 ani · 7 ani între 18 și 25 de ani · 10 ani după 25 de ani · nelimitată după 55 de ani | OUG 97/2005, art. 16 alin. (1) |
| CI clasică emisă după eliberarea primei cărți electronice (2021) | valabilă cel mult până la **03.08.2031** | OUG 97/2005, art. 16 alin. (1^1) |
| Valabilitatea **cărții electronice de identitate (CEI)** și a **cărții de identitate simple (CIS)** | 5 ani între 14 și 18 ani · **10 ani după 18 ani** · nelimitată după 70 de ani; CEI cu valabilitate de 1 an când amprentele nu pot fi prelevate. **Termenul se calculează de la data emiterii** (nu de la ziua de naștere). Regimul se aplică de la **20.03.2025** pentru CEI de la 14 ani în sus (alin. (2) lit. c)–e)), de la **02.06.2025** pentru CEI sub 14 ani (lit. a)–b)) și de la **20.05.2025** pentru CIS. MAI extinde emiterea CEI **eșalonat** (alin. (2) din HG), deci un act emis după aceste date nu trebuie să fie obligatoriu CEI | OUG 97/2005, art. 16 alin. (2), (2^2) și (6); HG nr. 231/2025, art. unic alin. (1) lit. a)–c) și alin. (2) (redată ca notă în textul OUG) |
| CI clasică emisă după 01.08.2025 | **Nu se marchează automat ca suspectă.** Legea permite în continuare emiterea CI clasice cu valabilitate până la 03.08.2031 (art. 16 alin. (1^1)), iar, potrivit precizărilor DGEP/MAI, există situații speciale în care se emite (comunicatul nu a putut fi consultat la revizie). Se verifică doar tipul actului, data expirării și datele din el | OUG 97/2005, art. 16 alin. (1^1); precizările DGEP/MAI (nu sunt în folder) |
| Identificarea clientului persoană fizică | toate datele de stare civilă din actul de identitate, verificate din surse sigure și independente | Legea 129/2019, art. 11 și art. 15 |
| Persoane expuse public | măsuri suplimentare de cunoaștere a clientului | Legea 129/2019, art. 17 |
| Acordul pentru consultarea CRC | Necesar, **cu excepția** debitorilor raportați de aceeași bancă în ultima perioadă de raportare și a informațiilor despre fraude cu carduri. Se poate da prin semnătură olografă, semnătură electronică sau identificare la distanță. Formularul este F5 | Reg. BNR 4/2025, art. 23 și anexa nr. 5 |

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
| Fără credite executate sau rambursate cu întârzieri mari și repetate | criteriu de eligibilitate | confirmat. Se verifică din rapoartele disponibile CRC/Biroul de Credit și din celelalte dovezi relevante; absența raportării nu dovedește absența incidentelor |

### 3.3 Completitudinea informațiilor despre datorii

CRC și Biroul de Credit au domenii, praguri, participanți și perioade de raportare proprii. Nu se presupune că împreună acoperă orice obligație. Acesta este un **control operațional de completitudine**, nu o afirmație că fiecare solicitant trebuie obligatoriu interogat în ambele baze. Se respectă temeiul și condițiile fiecărei consultări. Datele se reconciliază cu declarațiile clientului și dovezile disponibile; pentru date lipsă sau contradictorii: **date insuficiente / analiză umană**, nu zero datorii. Aceeași obligație nu se numără de două ori când apare în surse diferite.


### Notă – versiunea formularului ANAF

modelul în vigoare folosit în dosare este anexa 1 din OPANAF 146/2022. PDF-ul Raiffeisen din 2015 (în `_arhiva_abrogate`) citează Legea 677/2001; aceste trimiteri istorice nu reactivează legea abrogată și nu înlocuiesc GDPR. Fereastra de 5 zile lucrătoare e aceeași în ambele modele.

### 3.4 Adeverința publică Raiffeisen de salariu și vechime

Sursa: `Adeverinta_salariu_vechime_Raiffeisen.pdf`. Se verifică numai câmpurile aplicabile: identitatea angajatului și angajatorului, CNP/CUI, numărul și data documentului, data angajării și vechimea, durata și expirarea contractului, informațiile despre contractele succesive, veniturile nete din ultimele trei luni și componentele variabile, venitul brut din anul anterior și lunile lucrate, creșterea venitului și motivul acesteia, rețineri/cesiuni/popriri, numele, funcția și semnătura reprezentantului autorizat conform formularului. Câmpurile condiționale nu se cer dacă situația nu se aplică.

**Nu se compară direct brutul anual cu netul lunar.** O rubrică DA despre suspendare, preaviz, restructurare sau poprire cere analiză în context; formularul nu stabilește singur respingerea. Din acest model nu se deduce un termen universal de valabilitate și nici obligativitatea lui pentru orice dosar. Lipsa unei rubrici ori a unei dovezi se clasifică după aplicabilitate și stadiu; nu dovedește automat falsul.

### 3.5 Informarea precontractuală și contractul

Sursa: `OUG_50_2010_contracte_credit_consumatori.pdf`, art. 11, art. 46 și anexa nr. 2. Verificările depind de **stadiul dosarului**: absența contractului într-o simplă cerere nu este încălcare automată.

| Verificare | Regula și rezultat |
|---|---|
| Informații standard la nivel european | Înainte de încheiere/acceptarea ofertei, se verifică furnizarea formularului din anexa nr. 2, pe hârtie sau alt suport durabil, și dovezile de transmitere/primire disponibile; art. 11. Simplul fișier gol nu dovedește informarea. |
| Intervalul înainte de contract/ofertă | Art. 11 alin. (2) lit. a): minimum **15 zile**; alin. (3) permite reducerea cu **acordul scris al consumatorului**. Un interval mai scurt se verifică împreună cu acordul; nu se respinge automat. Fără date suficiente: date insuficiente. |
| Forma informațiilor | Art. 11 alin. (2) lit. b): scris vizibil, ușor de citit, Times New Roman minimum 12 p, suport durabil; contrast la hârtie. OCR-ul singur nu certifică fontul și lizibilitatea. |
| Conținut contractual | Art. 46: tipul creditului, părți, durată, valoare și tragere, dobândă și condiții/formulă de modificare, DAE și ipoteze, total plătibil, suma/numărul/frecvența plăților, costuri, întârzieri, garanții/asigurări dacă se aplică, drepturi și proceduri de retragere/rambursare anticipată, încetare, căi extrajudiciare și autoritate de supraveghere. Lista este un rezumat: se verifică toate literele aplicabile din articol. |
| Concordanță ofertă-contract | Se confruntă suma, durata, dobânda, DAE, totalul plătibil și costurile cu oferta aplicabilă și graficul. Diferențele trebuie explicate; o ofertă modificată nu dovedește singură ilegalitate. Control operațional bazat pe documentele disponibile. |

### 3.6 Semnături electronice

Sursa inclusă: `Legea_214_2024_semnatura_electronica.pdf`, art. 1 alin. (4), art. 3 și art. 4. Referințe eIDAS: `SURSE_eIDAS.md` (linkuri, nu text integral inclus).

- Se disting semnătura simplă, avansată și calificată. Legea 214/2024 art. 3 permite efecte juridice și probatorii pentru toate tipurile, dar echivalența cu semnătura olografă depinde de tip și de condițiile art. 4. Nu se presupune că orice semnătură simplă sau avansată este automat echivalentă.
- Conform art. 3 alin. (3), valabilitatea se evaluează **la momentul semnării**; expirarea ulterioară a certificatului nu invalidează singură documentul. Se păstrează rezultatul validării și dovezile disponibile despre integritate, certificat, revocare și timp. Acestea sunt controale tehnice de probă, nu dovada că orice document are obligatoriu marcă temporală.
- Nu se respinge un document electronic valid doar pentru absența semnăturii olografe. O imagine a unei semnături sau un text OCR nu certifică validarea criptografică. Fără fișierul electronic ori dovezi suficiente: **date insuficiente / analiză umană**.
- Cerința exactă pentru formular și canal se verifică separat. Pentru CRC/F5 se păstrează cerințele specifice din Reg. BNR 4/2025; nu sunt relaxate automat de această sinteză.

---

## 4. Reguli corectate sau eliminate la revizia din 28.10.2026

| Ce scria înainte | Ce s-a schimbat | Motiv |
|---|---|---|
| Acordul CRC după Reg. BNR 2/2012, formularul F5 din anexa nr. 5 | Înlocuit cu **Reg. BNR 4/2025 art. 23 + anexa nr. 5**. Reg. 2/2012 a fost mutat în `_arhiva_abrogate` | Reg. 4/2025 art. 44 alin. (2) abrogă Reg. 2/2012 de la 01.12.2025 |
| „Venitul eligibil nu poate depăși cu mai mult de 20% venitul anului anterior”, prezentat ca limită absolută | S-a adăugat excepția din art. 15 alin. (4) | Venitul mai mare se acceptă dacă există documente justificative |
| „Excepție de la plafonul de îndatorare: maximum 15%” | Explicat ca plafon de portofoliu al băncii, cu condițiile lui | Art. 20 nu se aplică individual pe dosar |
| Durata de 5 ani: „excepție doar pentru creditele imobiliare” | S-a adăugat excepția pentru revolving prin carduri (alin. (3)) | Textul art. 17 |
| „CI clasică emisă după 01.08.2025 e suspectă” | **Eliminat** | Legea permite emiterea până la 03.08.2031, iar precizările DGEP/MAI menționează situații speciale |
| „Lunile declarate în D112 nu pot depăși ultima lună pentru care D112 era scadentă” | **Eliminat** | Scadența (25 a lunii următoare) e un termen-limită, iar D112 se poate depune mai devreme. Termenul D112 e în **Codul fiscal (Legea 227/2015), art. 147 alin. (1)**. Regula corectă e acum în 3.1 |
| „Venit minim: aprox. 2.699 lei net (salariul minim brut 4.325 lei)” | **Eliminat** | Sursa era presa, nu un text oficial. Calculul brut → net depinde de situația fiscală a persoanei |
| „Vârsta: 21 – 63 F / 65 B”, „Suma: 500 – 30.000 EUR” ca reguli sigure | Marcate „necesită confirmarea băncii” | Pagina oficială se contrazice (vezi 3.2) |
| Termenul de 90 de zile aplicat oricărei adeverințe de venit | Limitat la modelul din OPANAF 3396/2016 | Termenul apare doar în textul acelui formular |
| `Flexicredit_Raiffeisen_conditii.pdf`: extras redactat, cu o notă proprie | Refăcut din textul întreg al paginii oficiale salvate | Un extras redactat nu e sursă oficială |
| Acordul CRC „obligatoriu” fără excepții; F5 descris fără zonele noi | Adăugate excepția din art. 23 alin. (2), punctele c)–d) din zona 3, cerința pentru semnătura autorizată și proba acordului la distanță | Reg. BNR 4/2025, art. 23 și anexa nr. 5 |
| CEI/CIS: lipsea data de la care se calculează valabilitatea | Adăugate art. 16 alin. (6) (valabilitatea se calculează de la data emiterii) și HG 231/2025 (20.03.2025 CEI / 20.05.2025 CIS) | Textul OUG 97/2005 din folder |
| Gradul de îndatorare fără regula pentru carduri și overdraft | Adăugat minimul de 3% din plafon pentru facilitățile revolving existente | Reg. BNR 17/2012, art. 13 alin. (2) |
| Termenul D112 atribuit Codului de procedură fiscală | Corectat: Codul fiscal (Legea 227/2015), art. 147 alin. (1) | Încadrare greșită a sursei |
| Nicio regulă activă despre D112 | Adăugată regula D112 din art. 147 alin. (1), doar cu controalele care rezultă din text | Codul fiscal a fost adăugat în folder (forma consolidată la 25.10.2026) |
| Excluderile Flexicredit (transferuri proprii etc.) prezentate ca regulă a băncii pentru venit | Marcate drept regulă a echipei | Pe pagină se aplică doar venitului de 2.000 lei pentru discountul de dobândă |
| Antetul `BNR_Regulament_4_2025_Centrala_Riscului_de_Credit.pdf` trimitea la un fișier inexistent | Corectat numele fișierului F5 | Nume greșit în nota de început (textul regulamentului nu s-a schimbat) |
| Acordul ANAF verificat după formularul Raiffeisen din 2015 (Legea 677/2001) | Sursa devine **OPANAF 146/2022, anexa 1**; formularul din 2015 e mutat în `_arhiva_abrogate` | OPANAF 146/2022 e modelul oficial în vigoare; formularul din 2015 citează o lege abrogată |

---

## 5. Ce nu se află în folder și de ce

| Lipsește | Motiv |
|---|---|
| **Normele interne de creditare Raiffeisen** (metodologia gradului de îndatorare, tratarea bonusurilor, valabilitatea adeverinței de la angajator, scoring) | Nu sunt publice. Reg. BNR 17/2012 art. 12 cere fiecărei bănci propriile reglementări. Se cer mentorului (secțiunea 7). Orice valoare simulată se marchează explicit ca **simulată** |
| Proiectul BNR din 2026 de modificare a Reg. 17/2012 | Este doar proiect, nu e în vigoare |
| Cererea de credit Raiffeisen | Nu e publicată online. Modelele publice ale celorlalte formulare sunt în folder: acordul CRC (F5, anexa 5 la Reg. BNR 4/2025) și acordul ANAF (anexa 1 din OPANAF 146/2022). Formularul ANAF Raiffeisen din 2015 e păstrat doar ca istoric, în `_arhiva_abrogate` |
| Regulile Biroului de Credit | Sunt contractuale între bănci și Biroul de Credit. Temeiul și datele transmise sunt în `Nota_informare_credite_Raiffeisen.pdf` |
| Precizările DGEP/MAI despre cărțile de identitate | [mai.gov.ro](https://www.mai.gov.ro/precizari-ale-directiei-generale-pentru-evidenta-persoanelor-dgep-cu-privire-la-informatiile-eronate-aparute-in-spatiul-public-referitoare-la-documentele-de-identitate-aflate-in-prezent-in-circulati/). Nu e descărcat |
| FATCA / CRS | FATCA: Legea nr. 233/2015 (Acordul România–SUA); CRS: Codul de procedură fiscală. Textele nu sunt în folder. Aplicația verifică doar că declarația e **completă și semnată**. Regulile despre TIN/NIF nu se presupun pentru toți solicitanții |
| eIDAS - textul integral | Legea 214/2024 este inclusă ca PDF și HTML. Sursa eIDAS și verificările sunt în 3.6 și `SURSE_eIDAS.md`. Textul integral eIDAS nu a putut fi descărcat (accesul EUR-Lex a returnat răspuns gol); nu este pretins ca inclus. |
| Credite imobiliare (OUG 52/2016), credite pentru firme | În afara domeniului. Au nevoie de cataloage separate |
| Confirmarea modelului ANAF folosit efectiv de Raiffeisen | Modelul-cadru e în OPANAF 146/2022, anexa 1. Dacă Raiffeisen folosește o variantă proprie a acestui model pe un anumit canal (agenție / Smart Mobile) se confirmă cu banca. Convenția de calcul a celor 5 zile lucrătoare în cazuri-limită necesită confirmare |
| Verificarea angajatorului (firmă activă, fără insolvență) | Temeiuri posibile: Legea 265/2022 (registrul comerțului), Legea 85/2014 (insolvență). Nu sunt în folder. Până atunci e un **control operațional** al echipei, nu o obligație legală citată |
| Legea 190/2018 (măsuri de punere în aplicare a GDPR) | Art. 4 reglementează prelucrarea CNP-ului și a copiilor după actul de identitate. Opțională: contează pentru conformitatea aplicației, nu pentru verificarea documentelor din dosar |
| AI Act – Regulamentul (UE) 2024/1689 | Evaluarea bonității persoanelor fizice prin AI e sistem cu **risc ridicat** (anexa III pct. 5 lit. b). Data de la care se aplică obligațiile (posibil amânată prin modificări din 2026) **nu a fost verificată**. Între timp se aplică GDPR art. 22 (decizii automatizate). Aplicația **verifică documente** și nu ia decizia de credit; această distincție trebuie păstrată |

## 6. De verificat înainte de prezentare

- **OUG 50/2010** rămâne aplicabilă cererilor depuse înainte de **20.11.2026**. Forma din folder conține modificări până la **OUG nr. 15/2024**. La consultarea din 28.10.2026 a [paginii actului](https://legislatie.just.ro/public/DetaliiDocument/119472), istoricul afișa ultima consolidare la **17.03.2024**. Această constatare privește istoricul afișat, nu certifică inexistența oricărui act nou ori tranzitoriu. Directiva (UE) 2023/2225 prevede aplicarea măsurilor de transpunere de la **20.11.2026**; actul român și eventualele modificări ulterioare nu sunt validate prin această revizie. Pentru dosarele de după această dată trebuie verificate actul român de transpunere și dispozițiile tranzitorii. Directiva singură nu înlocuiește legea națională.
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


## 8. Revizia 6 - modificări aprobate

Au fost aprobate și aplicate cele cinci grupe: acordul ANAF și fereastra din model; formularul de salariu și verificările sale; informarea precontractuală și conținutul contractual; sursele și verificările pentru semnături electronice; corectarea certitudinii despre datorii și actualitatea surselor. Structura originală și documentele anterioare au fost păstrate.

`SURSE_ADAUGATE_6.json` conține URL-urile, data consultării/descărcării și amprentele SHA-256 ale PDF-urilor adăugate. `SURSE_eIDAS.md` indică sursa eIDAS care nu a putut fi descărcată integral. Revizia nu rezolvă limitele de produs contradictorii și nu substituie normele interne Raiffeisen. FATCA/CRS, calendarul AI Act și actul național de transpunere a Directivei 2023/2225 rămân puncte deschise; nu s-au activat reguli neverificate pentru acestea.

## 9. Revizia 7 (28.10.2026)

- Adăugat `OPANAF_146_2022_protocol_inclusiv_Anexa1_acord_ANAF.pdf` (original ANAF). Acordul ANAF din dosare se verifică după anexa 1; formularul Raiffeisen din 2015 devine istoric.
- Adăugat `Codul_fiscal_Legea_227_2015.pdf` (forma consolidată la 25.10.2026) și regula D112 din art. 147 alin. (1).
- Completate: datele minime KYC (Reg. BNR 2/2019 art. 8) și definiția PEP (Legea 129/2019 art. 3); validarea CNP marcată drept control tehnic; Legea 190/2018 trecută ca sursă opțională.
- Reparat tabelul din secțiunea 1 (o linie goală îl rupea în două).

## 10. Revizia 8 (28.10.2026)

- Regulile nu mai trimit la conținutul datelor de test: formulările de tipul „modelul folosit în dosarele de test” au devenit „modelul oficial”, iar nota despre acordurile CRC din datele de test a fost scoasă.
- CEI/CIS: corectate datele de aplicare din HG 231/2025 (de la 14 ani: 20.03.2025; sub 14 ani: 02.06.2025; CIS: 20.05.2025) și adăugată emiterea eșalonată.
- RAG: Codul fiscal întreg a fost mutat în `_text_integral_neindexat`; în rădăcină a rămas doar extrasul cu art. 147. Formularul ANAF Raiffeisen din 2015 a fost mutat în `_arhiva_abrogate`.
- `SURSE_ADAUGATE_6.json`: adăugat extrasul din Codul fiscal; URL-urile care lipsesc sunt marcate „de completat”.
