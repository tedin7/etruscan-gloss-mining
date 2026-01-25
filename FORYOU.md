# The Etruscan Word Detective: How This Project Works

*A plain-language guide to hunting for lost words in ancient texts*

---

## What Are We Actually Building?

Imagine you're a detective, but instead of solving crimes, you're hunting for lost words from a dead language. The Etruscans were an ancient Italian civilization who influenced Rome massively—they gave us gladiatorial games, the toga, and even the word "person" (from the Etruscan *phersu*). But their language? Almost completely lost. We have inscriptions we can mostly read, but we're still missing a lot of vocabulary.

Here's the lucky break: Roman and Greek writers sometimes explained Etruscan words in their texts. They'd write things like:

> "The Etruscans call a flute player *subulo*, which we call *tibicen*."

That's Varro, a Roman scholar, literally telling us an Etruscan word and its meaning. There are dozens of these "glosses" (explanations of foreign words) scattered across ancient literature. Some we know about, but others might be hiding in texts nobody's systematically searched.

**This project is an automated detective that scans ancient texts looking for these word explanations.**

---

## The Big Picture: From Raw Text to Validated Words

Think of the pipeline like a gold mining operation:

```
Ancient Texts (the mine)
        ↓
    Pattern Matching (the sifter)
        ↓
    Raw Candidates (gold flakes mixed with dirt)
        ↓
    Validation Pipeline (the assayer's office)
        ↓
    Verified Glosses (pure gold)
```

Each stage filters out more false positives until we're left with words we can actually trust.

---

## Part 1: The Pattern Library (Our Metal Detector)

### What We're Looking For

Ancient authors had specific ways of introducing foreign words. They'd say things like:

- "Tusci vocant X" — "The Etruscans call [it] X"
- "Etrusca lingua dicitur X" — "In the Etruscan language, X is said"
- "quod Etrusci X appellant" — "which the Etruscans call X"

We've cataloged 45+ of these patterns in `src/etruscan_miner/patterns/latin_patterns.py`. Each pattern is a regex (regular expression) that captures the Etruscan word.

### Confidence Scores

Not all patterns are equally reliable:

| Pattern | Confidence | Why? |
|---------|-----------|------|
| "Tusci vocant X" | 90% | Very explicit—definitely introducing an Etruscan word |
| "ex Etrusco X" | 70% | Could mean "from Etruria" (the place) not "from Etruscan" (the language) |
| "more Tusco" | 65% | "In the Tuscan manner"—might not be about language at all |

The patterns live in a hierarchy, and we can set a minimum confidence threshold to filter out the sketchy ones.

### The Extractor Class

The `GlossExtractor` in `extractor.py` is the workhorse. You give it text, it returns matches:

```python
extractor = GlossExtractor(min_confidence=0.70)
results = extractor.extract("Tusci tibicinem subulo vocant")
# Returns: [PatternMatch(word="subulo", pattern="tusci_vocant", confidence=0.90)]
```

It also captures the surrounding context (100 characters before and after) because context matters for validation.

---

## Part 2: Getting the Texts (Corpus Acquisition)

### The Two Sources

**Perseus Digital Library** — The scholarly standard for digitized classical texts. We use their CTS (Canonical Text Services) API. It's reliable but doesn't have everything we need.

**The Latin Library** — A massive collection of Latin texts. Less structured, but has Varro's *De Lingua Latina* (our most important source) and other texts Perseus doesn't have.

### The Caching Layer

We don't want to hammer these servers every time we run the pipeline. The `text_cache.py` module stores downloaded texts locally for 30 days. Think of it like a local library branch—once you've checked out a book, you don't need to drive downtown again.

### The Bulk Downloader

`scripts/download_all_texts.py` has 100+ hardcoded URLs for high-priority texts. We're not randomly crawling—we know exactly which ancient authors mentioned Etruscan words, so we target them specifically.

---

## Part 3: The Validation Pipeline (Quality Control)

Finding a pattern match is just the beginning. The word "subulo" might actually be Etruscan, or it might be a false positive. The validation pipeline scores candidates on four dimensions:

### Score 1: Pattern Confidence (30%)

How reliable is the pattern that found this word? A "Tusci vocant" match starts with 90% confidence. A "more Tusco" match starts at 65%.

### Score 2: Cross-Reference (30%)

Does this word appear in our database of known Etruscan vocabulary? We have:

- 47+ verified glosses from ancient sources (the stuff scholars already know)
- 43 "consensus" words that academics agree on
- ~1,500 words from comprehensive Etruscan glossaries

If a candidate matches something we already know, that's strong validation. If it's completely unknown, that's not necessarily bad—it might be a discovery!

The matching is smart:
1. Exact match → 100% score
2. Root/stem match → 60-80% (handles variant spellings like "aisar/aesar/ais")
3. Character similarity → up to 60% (catches typos and transliteration differences)

### Score 3: Linguistic Plausibility (20%)

Does this word *sound* Etruscan? The Etruscan language has distinctive features:

**Things that boost the score:**
- Endings like -a, -i, -e, -al, -na (common in Etruscan)
- Clusters like pr-, tr-, cr- (Etruscan loved these)
- Known roots like *ais-* (god), *clan* (son), *tin-* (day)

**Things that tank the score:**
- Voiced stops (b, d, g) — Etruscan didn't have these!
- The letter 'o' — Etruscan used 'u' instead
- Latin morphology like -orum, -ibus, -orum (that's Latin, not Etruscan)

This is encoded in `linguistic.py` as a scoring function that starts at 0.5 and adjusts based on features.

### Score 4: Context Analysis (20%)

Does the surrounding text suggest we're really looking at a word explanation?

Good signs:
- "significat" (means)
- "dicitur" (is called)
- "appellant" (they name)

Bad signs:
- "fortasse" (perhaps) — indicates uncertainty
- "nonnulli" (some people) — indicates disputed information

### The Final Verdict

```
overall_score = pattern × 0.30 + cross_ref × 0.30 + linguistic × 0.20 + context × 0.20
```

Then we bucket:
- **≥ 0.85**: AUTO-ACCEPT — high confidence, add to verified glosses
- **0.65–0.84**: NEEDS REVIEW — human should look at this
- **< 0.65**: REJECT — probably not a real Etruscan word

---

## Part 4: The Database (Our Filing Cabinet)

Everything goes into SQLite at `data/etruscan_glosses.db`. Ten tables track:

- **authors**: Varro, Pliny, Festus, Suetonius, etc.
- **works**: Their books and treatises
- **passages**: Text excerpts we've analyzed
- **candidates**: Words we've found (pending validation)
- **validations**: Individual scores for each validation type
- **verified_glosses**: The gold—confirmed Etruscan words with sources
- **mining_runs**: Audit trail of what we've processed

The `Repository` class in `repository.py` handles all database operations. We never write raw SQL in the scripts—everything goes through the repository.

---

## Part 5: Putting It All Together

### Typical Workflow

```bash
# 1. Set up the database
python scripts/setup_database.py

# 2. Import the known glosses (seed data)
python scripts/import_seeds.py

# 3. Download texts we want to search
python scripts/download_all_texts.py

# 4. Run the mining operation
python scripts/mine_glosses.py --work varro_de_lingua_latina

# 5. Validate what we found
python scripts/validate_candidates.py

# 6. Export the results
python scripts/export_results.py --format markdown -o results/findings.md
```

### What Success Looks Like

If everything works, we'll have:
- Rediscovered all the glosses scholars already know (validation that our patterns work)
- Potentially found new glosses that slipped through previous manual searches
- A confidence score for each candidate so humans know where to focus review time

---

## Lessons Learned & Engineering Wisdom

### Why Pattern Matching Instead of LLM?

You might think: "Why not just ask ChatGPT to find Etruscan words in texts?"

A few reasons:

1. **Precision matters more than recall.** False positives waste scholar time. Regex patterns are predictable and debuggable.

2. **Cost.** We're scanning thousands of pages. LLM inference adds up fast.

3. **Reproducibility.** A regex will find the same things every time. LLMs can be... creative.

4. **Domain expertise.** The patterns encode specific linguistic knowledge (what phrases ancient authors used). This is better captured explicitly than hoped for from a general model.

That said, we've left a slot for "LLM-based validation" as Score 5 if we want to add it later.

### The Cache Is Not Optional

I learned this the hard way: the first version hit the Perseus API constantly and got rate-limited. Now we cache aggressively. The 30-day expiry is a balance—long enough to not re-download, short enough that if Perseus updates texts, we'll eventually get the new versions.

### Normalized Comparison Is Crucial

Etruscan words appear in various forms:
- "aisar" / "aesar" / "ais" (same word, different spellings)
- "AISAR" vs "aisar" (case differences)
- "aïsar" vs "aisar" (diacritics)

The `normalize()` function in the repository strips diacritics, lowercases, and handles common Latin endings that might be attached to Etruscan roots. Without this, we'd miss tons of matches.

### Separate Pattern Confidence from Validation Score

Early versions mixed these together. Bad idea. The pattern confidence tells you "how likely is this phrase introducing a foreign word?" The validation score tells you "how likely is this specific word actually Etruscan?"

A high-confidence pattern can still extract a Latin word if the author was sloppy. A low-confidence pattern might catch a genuine gloss. Keep the scores separate, combine them at the end.

### Test Against Known Glosses First

Before hunting for new words, we verify the system finds the words we already know about. The test fixtures in `tests/fixtures/sample_passages.json` contain passages from Varro, Suetonius, and others where the Etruscan words are documented.

If we can't find "aisar" in Suetonius ("aesar Etrusca lingua deus dicitur"), something's broken. We expect >70% recall on known glosses before trusting the system on new texts.

---

## The Human Element

This pipeline doesn't replace scholars—it's a force multiplier. The output is:

1. **High-confidence matches** that can be added to databases with minimal review
2. **Medium-confidence candidates** that need a classicist to check the context
3. **Rejected candidates** that we can ignore (but keep, in case our rules were wrong)

The best discoveries will probably come from the medium tier—words that look plausible but need a human to read the Latin and confirm "yes, this author is definitely explaining an Etruscan word here."

---

## What's Next?

Things we haven't built yet:

- **Web UI for review**: A nice interface for scholars to accept/reject candidates
- **Active learning**: When a human rejects something, can we learn why?
- **Greek corpus**: We have Greek patterns but haven't fully processed Greek texts
- **LLM validation**: Use a language model to assess context quality

The foundation is solid. The patterns work. The validation pipeline catches most garbage. Now it's about scaling up and getting domain experts to review the output.

---

## Quick Reference

| Want to... | Run this |
|------------|----------|
| Set up fresh database | `python scripts/setup_database.py` |
| Import seed data | `python scripts/import_seeds.py` |
| Test a specific word | `python scripts/validate_candidates.py --word aisar` |
| Mine a text | `python scripts/mine_glosses.py --text "Tusci vocant..."` |
| Run all tests | `python -m pytest tests/ -v` |
| Export results | `python scripts/export_results.py --format markdown -o output.md` |

---

*Happy hunting! May you find words that have been lost for two millennia.*
