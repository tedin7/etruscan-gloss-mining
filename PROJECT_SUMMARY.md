# Progetto: Ricerca Sistematica Glosse Etrusche
**Data inizio:** 2026-01-24
**Obiettivo:** Raccogliere sistematicamente tutte le glosse etrusche citate da autori greci e latini antichi

---

## RISORSE RACCOLTE

### 1. Glossari Completi Scaricati

#### Tripod Glossary (Rick Mc Callister & Silvia Castillo, 1999)
- **File locale:** `glossary_tripod_complete.md`
- **Contenuto:** ~1,500+ parole etrusche con definizioni
- **URL:** https://etruscans1.tripod.com
- **Stato:** ✅ COMPLETATO
- **Glosse identificate con fonti antiche:**
  - `acale/acle` → Latino `aclius, aclus`
  - `acaletur` → Greco `agalé:tora`
  - `acerra` → prestito latino
  - `acila` → Latino `ancilla`
  - `aisar/ais` → "dei" (citato da Svetonio, Cassio Dione)

### 2. Database Accademici Disponibili

#### Mel Copeland - Etruscan Glossary A (2024)
- **Formato:** PDF (estratto in TXT)
- **Contenuto:** 2,800 parole individuali + 6,000+ occorrenze totali
- **File locale:** `data/pdf/Etruscan_Glossary_A_excel_doc_updated_03.pdf`
- **Estratto:** `data/extracted/copeland_glossary.txt` (16,479 righe)
- **Include:** Zagreb Mummy wrapping, Magliano Disk, specchi etruschi
- **Stato:** ✅ SCARICATO E ESTRATTO

#### Mel Copeland - English-Etruscan Dictionary
- **File locale:** `data/pdf/Copeland_English_Etruscan_Dictionary_Vol.pdf`
- **Estratto:** `data/extracted/copeland_dictionary.txt` (10,151 righe)
- **Stato:** ✅ SCARICATO E ESTRATTO

#### Mel Copeland - Introduction to Etruscan Language
- **File locale:** `data/pdf/Introduction_to_the_Etruscan_language_a.pdf`
- **Estratto:** `data/extracted/copeland_introduction.txt` (19,240 righe)
- **Stato:** ✅ SCARICATO E ESTRATTO

#### Gianfranco Forni - Etruscan Basic Lexicon Database
- **Formato:** Excel (.xlsx)
- **File locale:** `data/excel/Etruscan_basic_lexicon_database_March_20.xlsx`
- **Estratto:** `data/extracted/forni_lexicon_raw.txt` (3,523 entries)
- **Stato:** ✅ SCARICATO E ESTRATTO

#### Etruscan Texts Project (ETP) - UMass
- **URL:** https://scholarworks.umass.edu/ces_texts/
- **Contenuto:** Database online con 300+ iscrizioni etrusche (post-1990)
- **Base:** Successore di Helmut Rix, *Etruskische Texte* (1991)
- **Stato:** 🟡 ONLINE (da esplorare per API/export)

### 3. Consensus Accademico Glosse

**Fonte:** Gianfranco Forni - "The Etruscan language and its relationship with the Indo-European language family"

**Glosse con consenso tra etruscologi:**
- 43 glosse per lessico base
- 20 glosse per lessico non-base
- 24 glosse per morfemi legati
- 30 glosse lessico base con significato dubbio
- 14 glosse lessico non-base con significato dubbio

**File locale:** `data/pdf/The_Etruscan_language_and_its_relationsh.pdf`
**Documentazione:** `CONSENSUS_GLOSSES_FORNI.md`
**Stato:** ✅ SCARICATO E DOCUMENTATO

### 4. Autori Antichi Identificati Come Fonti

#### Fonti Primarie:
- **Svetonio** - *Vita Divi Augusti* 97: `aesar/aisar` = "dei"
- **Cassio Dione** - 56.29: conferma episodio fulmine su "Caesar"→"Aesar"
- **Festo** (Sesto Pompeo Festo) - *De verborum significatione*
- **Varrone** - *De Lingua Latina*
- **Isidoro di Siviglia** - *Etymologiae*

#### Fonti Secondarie:
- Dionigi di Alicarnasso
- Plinio il Vecchio
- Cicerone
- Livio
- Seneca
- Macrobio
- Giovanni Lido

### 5. Loanwords Latino-Etruschi Raccolti

**Dal glossario Tripod:**
- `acerra` - "scatola per incenso"
- `familia` - "famiglia"
- `lanista` - "allenatore di gladiatori"
- `histrio/hister` - "attore"
- `ludus` - "giochi pubblici"
- `ludia/ludio` - "attrice/gladiatore"
- `lanterna` - "lampada"
- `lacerna` - "mantello"
- `litterae` - "scrittura"
- `balteus` - "cintura spada"
- `populus` - "popolo"
- `persona` - (non ancora verificato, ma citato nelle fonti iniziali)

---

## RISORSE ONLINE NON ACCESSIBILI

### PDF Bloccati o Non Decodificabili:
1. Helmut Rix - "Etruscan" (Swiss Bay PDF) - binario non leggibile
2. "The Etruscan Loanwords In Latin" (UNC Press) - PDF compresso
3. Edmund Grondine - "Etruscan Dictionary.doc" (Academia) - richiede download

### Siti Non Raggiungibili:
1. http://etruskisch.de/pgs/vc.htm - ECONNREFUSED
2. http://www.pittau.it/Etrusco/etrusco.html - certificato SSL invalido
3. http://www.maravot.com/Etruscan_Vocabulary.html - ECONNREFUSED

---

## PROSSIMI PASSI

### Fase 1: Completare Raccolta Dati Esistenti
1. ✅ Glossario Tripod completo (~1,500 parole)
2. ✅ Scaricare Mel Copeland PDF (2,800 parole) - ESTRATTO
3. ✅ Scaricare Forni Basic Lexicon Database - ESTRATTO
4. ✅ Ottenere paper completo su 43+20+24 glosse consensus - DOCUMENTATO
5. 🔴 Esplorare ETP per export dati

### Fase 2: Estrazione Glosse da Fonti Primarie
1. 🔴 Cercare testo completo Festo (*De verborum significatione*)
2. 🔴 Cercare sezioni rilevanti Varrone (*De Lingua Latina*)
3. 🔴 Compilare lista completa citazioni Svetonio
4. 🔴 Verificare Isidoro *Etymologiae* per sezioni etrusche

### Fase 3: Analisi Automatizzata Perseus
1. 🔴 Verificare API Perseus Digital Library disponibile
2. 🔴 Creare script ricerca pattern:
   - "etrusco/a"
   - "Tusci/Tuscorum"
   - "lingua etrusca"
   - "apud Etruscos"
   - "vocant" + contesto etrusco
3. 🔴 Scansionare corpus latino completo pre-200 d.C.

### Fase 4: Consolidamento Finale
1. 🔴 Unificare tutte le glosse raccolte
2. 🔴 Verificare duplicati e varianti
3. 🔴 Creare database strutturato:
   - Parola etrusca
   - Significato
   - Fonte antica (autore + opera + citazione)
   - Citazione contestuale
   - Affidabilità
4. 🔴 Comparare con iscrizioni per verifica

---

## NOTE METODOLOGICHE

### Definizione "Glossa"
Una glossa etrusca è una parola etrusca il cui significato è esplicitamente spiegato da un autore greco o latino antico.

**Esempio valido:**
> Svetonio, *Vita Divi Augusti* 97: "aesar... etrusca lingua deus"
> (aesar... nella lingua etrusca significa dio)

**Non è una glossa:**
- Etimologie moderne
- Ricostruzioni comparative
- Deduzioni da contesto archeologico

### Criteri Affidabilità
1. **Alta:** Citazione diretta con traduzione esplicita
2. **Media:** Menzione indiretta ma chiara
3. **Bassa:** Etimologia antica speculativa
4. **Incerta:** Tradizione riportata da fonte tardiva (es. Isidoro)

---

## STATISTICHE ATTUALI

- **Parole etrusche catalogate:** ~1,500 (Tripod)
- **Glosse con fonte antica verificata:** ~10
- **Database da integrare:** 2 (Copeland, Forni)
- **Autori antichi identificati:** 12+
- **Loanwords latino-etruschi:** ~15+

---

## FONTI CITATE

### Articoli Accademici:
- [Etruscan language - Wikipedia](https://en.wikipedia.org/wiki/Etruscan_language)
- [Helmut Rix - "Etruscan" chapter](https://theswissbay.ch/pdf/Books/Linguistics/Mega%20linguistics%20pack/Other/Etruscan%20(Rix).pdf)
- [The Etruscan Loanwords In Latin](https://janeway.uncpress.org/capstone/article/2423/galley/2754/download/)

### Database:
- [Etruscan Texts Project (UMass)](https://scholarworks.umass.edu/ces_texts/)
- [Perseus Digital Library](https://www.perseus.tufts.edu/hopper/)
- [Mel Copeland - Etruscan Glossary A](https://www.academia.edu/759774/)
- [Gianfranco Forni - Basic Lexicon Database](https://www.academia.edu/22530267/)

### Glossari:
- [Rick Mc Callister & Silvia Castillo - Etruscan Glossary](https://etruscans1.tripod.com)
- [Wiktionary - Etruscan word list](https://en.wiktionary.org/wiki/Appendix:Etruscan_word_list)

---

**Ultimo aggiornamento:** 2026-01-24 03:00 CET
