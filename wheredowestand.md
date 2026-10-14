# Where we stand

## RESUME HERE

v1 is built and all tests pass (`python -m unittest`: 39 tests, including 233 fixture pairs in
`tests/cases.tsv`). Next: try it on real ASR transcripts (Whisper, Deepgram, Azure Arabic) and
add every miss to `tests/cases.tsv` before changing rules. Then pick from `backlog.md`.

## Layout

- `arabic_itn/__init__.py`: everything. Tokenizer, number parser (`_number`), and one matcher per
  value type. `normalize()` tries matchers in order at each token:
  email, order ID, date, time, money, phone/digits, number.
- `arabic_itn/__main__.py`: the CLI.
- `tests/test_itn.py`: unit tests per feature, CLI tests, and the fixture runner.
- `tests/cases.tsv`: utterance<TAB>expected text.

## Session log

### 2026-10-14: v1 build (automated)

- Built the PRD's "In v1" list test-first, one commit per task: numbers, phones, money,
  times/dates, emails/order IDs, then the CLI and fixture set.
- Choices worth knowing:
  - Local `05...` mobiles are ambiguous between Saudi and UAE, so `normalize(..., country=)` picks
    the code (default SA).
  - Lone number words under 11, and lone مية/ألف, are left as words to avoid "1 صاحبي" or
    "1000 مبروك".
  - Digit runs need 3 or more digits, so "خمسة ستة أيام" (five or six days) is left alone.
  - Letter names that are also Arabic words (في, او, ان, دي, بي...) only count as letters next to
    another letter.
  - Times keep "الساعة" in the text and replace only the time words.
