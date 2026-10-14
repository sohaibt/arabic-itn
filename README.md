# arabic-itn

Turn spoken-form Arabic ASR transcripts into the exact values a voice agent needs:
phone numbers, money, dates, times, spelled emails and order IDs.

```
الساعة تلاتة ونص العصر                      ->  الساعة 15:30
ميتين وخمسين ريال                           ->  250 SAR
صفر خمسة صفر واحد اتنين تلاتة اربعة ...     ->  +966501234567
اس ايه ار ايه آت جيميل دوت كوم              ->  sara@gmail.com
رقم الطلب ايه بي واحد اتنين تلاتة اربعة     ->  رقم الطلب AB-1234
يوم الخميس خمسة عشر أكتوبر ٢٠٢٦             ->  2026-10-15
```

A small rule-based Python library and CLI. Standard library only, runs locally, works on any
ASR's text output.

## Install

From a clone:

```
pip install .
```

Python 3.8+, no dependencies.

## Usage

```python
from arabic_itn import normalize

normalize("حول ميتين وخمسين ريال على صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة")
# {"text": "حول 250 SAR على +966501234567",
#  "spans": [{"type": "money", "raw": "ميتين وخمسين ريال", "value": "250 SAR"},
#            {"type": "phone", "raw": "صفر خمسة صفر ...", "value": "+966501234567"}]}

normalize("صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة", country="AE")["text"]
# "+971501234567"
```

Span types: `number`, `digits`, `phone`, `money`, `time`, `date`, `email`, `order_id`.
`raw` is the exact input substring; `value` is what replaced it in `text`.

CLI: one transcript per stdin line, one JSON object per stdout line.

```
echo "المبلغ ميتين وخمسين ريال" | arabic-itn
echo "صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة" | arabic-itn --country AE
python -m arabic_itn < transcripts.txt
```

## What it handles

- **Digits**: Arabic-Indic (٠-٩) and Persian (۰-۹) digits to 0-9.
- **Number words**: MSA and common Gulf / Egyptian / Levantine forms, masculine and feminine,
  teens (خمسة عشر, خمستاشر, خمسطعش), hundreds (ميتين, تلتمية, خمس مية), thousands
  (ألف, ألفين, تلات تلاف, عشرين ألف) and millions. Lone small words stay as words
  ("واحد صاحبي", "ألف مبروك", "خمسة ستة أيام").
- **Phones**: digit-by-digit or grouped speech, دبل/double and تريبل/triple, زائد/plus and 00
  prefixes. Saudi and UAE mobiles become E.164. A local `05...` number takes the `country`
  argument (default `SA`), because both countries use 05 prefixes. Other digit runs of 3 or more
  digits (OTP codes) become plain digits.
- **Money**: ريال/درهم/جنيه/دولار to SAR/AED/EGP/USD, with هللة/فلس/قرش/سنت subunits and dual forms
  (ريالين).
- **Times**: "الساعة ..." with ونص/وربع/وتلت/إلا ربع/minutes, MSA ordinals (الثالثة والنصف), and
  period words (الصبح, الظهر, العصر, المسا, بالليل) to 24-hour time. Without a period word the hour
  stays as spoken (03:30). Without "الساعة" a period word is required.
- **Dates**: [weekday] day [من] month [سنة] year to ISO dates. Gregorian and Levantine month names,
  or "شهر عشرة". Only converted when the year is given. Invalid dates are left alone.
- **Emails**: Latin words, English letter names in Arabic script (اس ايه ار ايه), at/آت,
  dot/دوت/نقطة, underscore, dash, and common domains said in Arabic (جيميل, هوتميل, ياهو, كوم).
- **Order IDs**: letters then digits to `AB-1234`. A trigger word just before it (رقم الطلب, الكود,
  رقم الحجز, order, code) lets one letter and one digit count.

## How it is different

- **Arabic, for voice agents.** Premove ITN is English-only. NVIDIA's Arabic ITN grammar is a heavy
  WFST stack under the Riva license. Soniox handles Arabic values only inside its paid STT.
- **MIT, zero dependencies, local.** Drop it after any ASR in any Python pipeline. Nothing leaves the
  process.
- **Built for the values agents act on**: Gulf phone shapes, SAR/AED, order IDs, code-switched
  English letters.
- **Public test set**: `tests/cases.tsv` has 233 utterance/expected pairs. Add yours.

## Tests

```
python -m unittest
```

## Limits

Rule-based, not a learned model. It covers common forms, not every dialect. See `backlog.md` for
what is planned and `BUILD_REPORT.md` for known gaps.

## License

MIT
