#!/usr/bin/env python3
"""Regression tests for heteronym per-injection readings.

Heteronyms share one surface form but have multiple readings depending on
sense (e.g. 角 = つの "horn" vs かど "corner/edge" vs かく "angle"). bll stores
ONE reading per lemma, so it could not flip the reading by context: a heteronym
injected over a given English word always showed the stored reading even when
the matched sense called for a different one. Fix: derive the reading
PER-INJECTION from the JMdict sense the aligned English word maps to
(jmdict.entry_for_en + cli.apply_sense_first), display only -- a strict-winner
rule that no-ops on ties / single-reading words.

Run: python tests/test_heteronym_reading.py   (exits non-zero on any failure)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bll import cli, jmdict

fails = []


def check(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


lk = jmdict.load()


def reading(lemma, en):
    e = jmdict.entry_for_en(lemma, lk.get(lemma), en)
    return e["r"][0] if e else None


# 1. The core case: 角 reads つの over horn (and its plural), but かど/かく for the
#    other senses -- and ties / no-match return None so the caller keeps the
#    stored reading.
check("角/horn", reading("角", "horn"), "つの")
check("角/horns", reading("角", "horns"), "つの")     # plural via lemmatizer
check("角/angle", reading("角", "angle"), "かく")
check("角/edge", reading("角", "edge"), "かど")
check("角/corner", reading("角", "corner"), None)     # かど/すみ tie -> keep fallback
check("方/way", reading("方", "way"), None)           # かた/ほう tie -> keep fallback
check("方/person", reading("方", "person"), "かた")

# 2. The "horn" trap: entry かく has 'Chinese "horn" constellation' (quoted, not
#    parenthesised) so a naive token match would tie. Exact-gloss-match on the
#    つの entry must still win uniquely.
check("角/horn not かく", reading("角", "horn"), "つの")

# 3. apply_sense_first end-to-end: only flips genuine heteronyms whose reading
#    actually changes; everything else is a byte-for-byte no-op.
plan = [
    {"cue": 0, "en_word": "horn", "lemma": "角", "reading": "かど",
     "exposure_before": 0, "recency_gap": 0},
    {"cue": 1, "en_word": "corner", "lemma": "角", "reading": "かど",
     "exposure_before": 0, "recency_gap": 0},
    {"cue": 2, "en_word": "today", "lemma": "今日", "reading": "きょう",
     "exposure_before": 0, "recency_gap": 0},
]
changed = cli.apply_sense_first(plan, lk, conn=None, use_romaji=True)
check("apply_sense_first changed count", changed, 1)
check("horn injection -> つの", plan[0]["reading"], "つの")
check("horn injection note", plan[0].get("note"), "角 (tsuno) = horn; antler")
check("corner injection unchanged", plan[1]["reading"], "かど")
check("corner injection no note override", plan[1].get("note"), None)
check("今日 single-reading untouched", plan[2]["reading"], "きょう")
check("今日 no note override", plan[2].get("note"), None)

if fails:
    print("FAIL:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS: heteronym sense-first reading (角 tsuno/kado) + apply_sense_first")
