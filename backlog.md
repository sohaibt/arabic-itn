# Backlog (not in v1)

From the PRD's "Not in v1" list:

- A learned contextual scorer or model weights (generate-score-decode, like Premove ITN).
- Audio input.
- HTTP server.
- Pipecat / LiveKit / Vapi plugins.
- Address parsing.
- Full dialect coverage (v1 covers common MSA, Gulf, Egyptian and Levantine forms).
- Diacritics restoration.
- A hosted benchmark site.
- Paid country packs.

Found during the v1 build:

- Decimal numbers said in words ("تلاتة فاصلة خمسة"), and "ونص" after amounts ("مليون ونص",
  "ريال ونص").
- English number words in code-switched speech ("zero five double five").
- Egyptian (+20) and other MENA phone shapes, and Saudi/UAE landlines (only mobiles in v1).
- Construct-state forms such as "مئتا ألف" and "ثلاثمئة ألف" written as two words with "مئتا".
- Month-first dates ("أكتوبر خمسة عشر") and Hijri months.
