# Etruscan Gloss Mining - Findings Report
**Generated:** 2026-01-25

---

## Executive Summary

This report summarizes the results of computational mining for Etruscan
glosses in ancient Latin and Greek texts using a multi-phase discovery pipeline.

### Statistics

| Metric | Count |
|--------|-------|
| Verified Glosses (seed data) | 134 |
| Known Vocabulary | 10157 |
| Mining Patterns | 30+ |
| Total Candidates | 2672 |
| Accepted Candidates | 306 |
| Under Review | 78 |

---

## Discovery Pipeline Results (2026-01-25)

### Full Corpus Discovery

Ran unified discovery pipeline across 99 Latin Library texts using 6 discovery methods:

| Method | Description |
|--------|-------------|
| Pattern Mining | Explicit patterns (Tusci vocant) + implicit patterns |
| Cross-Linguistic | Lemnian, Raetic, Latin loanword analysis |
| Phonotactic | Non-Latin phonology detection |
| ML/NER | Foreign word detection, etymology passages |
| Semantic Search | Topic-based relevance (divination, theatre, religion) |
| Author Weighting | Source reliability (Varro=0.95, Isidore=0.40) |

### High-Confidence Discoveries

| Word | Confidence | Evidence |
|------|------------|----------|
| **persona** | 0.98 | Known loan + Raetic śtena parallel |
| **tuscanicum** | 0.94 | Explicit Etruscan attribution |
| **tibicines** | 0.94 | Theatre domain, Etruscan music tradition |
| **haruspex** | 0.89 | Known loan + Lemnian haralio parallel |
| **lanterna** | 0.85 | Raetic śtena parallel |
| **vana** | 0.84 | Lemnian vanala + Raetic śtena |
| **histrio** | 0.81 | Known Etruscan loan (actor) |
| **marathona** | 0.80 | Lemnian maraśm + Raetic parallels |
| **interamna** | 0.79 | Etruscan place name pattern |
| **pristina** | 0.79 | Raetic parallel + -na ending |

### Cross-Linguistic Parallels Found

| Etruscan | Lemnian | Raetic | Notes |
|----------|---------|--------|-------|
| avil (year) | aviś | - | High confidence cognate |
| maru (magistrate) | maraśm | - | Title parallel |
| nefts (grandson) | naphoth | - | Kinship term |
| -al (genitive) | -ale | -ale | Shared morpheme |
| Tinia (Jupiter) | - | tinake | Theonym |
| Velchans (Vulcan) | - | velχanu | Theonym |

### Discovery Statistics

- **Texts processed:** 99 (Latin Library)
- **Unique candidates:** 515
- **High confidence (≥0.70):** 78
- **Medium confidence (0.50-0.69):** 400
- **Discovery methods active:** 6

---

## New Discoveries

### High-Confidence Candidates

| Word | Confidence | Context |
|------|------------|---------|
| **Subulo** | 0.90 | Callimachum in poematibus eius...: quocirca radices eius in Etr |
| **deus** | 0.90 | ra notaret, futurumque ut inte...vocaretur. Tiberium igitur in  |
| **Subulo** | 0.90 | Callimachum in poematibus eius...: quocirca radices eius in Etr |
| **ister** | 0.85 | a voce motus erant. Accepta it...ludio vocabatur, nomen histrio |
| **ludio** | 0.85 | e motus erant. Accepta itaque ...vocabatur, nomen histrionibus  |
| **ita** | 0.75 | distant. Sunt enim in facie pr...capta exuritur, eiusque cinere |
| **ita** | 0.75 | um nutrit, sicque iterum de ci...in excelsis nemoribus texit ni |
| **Lentis** | 0.75 | yptia. [4] Faba fresa dicta eo...humida et lenta est, vel quod  |
| **Lanterna** | 0.75 | quod lambentis motum ostendere...lucem interius habeat clausam. |
| **se** | 0.75 | inorum prodente civitatem fact...fidemque quam implorassent ab  |
| **anno** | 0.75 | adversus Umbros missa a flumin...adversus indutias paratum bell |
| **est** | 0.75 | i. Exceptis enim Latinis hanc ...per C cuncta veteres scripseru |
| **ita** | 0.75 | ricus conposuit. [8] A frequen...ea idem elegantissime [et freq |
| **ita** | 0.75 | distant. Sunt enim in facie pr...capta exuritur, eiusque cinere |
| **ita** | 0.75 | um nutrit, sicque iterum de ci...in excelsis nemoribus texit ni |
| **Lentis** | 0.75 | yptia. [4] Faba fresa dicta eo...humida et lenta est, vel quod  |
| **Lanterna** | 0.75 | quod lambentis motum ostendere...lucem interius habeat clausam. |
| **anno** | 0.75 | aduersus Vmbros missa a flumin...aduersus indutias paratum bell |
| **se** | 0.75 | inorum prodente ciuitatem fact...fidemque quam implorassent ab  |
| **Lentis** | 0.75 | yptia. [4] Faba fresa dicta eo...humida et lenta est, vel quod  |

### Candidates Under Review

The following candidates require expert review:

- **tibicines**: `ita dicunt tibicines Tusci`
- **autem**: `autem vocatur quod`
- **Spes**: `Spes vocata quod`
- **Iscurra**: `Iscurra vocatur quia`
- **Sicarius**: `Sicarius vocatur quia`
- **Hispaniae**: `Hispaniae dicta quod`
- **Cella**: `Cella dicta quod`
- **Arista**: `Arista appellata quod`
- **Alnus**: `Alnus vocatur quod`
- **Arca**: `Arca dicta quod`

---

## Methodology

### Pattern Matching

Latin texts were searched for phrases indicating Etruscan vocabulary:

- `Tusci vocant X` - The Etruscans call X
- `Etrusca lingua X` - In Etruscan language, X
- `Etrusco vocabulo X` - With Etruscan word X
- And 20+ additional patterns

### Validation Pipeline

Each candidate was scored on:

1. **Pattern Confidence** (30%) - Match quality
2. **Cross-Reference** (30%) - Known vocabulary match
3. **Linguistic Plausibility** (20%) - Etruscan phonotactics
4. **Contextual Coherence** (20%) - Meaning indicators

---

## References

- Perseus Digital Library
- Bonfante & Bonfante, *The Etruscan Language*
- Rix, *Etruskische Texte*

---

*Report generated by Etruscan Gloss Miner*