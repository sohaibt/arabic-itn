# Build plan (v1)

Scope: the PRD's "In v1" list only. Python stdlib, one package `arabic_itn`.

1. Digits and number words: Arabic-Indic / Persian digits to Western digits; Arabic number
   words (MSA + common Gulf/Egyptian/Levantine forms, masc/fem, teens, tens, hundreds,
   thousands, millions) to digits.
2. Phone numbers: digit-by-digit speech, grouped speech, "double"/"triple", plus/00 prefixes,
   Saudi and UAE mobile shapes (+966 / +971 / 05...) to E.164. Other digit-by-digit runs to digits.
3. Money: number + ريال/درهم/جنيه/دولار (+ هللة/فلس/قرش/سنت) to "250 SAR" / "10.50 AED".
4. Times and dates: "الساعة تلاتة ونص العصر" to 15:30 (03:30 without a period word);
   [weekday] day month year to ISO dates (only when the year is given).
5. Spelled emails and order IDs: English letter names (Latin or Arabic script), at/آت,
   dot/نقطة/دوت, gmail/جيميل... to a.b@x.com; letters + digits to AB-1234.
6. API and CLI: `normalize(text, country="SA") -> {"text", "spans": [{"type", "raw", "value"}]}`,
   `arabic-itn` CLI (stdin to JSON), fixture test set of 200+ utterance/expected pairs run by
   `python -m unittest`.
