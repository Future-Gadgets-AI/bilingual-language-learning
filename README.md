# bll — bilingual subtitle language learning

`bll` turns the subtitles of a show into a graded immersion tool. It takes a
Japanese (L2) subtitle file and its English (L1) counterpart for the same
episode, selects the highest-value Japanese words, and injects each one into the
English subtitle in place of the word it translates. As more episodes are
processed, an SQLite vocabulary database accumulates and the on-screen help for
each word fades — reading annotations disappear once a word is consolidated, so
the subtitles stay just ahead of what the learner already knows.

The result: watch with mostly-English subtitles, but absorb real Japanese
vocabulary in context, at a pace the tool controls.

```
EN:  Did you make a promise with someone?
bll: Did you make a 約束 (yakusoku) with someone?
        ↓  (after enough exposures, the reading drops)
bll: Did you make a 約束 with someone?
```

## How it works

Each `process` run:

1. **Tokenizes** the Japanese subtitles (fugashi + UniDic) and merges compounds.
2. **Selects** new words by general-corpus frequency, gated by a pace limit so
   only a few unconsolidated words are ever on screen at once.
3. **Aligns** each selected word to the exact English substring that expresses it
   in context, using a local language model (via [Ollama](https://ollama.com)).
4. **Vetoes** non-canonical matches against the JMdict dictionary — a swap fires
   only if the model *and* the dictionary agree, and the injected span is trimmed
   to the matching core. This conjunction is what keeps proper-noun and
   free-translation false positives out.
5. **Renders** four subtitle layers plus a plan sidecar, and records each word's
   exposures in the database.

The dictionary and reading data are downloaded automatically on first run.

Alignment runs locally via Ollama by default — no API key, no cost. A
`--backend claude` opt-in aligns through the Claude CLI instead; it spends your
Claude tokens and prints a warning first, so the paid path is never taken
silently.

## Output: four layers per episode

`process` writes four subtitle files (and a `.plan.json` sidecar that can
re-create them later with no model):

| Layer | Reading shown | Use |
| --- | --- | --- |
| **adaptive** | while the word is still being learned, then bare | the main watching layer |
| **plain** | never (bare Japanese) | maximum challenge |
| **kana** | always | every injected word annotated |
| **answers** | always, plus a translator note per new word | full reference |

The reading annotation can be hiragana or romaji (`--romaji`).

## Requirements

- Python ≥ 3.9
- [Ollama](https://ollama.com) running locally, for word alignment
- (optional) Docker, for the packaged deployment in `deploy/`

## Install

```bash
pip install -e .            # or: pip install -e '.[web]' for the web console
```

Provision the alignment model (one-time; pulls a base model and creates a tuned
profile named `bll-align`):

```bash
bll bootstrap
```

## Quick start

```bash
# Inject words from an episode's subtitle pair
bll process episode.ja.srt episode.en.srt -o episode.bll.ass

# Inspect the growing vocabulary and overall progress
bll words
bll stats

# Re-create the four layers from a saved plan (no model needed)
bll render episode.bll.plan.json -o episode.bll.ass
```

Subtitles in `.srt`, `.ass`, `.ssa`, and `.vtt` are supported. The vocabulary
database lives under `~/.local/share/bll/` by default; override it with the
`BLL_DB` environment variable or `--db` to keep separate vocabularies per learner
or per show.

A small synthetic example pair is not bundled; point `bll process` at any
matching Japanese/English subtitle files for the same episode.

## Web console

```bash
bll serve                       # http://127.0.0.1:8000
bll serve --host 0.0.0.0        # expose on the local network
```

The operator console exposes the whole workflow — process episodes, browse the
vocabulary with its learning lifecycle, edit translator notes, manage a branching
episode timeline, and re-render — all from the browser.

## Selected tuning flags

| Flag | Effect |
| --- | --- |
| `--new-words N` | new words introduced per episode |
| `--max-active N` | cap on unconsolidated words on screen at once (pace) |
| `--learning-threshold N` | exposures after which a word counts as learned |
| `--kana-threshold N` | exposures after which the reading annotation drops |
| `--max-per-cue N` | replacements per subtitle line (`0` = unlimited) |
| `--romaji` | annotate with romaji instead of hiragana |
| `--include-pos` | parts of speech eligible for new words (default `noun,adj`) |

Run `bll <command> -h` for the full list.

## Deployment

`deploy/` contains a Dockerfile, a Compose file, and a Modelfile for running the
tool and its aligner together. See the comments in those files for details.
