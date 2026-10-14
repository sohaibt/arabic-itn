# Build report: arabic-itn v1

## Summary

- Built the PRD's whole "In v1" list: a zero-dependency Python library and CLI that turns
  spoken-form Arabic ASR text into exact values (numbers, E.164 phones, money, times, ISO dates,
  emails, order IDs).
- API: `normalize(text, country="SA") -> {"text", "spans": [{"type", "raw", "value"}]}`. CLI: `arabic-itn`.
- Tests: `python -m unittest`: 39 tests, all pass, including 233 utterance/expected fixture pairs.
- Not verified: building or installing the package (the sandbox could not download setuptools).

## What was built

Each task was built test-first and has its own commit (see `docs/plan.md`).

1. **Digits and number words**: Arabic-Indic and Persian digits to Western digits. MSA + Gulf /
   Egyptian / Levantine number words (masc/fem, teens like خمستاشر/خمسطعش, hundreds like
   ميتين/تلتمية/خمس مية, thousands like تلات تلاف/عشرين ألف, millions). Handles "و" joins
   (attached or separate). Lone words under 11, and lone مية/ألف, stay as words.
2. **Phones**: digit-by-digit and grouped speech, دبل/تريبل (double/triple), زائد/plus/00 prefixes.
   Saudi (+966) and UAE (+971) mobiles become E.164. Local 05 numbers use `country`. Other runs of
   3+ spoken digits become digits (OTP codes).
3. **Money**: ريال/درهم/جنيه/دولار to SAR/AED/EGP/USD, with هللة/فلس/قرش/سنت subunits, duals
   (ريالين) and adjectives (سعودي, مصري...). Output: `250 SAR`, `10.50 SAR`.
4. **Times and dates**: الساعة + hour + ونص/وربع/وتلت/إلا/minutes + period word to `HH:MM`
   (24h with a period word, as spoken without one). MSA ordinal hours too. Dates: [weekday]
   day [من] month [سنة] year to ISO, with Gregorian and Levantine months or "شهر N". Only when the
   year is given; invalid dates are left alone.
5. **Emails and order IDs**: Latin words, English letter names in Arabic script, at/آت,
   dot/دوت/نقطة, underscore, dash, Arabic domain words (جيميل, هوتميل, ياهو, كوم) to
   `sara.ali@gmail.com`. Letters + digits to `AB-1234`; trigger words (رقم الطلب, الكود, order...)
   lower the minimum length.
6. **API and CLI**: `normalize()`, the `arabic-itn` CLI (one JSON object per stdin line, `--country`),
   `pyproject.toml` with a console script, and `tests/cases.tsv` (233 pairs).

Also added: README.md, LICENSE (MIT, 2026, Sohaib Thiab), .gitignore, wheredowestand.md, backlog.md.

## Test command and result

```
python -m unittest
...
Ran 39 tests in 0.060s
OK
```

Run with Python 3.14.7. The fixture test checks all 233 pairs (one subTest each) and asserts there
are at least 200.

## Left out (PRD "Not in v1")

Learned contextual scorer / model weights, audio input, HTTP server, Pipecat/LiveKit/Vapi plugins,
address parsing, full dialect coverage, diacritics restoration, hosted benchmark site, paid packs.
All listed in `backlog.md`.

## Known gaps

- **Packaging not verified.** `pip wheel .` failed in the build sandbox because it could not
  download `setuptools>=61` from PyPI. `pyproject.toml` is standard but untested. `python -m arabic_itn`
  and the library work from a clone.
- **Python versions.** `requires-python = ">=3.8"` is not tested. Only Python 3.14 was run.
- **Ambiguity is resolved by rules, not context.** For example, "خمسة مية" is always 500, so a phone
  said as "...خمسة، مية وتلاتة وعشرين" needs the pause/comma to split correctly. Local 05 numbers
  need the caller's `country` (both countries use 05).
- **Times** without "الساعة" are only converted when a period word follows (to avoid "كيلو ونص").
  Without a period word, the hour is kept as spoken (03:30, not 15:30).
- **Coverage** is common forms only: no decimals in words, no English number words, no Egyptian
  (+20) phones, no landlines, no Hijri months, no month-first dates. See `backlog.md`.
- **Test set is hand-written** from typical forms, not from real ASR output. Real transcripts will
  surface misses.
- Nothing in the PRD asked for publishing, public repos, cloud, payment or keys, so no PRD items
  were skipped for hard-rule reasons. The PRD's promotion plan (Product Hunt, Substack) is outside
  a build and was not done.
